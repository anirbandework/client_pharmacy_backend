from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, case, and_, or_
from app.database.database import get_db
from modules.auth.dependencies import get_current_admin
from .models import PurchaseInvoice, PurchaseInvoiceItem
from datetime import date, datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
import statistics

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
    
    # Calculate additional insights
    median_margin = round(statistics.median(margins), 2) if margins else 0
    margin_std_dev = round(statistics.stdev(margins), 2) if len(margins) > 1 else 0
    
    # Low margin products (below 20%)
    low_margin_items = [item for item in items if item.profit_margin and item.profit_margin < 20]
    low_margin_revenue = sum(item.selling_price * item.quantity for item in low_margin_items)
    
    # High margin products (above 40%)
    high_margin_items = [item for item in items if item.profit_margin and item.profit_margin > 40]
    high_margin_revenue = sum(item.selling_price * item.quantity for item in high_margin_items)
    
    # Margin efficiency score (weighted by revenue)
    total_weighted_margin = sum((item.profit_margin or 0) * (item.selling_price * item.quantity) for item in items)
    margin_efficiency = round((total_weighted_margin / total_revenue * 100) if total_revenue > 0 else 0, 2)
    
    return {
        "summary": {
            "avg_margin": round(sum(margins) / len(margins), 2) if margins else 0,
            "median_margin": median_margin,
            "margin_std_dev": margin_std_dev,
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_revenue - total_cost, 2),
            "total_items": len(items),
            "min_margin": round(min(margins), 2) if margins else 0,
            "max_margin": round(max(margins), 2) if margins else 0,
            "low_margin_count": len(low_margin_items),
            "low_margin_revenue": round(low_margin_revenue, 2),
            "high_margin_count": len(high_margin_items),
            "high_margin_revenue": round(high_margin_revenue, 2),
            "margin_efficiency_score": margin_efficiency,
            "roi_percentage": round(((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0, 2)
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

@router.get("/analytics/pricing-optimization")
async def get_pricing_optimization(
    shop_id: Optional[int] = None,
    target_margin: float = 35.0,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get pricing optimization recommendations"""
    query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
        PurchaseInvoice.is_admin_verified == True
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    items = query.all()
    
    recommendations = []
    for item in items:
        if not item.profit_margin or item.profit_margin < target_margin:
            # Calculate optimal selling price for target margin
            optimal_price = item.unit_price * (1 + target_margin / 100)
            
            # Check MRP constraint
            try:
                mrp_value = float(str(item.mrp).split('/')[0]) if item.mrp else None
            except:
                mrp_value = None
            
            if mrp_value and optimal_price > mrp_value:
                # MRP-constrained - calculate max achievable margin
                max_margin = ((mrp_value - item.unit_price) / item.unit_price) * 100
                recommended_price = mrp_value
                achievable_margin = max_margin
                mrp_constrained = True
            else:
                recommended_price = optimal_price
                achievable_margin = target_margin
                mrp_constrained = False
            
            # Calculate potential revenue and profit increase
            current_revenue = item.selling_price * item.quantity
            potential_revenue = recommended_price * item.quantity
            revenue_increase = potential_revenue - current_revenue
            
            current_profit = (item.selling_price - item.unit_price) * item.quantity
            potential_profit = (recommended_price - item.unit_price) * item.quantity
            profit_increase = potential_profit - current_profit
            
            recommendations.append({
                "product_name": item.product_name,
                "composition": item.composition,
                "current_price": round(item.selling_price, 2),
                "current_margin": round(item.profit_margin, 2) if item.profit_margin else 0,
                "recommended_price": round(recommended_price, 2),
                "achievable_margin": round(achievable_margin, 2),
                "mrp": item.mrp,
                "mrp_constrained": mrp_constrained,
                "quantity": item.quantity,
                "revenue_increase": round(revenue_increase, 2),
                "profit_increase": round(profit_increase, 2),
                "priority": "high" if profit_increase > 1000 else "medium" if profit_increase > 500 else "low"
            })
    
    # Sort by profit increase potential
    recommendations.sort(key=lambda x: x["profit_increase"], reverse=True)
    
    total_potential_revenue = sum(r["revenue_increase"] for r in recommendations)
    total_potential_profit = sum(r["profit_increase"] for r in recommendations)
    
    return {
        "recommendations": recommendations[:50],  # Top 50 opportunities
        "summary": {
            "total_opportunities": len(recommendations),
            "total_potential_revenue_increase": round(total_potential_revenue, 2),
            "total_potential_profit_increase": round(total_potential_profit, 2),
            "high_priority_count": sum(1 for r in recommendations if r["priority"] == "high"),
            "mrp_constrained_count": sum(1 for r in recommendations if r["mrp_constrained"])
        }
    }

@router.get("/analytics/margin-trends")
async def get_margin_trends(
    shop_id: Optional[int] = None,
    months: int = 6,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get margin trends over time"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=months * 30)
    
    query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
        PurchaseInvoice.is_admin_verified == True,
        PurchaseInvoice.invoice_date >= start_date
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    items = query.all()
    
    # Group by month
    monthly_data = {}
    for item in items:
        invoice = item.invoice
        month_key = invoice.invoice_date.strftime("%Y-%m")
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {"margins": [], "revenue": 0, "cost": 0, "items": 0}
        
        monthly_data[month_key]["margins"].append(item.profit_margin or 0)
        monthly_data[month_key]["revenue"] += item.selling_price * item.quantity
        monthly_data[month_key]["cost"] += item.unit_price * item.quantity
        monthly_data[month_key]["items"] += 1
    
    trends = [{
        "month": k,
        "avg_margin": round(sum(v["margins"]) / len(v["margins"]), 2) if v["margins"] else 0,
        "total_revenue": round(v["revenue"], 2),
        "total_cost": round(v["cost"], 2),
        "total_profit": round(v["revenue"] - v["cost"], 2),
        "items_count": v["items"]
    } for k, v in sorted(monthly_data.items())]
    
    return {
        "trends": trends,
        "summary": {
            "months_analyzed": len(trends),
            "trend_direction": "improving" if len(trends) >= 2 and trends[-1]["avg_margin"] > trends[0]["avg_margin"] else "declining" if len(trends) >= 2 else "stable"
        }
    }


