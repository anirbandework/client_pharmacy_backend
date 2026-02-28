from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from collections import defaultdict

class DashboardAnalytics:
    """Comprehensive analytics for admin dashboard with chart-ready data"""
    
    @staticmethod
    def get_comprehensive_analytics(
        db: Session,
        organization_id: str,
        shop_id: int = None,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """Get all analytics data for dashboard charts (VERIFIED INVOICES ONLY)"""
        from .models import PurchaseInvoice, PurchaseInvoiceItem
        from modules.auth.models import Shop
        
        # Base query - ONLY VERIFIED INVOICES
        query = db.query(PurchaseInvoice).join(Shop).filter(
            Shop.organization_id == organization_id,
            PurchaseInvoice.is_verified == True
        )
        
        if shop_id:
            query = query.filter(PurchaseInvoice.shop_id == shop_id)
        if start_date:
            query = query.filter(PurchaseInvoice.invoice_date >= start_date)
        if end_date:
            query = query.filter(PurchaseInvoice.invoice_date <= end_date)
        
        invoices = query.all()
        
        return {
            "spending_trends": DashboardAnalytics._get_spending_trends(invoices),
            "supplier_analysis": DashboardAnalytics._get_supplier_analysis(invoices),
            "product_insights": DashboardAnalytics._get_product_insights(invoices),
            "gst_breakdown": DashboardAnalytics._get_gst_breakdown(invoices),
            "expiry_timeline": DashboardAnalytics._get_expiry_timeline(invoices),
            "purchase_patterns": DashboardAnalytics._get_purchase_patterns(invoices),
            "top_categories": DashboardAnalytics._get_top_categories(invoices),
            "payment_analysis": DashboardAnalytics._get_payment_analysis(invoices),
        }
    
    @staticmethod
    def _get_spending_trends(invoices: List) -> Dict[str, Any]:
        """Monthly/weekly spending trends for line chart"""
        monthly = defaultdict(float)
        weekly = defaultdict(float)
        daily = defaultdict(float)
        
        for inv in invoices:
            month_key = inv.invoice_date.strftime("%Y-%m")
            week_key = inv.invoice_date.strftime("%Y-W%U")
            day_key = inv.invoice_date.strftime("%Y-%m-%d")
            
            monthly[month_key] += inv.net_amount
            weekly[week_key] += inv.net_amount
            daily[day_key] += inv.net_amount
        
        return {
            "monthly": [{"period": k, "amount": round(v, 2)} for k, v in sorted(monthly.items())],
            "weekly": [{"period": k, "amount": round(v, 2)} for k, v in sorted(weekly.items())[-12:]],
            "daily": [{"period": k, "amount": round(v, 2)} for k, v in sorted(daily.items())[-30:]],
        }
    
    @staticmethod
    def _get_supplier_analysis(invoices: List) -> Dict[str, Any]:
        """Supplier spend distribution for pie/bar chart"""
        suppliers = defaultdict(lambda: {"spend": 0, "invoices": 0, "items": 0})
        
        for inv in invoices:
            suppliers[inv.supplier_name]["spend"] += inv.net_amount
            suppliers[inv.supplier_name]["invoices"] += 1
            suppliers[inv.supplier_name]["items"] += len(inv.items)
        
        sorted_suppliers = sorted(suppliers.items(), key=lambda x: x[1]["spend"], reverse=True)
        
        return {
            "top_10": [
                {
                    "name": name,
                    "spend": round(data["spend"], 2),
                    "invoices": data["invoices"],
                    "items": data["items"]
                }
                for name, data in sorted_suppliers[:10]
            ],
            "distribution": [
                {"name": name, "value": round(data["spend"], 2)}
                for name, data in sorted_suppliers[:5]
            ]
        }
    
    @staticmethod
    def _get_product_insights(invoices: List) -> Dict[str, Any]:
        """Product purchase analysis"""
        products = defaultdict(lambda: {"quantity": 0, "spend": 0, "frequency": 0})
        
        for inv in invoices:
            for item in inv.items:
                products[item.product_name]["quantity"] += item.quantity
                products[item.product_name]["spend"] += item.total_amount
                products[item.product_name]["frequency"] += 1
        
        sorted_by_spend = sorted(products.items(), key=lambda x: x[1]["spend"], reverse=True)
        sorted_by_qty = sorted(products.items(), key=lambda x: x[1]["quantity"], reverse=True)
        
        return {
            "top_by_spend": [
                {"name": name, "spend": round(data["spend"], 2), "quantity": data["quantity"]}
                for name, data in sorted_by_spend[:10]
            ],
            "top_by_quantity": [
                {"name": name, "quantity": data["quantity"], "spend": round(data["spend"], 2)}
                for name, data in sorted_by_qty[:10]
            ],
            "most_frequent": [
                {"name": name, "frequency": data["frequency"], "spend": round(data["spend"], 2)}
                for name, data in sorted(products.items(), key=lambda x: x[1]["frequency"], reverse=True)[:10]
            ]
        }
    
    @staticmethod
    def _get_gst_breakdown(invoices: List) -> Dict[str, Any]:
        """GST analysis for charts"""
        total_taxable = sum(inv.taxable_amount for inv in invoices)
        total_gst = sum(inv.total_gst for inv in invoices)
        total_net = sum(inv.net_amount for inv in invoices)
        
        gst_by_rate = defaultdict(float)
        for inv in invoices:
            for item in inv.items:
                rate = item.cgst_percent + item.sgst_percent
                gst_by_rate[rate] += item.cgst_amount + item.sgst_amount
        
        return {
            "summary": {
                "taxable_amount": round(total_taxable, 2),
                "total_gst": round(total_gst, 2),
                "net_amount": round(total_net, 2),
                "gst_percentage": round((total_gst / total_net * 100), 2) if total_net > 0 else 0
            },
            "by_rate": [
                {"rate": f"{rate}%", "amount": round(amount, 2)}
                for rate, amount in sorted(gst_by_rate.items())
            ],
            "breakdown": [
                {"category": "Taxable Amount", "value": round(total_taxable, 2)},
                {"category": "GST", "value": round(total_gst, 2)},
            ]
        }
    
    @staticmethod
    def _get_expiry_timeline(invoices: List) -> Dict[str, Any]:
        """Expiry analysis with timeline"""
        today = date.today()
        
        expired = []
        expiring_30 = []
        expiring_60 = []
        expiring_90 = []
        safe = []
        
        for inv in invoices:
            for item in inv.items:
                if not item.expiry_date:
                    continue
                
                days_to_expiry = (item.expiry_date - today).days
                item_data = {
                    "product": item.product_name,
                    "batch": item.batch_number,
                    "days": days_to_expiry,
                    "value": round(item.total_amount, 2),
                    "quantity": item.quantity
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
                {"name": "Safe (>90)", "count": len(safe), "value": sum(i["value"] for i in safe)},
            ],
            "expired_items": sorted(expired, key=lambda x: abs(x["days"]), reverse=True)[:20],
            "critical_items": sorted(expiring_30, key=lambda x: x["days"])[:20]
        }
    
    @staticmethod
    def _get_purchase_patterns(invoices: List) -> Dict[str, Any]:
        """Purchase frequency and patterns"""
        by_day_of_week = defaultdict(lambda: {"count": 0, "amount": 0})
        
        for inv in invoices:
            day_name = inv.invoice_date.strftime("%A")
            by_day_of_week[day_name]["count"] += 1
            by_day_of_week[day_name]["amount"] += inv.net_amount
        
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        return {
            "by_day": [
                {
                    "day": day,
                    "count": by_day_of_week[day]["count"],
                    "amount": round(by_day_of_week[day]["amount"], 2)
                }
                for day in day_order
            ],
            "invoice_size_distribution": DashboardAnalytics._get_invoice_size_dist(invoices)
        }
    
    @staticmethod
    def _get_invoice_size_dist(invoices: List) -> List[Dict]:
        """Invoice size distribution"""
        ranges = [
            (0, 5000, "0-5K"),
            (5000, 10000, "5K-10K"),
            (10000, 25000, "10K-25K"),
            (25000, 50000, "25K-50K"),
            (50000, float('inf'), "50K+")
        ]
        
        distribution = {label: 0 for _, _, label in ranges}
        
        for inv in invoices:
            for min_val, max_val, label in ranges:
                if min_val <= inv.net_amount < max_val:
                    distribution[label] += 1
                    break
        
        return [{"range": k, "count": v} for k, v in distribution.items()]
    
    @staticmethod
    def _get_top_categories(invoices: List) -> Dict[str, Any]:
        """Product categories based on HSN codes"""
        hsn_groups = defaultdict(lambda: {"count": 0, "spend": 0})
        
        for inv in invoices:
            for item in inv.items:
                if item.hsn_code:
                    # Group by first 4 digits of HSN
                    category = item.hsn_code[:4] if len(item.hsn_code) >= 4 else item.hsn_code
                    hsn_groups[category]["count"] += item.quantity
                    hsn_groups[category]["spend"] += item.total_amount
        
        sorted_categories = sorted(hsn_groups.items(), key=lambda x: x[1]["spend"], reverse=True)
        
        return {
            "top_10": [
                {"hsn": hsn, "count": data["count"], "spend": round(data["spend"], 2)}
                for hsn, data in sorted_categories[:10]
            ]
        }
    
    @staticmethod
    def _get_payment_analysis(invoices: List) -> Dict[str, Any]:
        """Payment and discount analysis"""
        total_gross = sum(inv.gross_amount for inv in invoices)
        total_discount = sum(inv.discount_amount for inv in invoices)
        total_net = sum(inv.net_amount for inv in invoices)
        
        return {
            "summary": {
                "gross_amount": round(total_gross, 2),
                "total_discount": round(total_discount, 2),
                "net_amount": round(total_net, 2),
                "avg_discount_percent": round((total_discount / total_gross * 100), 2) if total_gross > 0 else 0
            },
            "discount_distribution": [
                {"category": "Gross Amount", "value": round(total_gross, 2)},
                {"category": "Discount", "value": round(total_discount, 2)},
                {"category": "Net Payable", "value": round(total_net, 2)}
            ]
        }
