from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import *
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import logging

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    try:
        import google.generativeai as genai
        GENAI_AVAILABLE = True
    except ImportError:
        genai = None
        GENAI_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger(__name__)

class StockAuditAIService:
    
    @staticmethod
    def _init_gemini():
        """Initialize Gemini AI"""
        if not settings.gemini_api_key:
            logger.warning("GEMINI_API_KEY not configured")
            return None
        
        if not GENAI_AVAILABLE:
            logger.warning("google-genai package not available")
            return None
        
        try:
            client = genai.Client(api_key=settings.gemini_api_key)
            logger.info("Gemini AI initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            return None
    
    @staticmethod
    def get_analytics_data(db: Session, shop_id: int, days: int = 30) -> Dict[str, Any]:
        """Gather stock audit analytics data"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Audit records
        audit_records = db.query(StockAuditRecord).filter(
            StockAuditRecord.shop_id == shop_id,
            StockAuditRecord.audit_date >= cutoff_date
        ).all()
        
        # Stock items
        items = db.query(StockItem).filter(StockItem.shop_id == shop_id).all()
        
        # Discrepancy trends
        discrepancy_by_date = {}
        for record in audit_records:
            date_key = record.audit_date.date().isoformat()
            if date_key not in discrepancy_by_date:
                discrepancy_by_date[date_key] = {"total": 0, "count": 0}
            discrepancy_by_date[date_key]["total"] += abs(record.discrepancy)
            discrepancy_by_date[date_key]["count"] += 1
        
        # Section-wise discrepancies
        section_discrepancies = {}
        for item in items:
            if item.section and item.audit_discrepancy != 0:
                section_name = item.section.section_name
                if section_name not in section_discrepancies:
                    section_discrepancies[section_name] = 0
                section_discrepancies[section_name] += abs(item.audit_discrepancy)
        
        # Staff performance
        staff_audits = {}
        for record in audit_records:
            staff = record.staff_name or "Unknown"
            if staff not in staff_audits:
                staff_audits[staff] = {"audits": 0, "discrepancies": 0}
            staff_audits[staff]["audits"] += 1
            staff_audits[staff]["discrepancies"] += abs(record.discrepancy)
        
        return {
            "total_audits": len(audit_records),
            "total_items": len(items),
            "items_with_discrepancies": sum(1 for i in items if i.audit_discrepancy != 0),
            "total_discrepancy_value": sum(abs(i.audit_discrepancy) for i in items),
            "discrepancy_trends": discrepancy_by_date,
            "section_discrepancies": section_discrepancies,
            "staff_performance": staff_audits,
            "audit_completion_rate": sum(1 for i in items if i.last_audit_date) / len(items) * 100 if items else 0
        }
    
    @staticmethod
    def get_chart_data(db: Session, shop_id: int, days: int = 30) -> Dict[str, Any]:
        """Get data formatted for charts"""
        data = StockAuditAIService.get_analytics_data(db, shop_id, days)
        
        # Discrepancy trend chart
        trend_dates = sorted(data["discrepancy_trends"].keys())
        trend_chart = {
            "labels": trend_dates,
            "datasets": [{
                "label": "Average Discrepancy",
                "data": [data["discrepancy_trends"][d]["total"] / data["discrepancy_trends"][d]["count"] 
                        for d in trend_dates]
            }]
        }
        
        # Section discrepancies pie chart
        section_chart = {
            "labels": list(data["section_discrepancies"].keys()),
            "data": list(data["section_discrepancies"].values())
        }
        
        # Staff performance bar chart
        staff_chart = {
            "labels": list(data["staff_performance"].keys()),
            "datasets": [
                {
                    "label": "Audits Completed",
                    "data": [data["staff_performance"][s]["audits"] for s in data["staff_performance"]]
                },
                {
                    "label": "Discrepancies Found",
                    "data": [data["staff_performance"][s]["discrepancies"] for s in data["staff_performance"]]
                }
            ]
        }
        
        return {
            "discrepancy_trend": trend_chart,
            "section_discrepancies": section_chart,
            "staff_performance": staff_chart
        }
    
    @staticmethod
    def get_ai_insights(db: Session, shop_id: int, days: int = 30) -> Dict[str, Any]:
        """Get AI-generated insights using Gemini"""
        data = StockAuditAIService.get_analytics_data(db, shop_id, days)
        
        client = StockAuditAIService._init_gemini()
        
        if not client:
            return StockAuditAIService._get_fallback_insights(data)
        
        prompt = f"""
Analyze this pharmacy stock audit data and provide actionable insights:

Summary:
- Total audits conducted: {data['total_audits']}
- Total items in inventory: {data['total_items']}
- Items with discrepancies: {data['items_with_discrepancies']}
- Total discrepancy value: {data['total_discrepancy_value']} units
- Audit completion rate: {data['audit_completion_rate']:.1f}%

Section-wise discrepancies:
{json.dumps(data['section_discrepancies'], indent=2)}

Staff performance:
{json.dumps(data['staff_performance'], indent=2)}

Provide:
1. Key findings (3-5 bullet points)
2. Risk areas that need attention
3. Actionable recommendations (3-5 specific actions)
4. Predicted issues if trends continue

Format as JSON with keys: findings, risks, recommendations, predictions
"""
        
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )
            insights = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            return insights
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return StockAuditAIService._get_fallback_insights(data)
    
    @staticmethod
    def _get_fallback_insights(data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic insights without AI"""
        findings = []
        risks = []
        recommendations = []
        
        if data['total_audits'] == 0:
            findings.append("No audits conducted in the selected period")
            recommendations.append("Start conducting regular stock audits")
        else:
            findings.append(f"Completed {data['total_audits']} audits covering {data['total_items']} items")
        
        if data['items_with_discrepancies'] > 0:
            discrepancy_rate = (data['items_with_discrepancies'] / data['total_items'] * 100) if data['total_items'] > 0 else 0
            findings.append(f"{discrepancy_rate:.1f}% of items have discrepancies")
            
            if discrepancy_rate > 20:
                risks.append("High discrepancy rate indicates potential inventory management issues")
                recommendations.append("Implement stricter inventory controls and staff training")
        
        if data['audit_completion_rate'] < 100:
            risks.append(f"Only {data['audit_completion_rate']:.1f}% of items have been audited")
            recommendations.append("Complete audits for all inventory items")
        
        if data['section_discrepancies']:
            worst_section = max(data['section_discrepancies'].items(), key=lambda x: x[1])
            risks.append(f"Section '{worst_section[0]}' has highest discrepancies ({worst_section[1]} units)")
            recommendations.append(f"Focus audit efforts on {worst_section[0]} section")
        
        return {
            "findings": findings or ["Insufficient data for analysis"],
            "risks": risks or ["No significant risks identified"],
            "recommendations": recommendations or ["Continue regular audits"],
            "predictions": ["AI predictions unavailable - using statistical analysis"]
        }
    
    @staticmethod
    def get_comprehensive_analysis(db: Session, shop_id: int, days: int = 30) -> Dict[str, Any]:
        """Get complete AI analysis with charts and insights"""
        try:
            analytics = StockAuditAIService.get_analytics_data(db, shop_id, days)
            charts = StockAuditAIService.get_chart_data(db, shop_id, days)
            insights = StockAuditAIService.get_ai_insights(db, shop_id, days)
            
            return {
                "summary": {
                    "total_audits": analytics["total_audits"],
                    "total_items": analytics["total_items"],
                    "items_with_discrepancies": analytics["items_with_discrepancies"],
                    "total_discrepancy_value": analytics["total_discrepancy_value"],
                    "audit_completion_rate": round(analytics["audit_completion_rate"], 2)
                },
                "charts": charts,
                "ai_insights": insights,
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            raise
