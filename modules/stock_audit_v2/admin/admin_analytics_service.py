from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from collections import defaultdict

class StockAuditAnalytics:
    """Comprehensive analytics for stock audit admin dashboard"""
    
    @staticmethod
    def get_comprehensive_analytics(
        db: Session,
        organization_id: str,
        shop_id: int = None
    ) -> Dict[str, Any]:
        """Get all analytics data for stock audit dashboard"""
        from modules.stock_audit_v2.models import StockItem, StockAuditRecord, StockAdjustment, Purchase, Sale
        from modules.auth.models import Shop
        
        # Base query for stock items
        query = db.query(StockItem).join(Shop).filter(
            Shop.organization_id == organization_id
        )
        
        if shop_id:
            query = query.filter(StockItem.shop_id == shop_id)
        
        stock_items = query.all()
        
        return {
            "stock_overview": StockAuditAnalytics._get_stock_overview(stock_items),
            "discrepancy_analysis": StockAuditAnalytics._get_discrepancy_analysis(stock_items),
            "expiry_analysis": StockAuditAnalytics._get_expiry_analysis(stock_items),
            "stock_value_analysis": StockAuditAnalytics._get_stock_value_analysis(stock_items),
            "audit_performance": StockAuditAnalytics._get_audit_performance(db, organization_id, shop_id),
            "stock_movement": StockAuditAnalytics._get_stock_movement(db, organization_id, shop_id),
            "adjustment_analysis": StockAuditAnalytics._get_adjustment_analysis(db, organization_id, shop_id),
        }
    
    @staticmethod
    def _get_stock_overview(stock_items: List) -> Dict[str, Any]:
        """Overall stock statistics"""
        total_items = len(stock_items)
        total_software_qty = sum((item.quantity_software or 0) for item in stock_items)
        total_physical_qty = sum((item.quantity_physical or 0) for item in stock_items if item.quantity_physical is not None)

        items_with_discrepancy = [item for item in stock_items if (item.audit_discrepancy or 0) != 0]
        items_audited = [item for item in stock_items if item.last_audit_date is not None]
        items_not_audited = [item for item in stock_items if item.last_audit_date is None]

        total_value = sum(((item.quantity_software or 0) * item.unit_price) for item in stock_items if item.unit_price)
        
        return {
            "total_items": total_items,
            "total_software_quantity": total_software_qty,
            "total_physical_quantity": total_physical_qty,
            "items_audited": len(items_audited),
            "items_not_audited": len(items_not_audited),
            "items_with_discrepancy": len(items_with_discrepancy),
            "total_stock_value": round(total_value, 2),
            "audit_completion_rate": round((len(items_audited) / total_items * 100), 2) if total_items > 0 else 0
        }
    
    @staticmethod
    def _get_discrepancy_analysis(stock_items: List) -> Dict[str, Any]:
        """Analyze stock discrepancies"""
        discrepancies = []
        
        for item in stock_items:
            disc = item.audit_discrepancy or 0
            if disc != 0:
                discrepancies.append({
                    "product_name": item.product_name,
                    "batch_number": item.batch_number,
                    "software_qty": item.quantity_software or 0,
                    "physical_qty": item.quantity_physical,
                    "discrepancy": disc,
                    "value_impact": round((disc * item.unit_price), 2) if item.unit_price else 0,
                    "last_audit": item.last_audit_date.isoformat() if item.last_audit_date else None
                })
        
        # Categorize discrepancies
        positive_disc = [d for d in discrepancies if d["discrepancy"] > 0]
        negative_disc = [d for d in discrepancies if d["discrepancy"] < 0]
        
        total_value_impact = sum(d["value_impact"] for d in discrepancies)
        
        return {
            "total_discrepancies": len(discrepancies),
            "positive_discrepancies": len(positive_disc),
            "negative_discrepancies": len(negative_disc),
            "total_value_impact": round(total_value_impact, 2),
            "discrepancy_list": sorted(discrepancies, key=lambda x: abs(x["value_impact"]), reverse=True)[:20],
            "discrepancy_distribution": [
                {"category": "Excess Stock", "count": len(positive_disc)},
                {"category": "Missing Stock", "count": len(negative_disc)}
            ]
        }
    
    @staticmethod
    def _get_expiry_analysis(stock_items: List) -> Dict[str, Any]:
        """Analyze expiring stock"""
        today = date.today()
        
        expired = []
        expiring_30 = []
        expiring_60 = []
        expiring_90 = []
        safe = []
        
        for item in stock_items:
            if not item.expiry_date:
                continue
            
            days_to_expiry = (item.expiry_date - today).days
            value = (item.quantity_software * item.unit_price) if item.unit_price else 0
            
            item_data = {
                "product": item.product_name,
                "batch": item.batch_number,
                "quantity": item.quantity_software,
                "days": days_to_expiry,
                "value": round(value, 2)
            }
            
            if days_to_expiry < 0:
                expired.append(item_data)
            elif days_to_expiry <= 30:
                expiring_30.append(item_data)
            elif days_to_expiry <= 60:
                expiring_60.append(item_data)
            elif days_to_expiry <= 90:
                expiring_90.append(item_data)
            else:
                safe.append(item_data)
        
        return {
            "categories": [
                {"name": "Expired", "count": len(expired), "value": sum(i["value"] for i in expired)},
                {"name": "0-30 Days", "count": len(expiring_30), "value": sum(i["value"] for i in expiring_30)},
                {"name": "31-60 Days", "count": len(expiring_60), "value": sum(i["value"] for i in expiring_60)},
                {"name": "61-90 Days", "count": len(expiring_90), "value": sum(i["value"] for i in expiring_90)},
                {"name": "Safe (>90)", "count": len(safe), "value": sum(i["value"] for i in safe)}
            ],
            "expired_items": sorted(expired, key=lambda x: abs(x["days"]), reverse=True)[:10],
            "critical_items": sorted(expiring_30, key=lambda x: x["days"])[:10]
        }
    
    @staticmethod
    def _get_stock_value_analysis(stock_items: List) -> Dict[str, Any]:
        """Analyze stock value distribution"""
        value_ranges = [
            (0, 1000, "0-1K"),
            (1000, 5000, "1K-5K"),
            (5000, 10000, "5K-10K"),
            (10000, 25000, "10K-25K"),
            (25000, float('inf'), "25K+")
        ]
        
        distribution = {label: {"count": 0, "value": 0} for _, _, label in value_ranges}
        
        for item in stock_items:
            if not item.unit_price:
                continue
            
            item_value = (item.quantity_software or 0) * item.unit_price
            
            for min_val, max_val, label in value_ranges:
                if min_val <= item_value < max_val:
                    distribution[label]["count"] += 1
                    distribution[label]["value"] += item_value
                    break
        
        return {
            "distribution": [
                {"range": k, "count": v["count"], "value": round(v["value"], 2)}
                for k, v in distribution.items()
            ]
        }
    
    @staticmethod
    def _get_audit_performance(db: Session, organization_id: str, shop_id: int = None) -> Dict[str, Any]:
        """Analyze audit performance over time"""
        from modules.stock_audit_v2.models import StockAuditRecord
        from modules.auth.models import Shop
        
        query = db.query(StockAuditRecord).join(Shop).filter(
            Shop.organization_id == organization_id
        )
        
        if shop_id:
            query = query.filter(StockAuditRecord.shop_id == shop_id)
        
        # Last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_audits = query.filter(StockAuditRecord.audit_date >= thirty_days_ago).all()
        
        # Group by date
        audits_by_date = defaultdict(lambda: {"count": 0, "discrepancies": 0})
        
        for audit in recent_audits:
            date_key = audit.audit_date.strftime("%Y-%m-%d")
            audits_by_date[date_key]["count"] += 1
            if audit.discrepancy != 0:
                audits_by_date[date_key]["discrepancies"] += 1
        
        return {
            "daily_audits": [
                {"date": k, "audits": v["count"], "discrepancies": v["discrepancies"]}
                for k, v in sorted(audits_by_date.items())
            ],
            "total_audits_30_days": len(recent_audits),
            "avg_audits_per_day": round(len(recent_audits) / 30, 2)
        }
    
    @staticmethod
    def _get_stock_movement(db: Session, organization_id: str, shop_id: int = None) -> Dict[str, Any]:
        """Analyze stock movement (purchases vs sales)"""
        from modules.stock_audit_v2.models import Purchase, Sale
        from modules.auth.models import Shop
        
        # Last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        purchase_query = db.query(Purchase).join(Shop).filter(
            Shop.organization_id == organization_id,
            Purchase.purchase_date >= thirty_days_ago.date()
        )
        
        sale_query = db.query(Sale).join(Shop).filter(
            Shop.organization_id == organization_id,
            Sale.sale_date >= thirty_days_ago.date()
        )
        
        if shop_id:
            purchase_query = purchase_query.filter(Purchase.shop_id == shop_id)
            sale_query = sale_query.filter(Sale.shop_id == shop_id)
        
        purchases = purchase_query.all()
        sales = sale_query.all()
        
        total_purchased = sum(p.total_amount for p in purchases)
        total_sold = sum(s.total_amount for s in sales)
        
        return {
            "purchases_30_days": len(purchases),
            "sales_30_days": len(sales),
            "total_purchase_value": round(total_purchased, 2),
            "total_sale_value": round(total_sold, 2),
            "net_movement": round(total_purchased - total_sold, 2)
        }
    
    @staticmethod
    def _get_adjustment_analysis(db: Session, organization_id: str, shop_id: int = None) -> Dict[str, Any]:
        """Analyze stock adjustments"""
        from modules.stock_audit_v2.models import StockAdjustment
        from modules.auth.models import Shop
        
        query = db.query(StockAdjustment).join(Shop).filter(
            Shop.organization_id == organization_id
        )
        
        if shop_id:
            query = query.filter(StockAdjustment.shop_id == shop_id)
        
        # Last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        adjustments = query.filter(StockAdjustment.adjustment_date >= thirty_days_ago).all()
        
        # Group by type
        by_type = defaultdict(lambda: {"count": 0, "total_qty": 0})
        
        for adj in adjustments:
            by_type[adj.adjustment_type]["count"] += 1
            by_type[adj.adjustment_type]["total_qty"] += adj.quantity_change
        
        return {
            "total_adjustments": len(adjustments),
            "by_type": [
                {"type": k, "count": v["count"], "total_quantity": v["total_qty"]}
                for k, v in by_type.items()
            ]
        }
