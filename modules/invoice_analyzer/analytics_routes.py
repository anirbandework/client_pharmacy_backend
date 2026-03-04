from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, case, and_, or_
from app.database.database import get_db
from modules.auth.dependencies import get_current_admin
from .models import PurchaseInvoice, PurchaseInvoiceItem
from datetime import date
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter()

class MarginSimulationRequest(BaseModel):
    product_names: Optional[List[str]] = None
    compositions: Optional[List[str]] = None
    new_margin: float
    apply_discount: Optional[float] = None

@router.get("/analytics/margin-playground")
async def get_margin_playground(
    shop_id: Optional[int] = None,
    product_name: Optional[str] = None,
    composition: Optional[str] = None,
    manufacturer: Optional[str] = None,
    margin_min: Optional[float] = None,
    margin_max: Optional[float] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Comprehensive margin playground data for admin"""
    query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
        PurchaseInvoice.is_admin_verified == True
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    if product_name:
        query = query.filter(PurchaseInvoiceItem.product_name.ilike(f"%{product_name}%"))
    if composition:
        query = query.filter(PurchaseInvoiceItem.composition.ilike(f"%{composition}%"))
    if manufacturer:
        query = query.filter(PurchaseInvoiceItem.manufacturer.ilike(f"%{manufacturer}%"))
    if margin_min is not None:
        query = query.filter(PurchaseInvoiceItem.profit_margin >= margin_min)
    if margin_max is not None:
        query = query.filter(PurchaseInvoiceItem.profit_margin <= margin_max)
    if date_from:
        query = query.filter(PurchaseInvoice.invoice_date >= date_from)
    if date_to:
        query = query.filter(PurchaseInvoice.invoice_date <= date_to)
    
    items = query.all()
    
    if not items:
        return {
            "summary": {"avg_margin": 0, "total_revenue": 0, "total_cost": 0, "total_profit": 0, "total_items": 0, "min_margin": 0, "max_margin": 0},
            "items": [],
            "margin_distribution": [],
            "composition_breakdown": [],
            "product_breakdown": [],
            "manufacturer_breakdown": []
        }
    
    margins = [item.profit_margin for item in items if item.profit_margin is not None]
    total_cost = sum(item.unit_price * item.quantity for item in items)
    total_revenue = sum(item.selling_price * item.quantity for item in items)
    
    # Margin distribution
    distribution = [
        {"range": "0-10%", "count": sum(1 for m in margins if 0 <= m < 10)},
        {"range": "10-20%", "count": sum(1 for m in margins if 10 <= m < 20)},
        {"range": "20-30%", "count": sum(1 for m in margins if 20 <= m < 30)},
        {"range": "30-40%", "count": sum(1 for m in margins if 30 <= m < 40)},
        {"range": "40-50%", "count": sum(1 for m in margins if 40 <= m < 50)},
        {"range": "50%+", "count": sum(1 for m in margins if m >= 50)}
    ]
    
    # Composition breakdown
    comp_data = {}
    for item in items:
        if item.composition:
            if item.composition not in comp_data:
                comp_data[item.composition] = {"revenue": 0, "cost": 0, "items": 0, "margins": []}
            comp_data[item.composition]["revenue"] += item.selling_price * item.quantity
            comp_data[item.composition]["cost"] += item.unit_price * item.quantity
            comp_data[item.composition]["items"] += 1
            comp_data[item.composition]["margins"].append(item.profit_margin)
    
    composition_breakdown = [{
        "composition": k,
        "revenue": round(v["revenue"], 2),
        "cost": round(v["cost"], 2),
        "profit": round(v["revenue"] - v["cost"], 2),
        "avg_margin": round(sum(v["margins"]) / len(v["margins"]), 2) if v["margins"] else 0,
        "items": v["items"]
    } for k, v in sorted(comp_data.items(), key=lambda x: x[1]["revenue"], reverse=True)[:15]]
    
    # Product breakdown
    prod_data = {}
    for item in items:
        if item.product_name:
            key = f"{item.product_name}|{item.composition or ''}"
            if key not in prod_data:
                prod_data[key] = {"product_name": item.product_name, "composition": item.composition, "revenue": 0, "cost": 0, "margins": [], "qty": 0}
            prod_data[key]["revenue"] += item.selling_price * item.quantity
            prod_data[key]["cost"] += item.unit_price * item.quantity
            prod_data[key]["margins"].append(item.profit_margin)
            prod_data[key]["qty"] += item.quantity
    
    product_breakdown = [{
        "product_name": v["product_name"],
        "composition": v["composition"],
        "revenue": round(v["revenue"], 2),
        "cost": round(v["cost"], 2),
        "profit": round(v["revenue"] - v["cost"], 2),
        "avg_margin": round(sum(v["margins"]) / len(v["margins"]), 2) if v["margins"] else 0,
        "quantity": v["qty"]
    } for v in sorted(prod_data.values(), key=lambda x: x["revenue"], reverse=True)[:20]]
    
    # Manufacturer breakdown
    mfr_data = {}
    for item in items:
        if item.manufacturer:
            if item.manufacturer not in mfr_data:
                mfr_data[item.manufacturer] = {"revenue": 0, "cost": 0, "margins": [], "items": 0}
            mfr_data[item.manufacturer]["revenue"] += item.selling_price * item.quantity
            mfr_data[item.manufacturer]["cost"] += item.unit_price * item.quantity
            mfr_data[item.manufacturer]["margins"].append(item.profit_margin)
            mfr_data[item.manufacturer]["items"] += 1
    
    manufacturer_breakdown = [{
        "manufacturer": k,
        "revenue": round(v["revenue"], 2),
        "cost": round(v["cost"], 2),
        "profit": round(v["revenue"] - v["cost"], 2),
        "avg_margin": round(sum(v["margins"]) / len(v["margins"]), 2) if v["margins"] else 0,
        "items": v["items"]
    } for k, v in sorted(mfr_data.items(), key=lambda x: x[1]["revenue"], reverse=True)[:10]]
    
    # Item details
    item_details = [{
        "id": item.id,
        "product_name": item.product_name,
        "composition": item.composition,
        "manufacturer": item.manufacturer,
        "unit_price": round(item.unit_price, 2),
        "selling_price": round(item.selling_price, 2),
        "mrp": item.mrp,
        "profit_margin": round(item.profit_margin, 2) if item.profit_margin else 0,
        "quantity": item.quantity,
        "total_cost": round(item.unit_price * item.quantity, 2),
        "total_revenue": round(item.selling_price * item.quantity, 2),
        "total_profit": round((item.selling_price - item.unit_price) * item.quantity, 2)
    } for item in items[:100]]  # Limit to 100 items for performance
    
    return {
        "summary": {
            "avg_margin": round(sum(margins) / len(margins), 2) if margins else 0,
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_revenue - total_cost, 2),
            "total_items": len(items),
            "min_margin": round(min(margins), 2) if margins else 0,
            "max_margin": round(max(margins), 2) if margins else 0
        },
        "items": item_details,
        "margin_distribution": distribution,
        "composition_breakdown": composition_breakdown,
        "product_breakdown": product_breakdown,
        "manufacturer_breakdown": manufacturer_breakdown
    }

@router.post("/analytics/simulate-margin-change")
async def simulate_margin_change(
    request: MarginSimulationRequest,
    shop_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Simulate margin changes for products/compositions"""
    query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
        PurchaseInvoice.is_admin_verified == True
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    if request.product_names:
        query = query.filter(PurchaseInvoiceItem.product_name.in_(request.product_names))
    
    if request.compositions:
        query = query.filter(PurchaseInvoiceItem.composition.in_(request.compositions))
    
    items = query.all()
    
    results = []
    for item in items:
        # Calculate new selling price with new margin
        new_selling_price = item.unit_price * (1 + request.new_margin / 100)
        
        # Apply discount if provided
        if request.apply_discount:
            new_selling_price = new_selling_price * (1 - request.apply_discount / 100)
        
        # Check MRP cap
        mrp_value = float(item.mrp) if item.mrp and str(item.mrp).replace('.', '').replace('-', '').isdigit() else None
        capped = False
        
        if mrp_value and new_selling_price > mrp_value:
            new_selling_price = mrp_value
            capped = True
        
        # Calculate actual margin after adjustments
        actual_margin = ((new_selling_price - item.unit_price) / item.unit_price) * 100 if item.unit_price > 0 else 0
        
        # Calculate impact
        old_revenue = item.selling_price * item.quantity
        new_revenue = new_selling_price * item.quantity
        revenue_change = new_revenue - old_revenue
        
        old_profit = (item.selling_price - item.unit_price) * item.quantity
        new_profit = (new_selling_price - item.unit_price) * item.quantity
        profit_change = new_profit - old_profit
        
        results.append({
            "product_name": item.product_name,
            "composition": item.composition,
            "current_selling_price": round(item.selling_price, 2),
            "current_margin": round(item.profit_margin, 2) if item.profit_margin else 0,
            "new_selling_price": round(new_selling_price, 2),
            "new_margin": round(actual_margin, 2),
            "mrp": item.mrp,
            "capped_by_mrp": capped,
            "quantity": item.quantity,
            "revenue_change": round(revenue_change, 2),
            "profit_change": round(profit_change, 2),
            "old_revenue": round(old_revenue, 2),
            "new_revenue": round(new_revenue, 2),
            "old_profit": round(old_profit, 2),
            "new_profit": round(new_profit, 2)
        })
    
    # Summary
    total_revenue_change = sum(r["revenue_change"] for r in results)
    total_profit_change = sum(r["profit_change"] for r in results)
    
    return {
        "items": results,
        "summary": {
            "total_items": len(results),
            "total_revenue_change": round(total_revenue_change, 2),
            "total_profit_change": round(total_profit_change, 2),
            "avg_new_margin": round(sum(r["new_margin"] for r in results) / len(results), 2) if results else 0,
            "items_capped_by_mrp": sum(1 for r in results if r["capped_by_mrp"])
        }
    }


