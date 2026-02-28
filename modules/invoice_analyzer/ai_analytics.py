import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-generativeai not installed. AI analytics unavailable.")

class InvoiceAIAnalytics:
    """AI-powered analytics for invoice data"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.api_key and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                # Use Gemini 2.5 Flash (fastest and most cost-effective)
                self.model = genai.GenerativeModel('models/gemini-2.5-flash')
                logger.info("✅ Gemini AI configured for analytics")
            except Exception as e:
                logger.error(f"❌ Failed to configure Gemini AI: {e}")
                self.model = None
        else:
            self.model = None
    
    def generate_comprehensive_analysis(
        self, 
        db: Session, 
        organization_id: int,
        shop_id: int = None,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """Generate comprehensive AI analysis of invoice data"""
        
        if not self.model:
            return {
                "error": "AI analytics unavailable. Please configure GEMINI_API_KEY.",
                "basic_stats": self._get_basic_stats(db, organization_id, shop_id, start_date, end_date)
            }
        
        # Gather data
        data = self._gather_analytics_data(db, organization_id, shop_id, start_date, end_date)
        
        # Generate AI insights
        try:
            prompt = self._build_analysis_prompt(data)
            response = self.model.generate_content(prompt)
            ai_insights = response.text
            
            return {
                "ai_insights": ai_insights,
                "data_summary": data,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {
                "error": f"AI analysis failed: {str(e)}",
                "data_summary": data,
                "generated_at": datetime.now().isoformat()
            }
    
    def _gather_analytics_data(
        self, 
        db: Session, 
        organization_id: int,
        shop_id: int = None,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """Gather comprehensive invoice data for analysis"""
        from modules.invoice_analyzer.models import PurchaseInvoice, PurchaseInvoiceItem
        from modules.auth.models import Shop
        
        # Base query
        invoice_query = db.query(PurchaseInvoice).join(Shop).filter(
            Shop.organization_id == organization_id
        )
        
        if shop_id:
            invoice_query = invoice_query.filter(PurchaseInvoice.shop_id == shop_id)
        
        if start_date:
            invoice_query = invoice_query.filter(PurchaseInvoice.invoice_date >= start_date)
        
        if end_date:
            invoice_query = invoice_query.filter(PurchaseInvoice.invoice_date <= end_date)
        
        invoices = invoice_query.all()
        
        # Calculate metrics
        total_invoices = len(invoices)
        total_spend = sum(inv.net_amount for inv in invoices)
        total_items = sum(len(inv.items) for inv in invoices)
        
        # Supplier analysis
        supplier_data = {}
        for inv in invoices:
            if inv.supplier_name not in supplier_data:
                supplier_data[inv.supplier_name] = {
                    "total_spend": 0,
                    "invoice_count": 0,
                    "items_purchased": 0
                }
            supplier_data[inv.supplier_name]["total_spend"] += inv.net_amount
            supplier_data[inv.supplier_name]["invoice_count"] += 1
            supplier_data[inv.supplier_name]["items_purchased"] += len(inv.items)
        
        top_suppliers = sorted(
            supplier_data.items(), 
            key=lambda x: x[1]["total_spend"], 
            reverse=True
        )[:10]
        
        # Product analysis
        product_data = {}
        expiring_soon = []
        expired_items = []
        
        for inv in invoices:
            for item in inv.items:
                # Product aggregation
                if item.product_name not in product_data:
                    product_data[item.product_name] = {
                        "total_quantity": 0,
                        "total_spend": 0,
                        "purchase_count": 0,
                        "avg_price": 0
                    }
                product_data[item.product_name]["total_quantity"] += item.quantity
                product_data[item.product_name]["total_spend"] += item.total_amount
                product_data[item.product_name]["purchase_count"] += 1
                product_data[item.product_name]["avg_price"] = (
                    product_data[item.product_name]["total_spend"] / 
                    product_data[item.product_name]["purchase_count"]
                )
                
                # Expiry analysis
                if item.expiry_date:
                    days_to_expiry = (item.expiry_date - date.today()).days
                    
                    if days_to_expiry < 0:
                        expired_items.append({
                            "product": item.product_name,
                            "batch": item.batch_number,
                            "expired_days_ago": abs(days_to_expiry),
                            "quantity": item.quantity,
                            "invoice_date": inv.invoice_date.isoformat()
                        })
                    elif days_to_expiry <= 90:  # Expiring in 3 months
                        expiring_soon.append({
                            "product": item.product_name,
                            "batch": item.batch_number,
                            "days_to_expiry": days_to_expiry,
                            "quantity": item.quantity,
                            "value": item.total_amount
                        })
        
        top_products = sorted(
            product_data.items(),
            key=lambda x: x[1]["total_spend"],
            reverse=True
        )[:10]
        
        # Time-based trends
        monthly_spend = {}
        for inv in invoices:
            month_key = inv.invoice_date.strftime("%Y-%m")
            if month_key not in monthly_spend:
                monthly_spend[month_key] = 0
            monthly_spend[month_key] += inv.net_amount
        
        # GST analysis
        total_gst = sum(inv.total_gst for inv in invoices)
        avg_gst_rate = (total_gst / total_spend * 100) if total_spend > 0 else 0
        
        return {
            "period": {
                "start_date": start_date.isoformat() if start_date else "all_time",
                "end_date": end_date.isoformat() if end_date else "all_time"
            },
            "overview": {
                "total_invoices": total_invoices,
                "total_spend": round(total_spend, 2),
                "total_items": total_items,
                "total_gst_paid": round(total_gst, 2),
                "avg_gst_rate": round(avg_gst_rate, 2),
                "avg_invoice_value": round(total_spend / total_invoices, 2) if total_invoices > 0 else 0
            },
            "suppliers": {
                "total_suppliers": len(supplier_data),
                "top_suppliers": [
                    {"name": name, **data} 
                    for name, data in top_suppliers
                ]
            },
            "products": {
                "unique_products": len(product_data),
                "top_products": [
                    {"name": name, **data}
                    for name, data in top_products
                ]
            },
            "expiry_alerts": {
                "expired_count": len(expired_items),
                "expiring_soon_count": len(expiring_soon),
                "expired_items": expired_items[:20],  # Top 20
                "expiring_soon": sorted(expiring_soon, key=lambda x: x["days_to_expiry"])[:20]
            },
            "trends": {
                "monthly_spend": monthly_spend
            }
        }
    
    def _build_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Build comprehensive analysis prompt for AI"""
        
        return f"""
You are a pharmaceutical business analyst. Analyze this invoice data and provide actionable insights.

DATA SUMMARY:
{json.dumps(data, indent=2)}

IMPORTANT FORMATTING RULES:
- Use ## for main section headings
- Use ### for subsections
- Use **bold** for important metrics, numbers, and key terms
- Use bullet points (-) for lists
- Add blank lines between sections for readability
- Highlight critical issues with **CRITICAL:** or **URGENT:**
- Use > for important callouts or warnings

Provide a comprehensive analysis covering:

## 1. FINANCIAL HEALTH

- **Overall Spending Trends:** Analyze spending patterns over time
- **Budget Efficiency:** Evaluate cost management and wastage
- **Cost Optimization:** Identify specific savings opportunities with estimated amounts
- **GST Analysis:** Review tax burden and input credit optimization

## 2. SUPPLIER INSIGHTS

- **Supplier Concentration Risk:** Assess dependency on single/few suppliers
- **Top Performers:** Identify best suppliers by reliability, pricing, quality
- **Negotiation Opportunities:** Specific areas to negotiate better terms
- **Diversification Strategy:** Concrete steps to reduce supplier risk

## 3. INVENTORY MANAGEMENT

- **High-Value Products:** List top products by spend with amounts
- **Slow-Moving Items:** Identify overstocked products
- **Reorder Optimization:** Suggest optimal quantities based on data
- **Stock Value at Risk:** Calculate financial exposure from poor inventory control

## 4. EXPIRY RISK ANALYSIS

- **Critical Alerts:** List urgent expiry issues with financial impact
- **Prevention Strategies:** Actionable steps to reduce expiry losses
- **FIFO Implementation:** Specific recommendations for stock rotation
- **Clearance Actions:** Immediate steps for at-risk inventory

## 5. PROCUREMENT TRENDS

- **Seasonal Patterns:** Identify buying cycles and seasonal variations
- **Purchase Frequency:** Analyze ordering patterns and efficiency
- **Bulk Opportunities:** Specific products where bulk buying saves money
- **Cost Trends:** Track unit price changes over time

## 6. STRATEGIC RECOMMENDATIONS

### 🎯 Top 3 Immediate Actions
1. **[Action 1]:** Specific task with expected impact
2. **[Action 2]:** Specific task with expected impact
3. **[Action 3]:** Specific task with expected impact

### 📈 Long-Term Strategies
- List 3-5 strategic initiatives for sustained improvement

### ⚠️ Risk Mitigation
- Identify top risks and mitigation steps

### 💡 Growth Opportunities
- Highlight areas for business expansion or optimization

**Format your response with clear sections, bullet points, bold emphasis on key metrics, and blank lines between sections for maximum readability.**
"""
    
    def _get_basic_stats(
        self, 
        db: Session, 
        organization_id: int,
        shop_id: int = None,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """Get basic statistics without AI"""
        data = self._gather_analytics_data(db, organization_id, shop_id, start_date, end_date)
        return data
