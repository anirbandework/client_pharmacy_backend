import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-generativeai not installed. AI analytics unavailable.")

class StockAuditAIAnalytics:
    """AI-powered analytics for stock audit data using Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.api_key and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('models/gemini-2.5-flash')
                logger.info("✅ Gemini AI configured for stock analytics")
            except Exception as e:
                logger.error(f"❌ Failed to configure Gemini AI: {e}")
                self.model = None
        else:
            self.model = None
    
    def generate_comprehensive_analysis(
        self, 
        db: Session, 
        organization_id: str,
        shop_id: int = None
    ) -> Dict[str, Any]:
        """Generate comprehensive AI analysis of stock audit data"""
        
        if not self.model:
            return {
                "error": "AI analytics unavailable. Please configure GEMINI_API_KEY."
            }
        
        # Gather data
        data = self._gather_stock_data(db, organization_id, shop_id)
        
        # Generate AI insights
        try:
            prompt = self._build_analysis_prompt(data)
            response = self.model.generate_content(prompt)
            ai_insights = response.text
            
            return {
                "insights": ai_insights,
                "data_summary": data,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {
                "error": f"AI analysis failed: {str(e)}",
                "data_summary": data
            }
    
    def _gather_stock_data(
        self, 
        db: Session, 
        organization_id: str,
        shop_id: int = None
    ) -> Dict[str, Any]:
        """Gather comprehensive stock audit data for analysis"""
        from modules.stock_audit_v2.models import StockItem, StockAuditRecord, StockAdjustment
        from modules.auth.models import Shop
        
        # Base query
        query = db.query(StockItem).join(Shop).filter(
            Shop.organization_id == organization_id
        )
        
        if shop_id:
            query = query.filter(StockItem.shop_id == shop_id)
        
        stock_items = query.all()
        
        # Calculate metrics
        total_items = len(stock_items)
        total_software_qty = sum(item.quantity_software for item in stock_items)
        total_physical_qty = sum(item.quantity_physical for item in stock_items if item.quantity_physical is not None)
        total_value = sum((item.quantity_software * item.unit_price) for item in stock_items if item.unit_price)
        
        # Audit status
        audited_items = [item for item in stock_items if item.last_audit_date is not None]
        audit_rate = (len(audited_items) / total_items * 100) if total_items > 0 else 0
        
        # Discrepancy analysis
        discrepancies = [item for item in stock_items if item.audit_discrepancy != 0]
        positive_disc = [item for item in discrepancies if item.audit_discrepancy > 0]
        negative_disc = [item for item in discrepancies if item.audit_discrepancy < 0]
        
        # Expiry analysis
        today = date.today()
        expired = []
        expiring_30 = []
        expiring_90 = []
        
        for item in stock_items:
            if not item.expiry_date:
                continue
            
            days_to_expiry = (item.expiry_date - today).days
            
            if days_to_expiry < 0:
                expired.append({
                    "product": item.product_name,
                    "batch": item.batch_number,
                    "days_expired": abs(days_to_expiry),
                    "quantity": item.quantity_software,
                    "value": (item.quantity_software * item.unit_price) if item.unit_price else 0
                })
            elif days_to_expiry <= 30:
                expiring_30.append({
                    "product": item.product_name,
                    "batch": item.batch_number,
                    "days_left": days_to_expiry,
                    "quantity": item.quantity_software,
                    "value": (item.quantity_software * item.unit_price) if item.unit_price else 0
                })
            elif days_to_expiry <= 90:
                expiring_90.append({
                    "product": item.product_name,
                    "days_left": days_to_expiry,
                    "quantity": item.quantity_software
                })
        
        # Recent audit activity
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_audits = db.query(StockAuditRecord).join(Shop).filter(
            Shop.organization_id == organization_id,
            StockAuditRecord.audit_date >= thirty_days_ago
        )
        if shop_id:
            recent_audits = recent_audits.filter(StockAuditRecord.shop_id == shop_id)
        
        recent_audits = recent_audits.all()
        
        # Recent adjustments
        recent_adjustments = db.query(StockAdjustment).join(Shop).filter(
            Shop.organization_id == organization_id,
            StockAdjustment.adjustment_date >= thirty_days_ago
        )
        if shop_id:
            recent_adjustments = recent_adjustments.filter(StockAdjustment.shop_id == shop_id)
        
        recent_adjustments = recent_adjustments.all()
        
        return {
            "overview": {
                "total_items": total_items,
                "total_software_quantity": total_software_qty,
                "total_physical_quantity": total_physical_qty,
                "total_stock_value": round(total_value, 2),
                "audit_completion_rate": round(audit_rate, 2),
                "items_audited": len(audited_items),
                "items_not_audited": total_items - len(audited_items)
            },
            "discrepancies": {
                "total_discrepancies": len(discrepancies),
                "positive_discrepancies": len(positive_disc),
                "negative_discrepancies": len(negative_disc),
                "top_discrepancies": [
                    {
                        "product": item.product_name,
                        "batch": item.batch_number,
                        "discrepancy": item.audit_discrepancy,
                        "software_qty": item.quantity_software,
                        "physical_qty": item.quantity_physical,
                        "value_impact": round((item.audit_discrepancy * item.unit_price), 2) if item.unit_price else 0
                    }
                    for item in sorted(discrepancies, key=lambda x: abs(x.audit_discrepancy), reverse=True)[:10]
                ]
            },
            "expiry_status": {
                "expired_items": len(expired),
                "expiring_30_days": len(expiring_30),
                "expiring_90_days": len(expiring_90),
                "expired_details": expired[:10],
                "critical_expiring": expiring_30[:10]
            },
            "recent_activity": {
                "audits_last_30_days": len(recent_audits),
                "adjustments_last_30_days": len(recent_adjustments),
                "avg_audits_per_day": round(len(recent_audits) / 30, 2)
            }
        }
    
    def _build_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Build comprehensive analysis prompt for AI"""
        
        return f"""
You are a pharmaceutical inventory management expert. Analyze this stock audit data and provide actionable insights.

DATA SUMMARY:
{json.dumps(data, indent=2)}

IMPORTANT FORMATTING RULES:
- DO NOT use any emojis anywhere in your response
- Use ## for main section headings
- Use ### for subsections
- Use **bold** for important metrics, numbers, and key terms
- Use bullet points (-) for lists
- Add blank lines between sections for readability
- Highlight critical issues with **CRITICAL:** or **URGENT:**
- Use > for important callouts or warnings

Provide a comprehensive analysis covering:

## 1. STOCK HEALTH OVERVIEW

- **Total Inventory Value:** ₹{data['overview']['total_stock_value']:,.2f}
- **Audit Completion:** {data['overview']['audit_completion_rate']}% ({data['overview']['items_audited']}/{data['overview']['total_items']} items)
- **Stock Accuracy:** Assess overall inventory accuracy
- **Critical Gaps:** Identify urgent issues requiring immediate attention

## 2. AUDIT PERFORMANCE ANALYSIS

- **Completion Rate Assessment:** Evaluate {data['overview']['audit_completion_rate']}% audit rate
- **Unaudited Items Risk:** {data['overview']['items_not_audited']} items not audited - financial exposure
- **Audit Frequency:** Analyze recent audit activity ({data['recent_activity']['audits_last_30_days']} audits in 30 days)
- **Improvement Plan:** Specific steps to achieve 100% audit coverage

## 3. DISCREPANCY ANALYSIS

### Critical Discrepancies
- **Total Discrepancies:** {data['discrepancies']['total_discrepancies']} items
- **Excess Stock:** {data['discrepancies']['positive_discrepancies']} items (potential theft/counting errors)
- **Missing Stock:** {data['discrepancies']['negative_discrepancies']} items (potential loss/damage)

### Root Cause Analysis
- Identify patterns in discrepancies
- Suggest process improvements
- Estimate financial impact

## 4. EXPIRY RISK MANAGEMENT

### URGENT ACTIONS REQUIRED
- **Expired Items:** {data['expiry_status']['expired_items']} items already expired
- **Critical (0-30 days):** {data['expiry_status']['expiring_30_days']} items expiring soon
- **At Risk (31-90 days):** {data['expiry_status']['expiring_90_days']} items need attention

### Prevention Strategy
- **FIFO Implementation:** Specific steps for first-in-first-out
- **Stock Rotation:** Practical rotation schedule
- **Clearance Plan:** Immediate actions for at-risk items
- **Loss Prevention:** Estimated savings from better expiry management

## 5. OPERATIONAL EFFICIENCY

- **Recent Activity:** {data['recent_activity']['audits_last_30_days']} audits, {data['recent_activity']['adjustments_last_30_days']} adjustments in 30 days
- **Audit Velocity:** {data['recent_activity']['avg_audits_per_day']:.2f} audits/day
- **Process Bottlenecks:** Identify slowdowns in audit workflow
- **Staff Performance:** Insights on audit team efficiency

## 6. FINANCIAL IMPACT ASSESSMENT

- **Stock Value at Risk:** Calculate total exposure from discrepancies and expiries
- **Loss Prevention Opportunities:** Quantify potential savings
- **ROI of Better Auditing:** Estimate returns from improved processes
- **Cost of Inaction:** Financial impact if issues not addressed

## 7. STRATEGIC RECOMMENDATIONS

### IMMEDIATE ACTIONS (Next 24-48 Hours)
1. **[Action 1]:** Specific urgent task with expected impact
2. **[Action 2]:** Specific urgent task with expected impact
3. **[Action 3]:** Specific urgent task with expected impact

### SHORT-TERM IMPROVEMENTS (1-2 Weeks)
- List 3-5 tactical improvements
- Include specific metrics to track
- Assign clear ownership

### LONG-TERM STRATEGIES (1-3 Months)
- Process automation opportunities
- Technology investments needed
- Training and development plans
- KPI framework for continuous monitoring

### RISK MITIGATION
- Top 3 risks and mitigation steps
- Contingency plans
- Early warning indicators

### BEST PRACTICES
- Industry benchmarks comparison
- Leading practices to adopt
- Quick wins for immediate improvement

## 8. KEY PERFORMANCE INDICATORS

Suggest 5-7 KPIs to track:
- Audit completion rate target
- Discrepancy rate threshold
- Expiry loss percentage
- Stock accuracy percentage
- Audit cycle time

**Format your response with clear sections, bullet points, bold emphasis on key metrics and amounts, and blank lines between sections for maximum readability. Use specific numbers and percentages from the data.**
"""
