"""AI Analytics for Customer Tracking"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from modules.customer_tracking_old.models import *
from datetime import datetime, timedelta, date
from typing import Dict, Any, List
import os
from google import genai
from google.genai import types

class CustomerTrackingAI:
    
    @staticmethod
    def comprehensive_analytics(db: Session, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive AI analytics"""
        
        start_date = datetime.now() - timedelta(days=days)
        
        # 1. Medicine Analytics
        medicine_stats = CustomerTrackingAI._analyze_medicines(db, start_date)
        
        # 2. Customer Behavior
        customer_behavior = CustomerTrackingAI._analyze_customer_behavior(db, start_date)
        
        # 3. Conversion Funnel
        conversion_funnel = CustomerTrackingAI._analyze_conversion_funnel(db, start_date)
        
        # 4. Staff Performance
        staff_performance = CustomerTrackingAI._analyze_staff_performance(db, start_date)
        
        # 5. Revenue Analysis
        revenue_analysis = CustomerTrackingAI._analyze_revenue(db, start_date)
        
        # 6. Customer Analytics (merged from /analytics/customer-analytics)
        customer_analytics = CustomerTrackingAI._get_customer_analytics(db)
        
        # 7. Conversion Report (merged from /analytics/conversion-report)
        conversion_report = CustomerTrackingAI._get_conversion_report(db, start_date)
        
        # 8. AI Insights
        ai_insights = CustomerTrackingAI._generate_ai_insights(
            medicine_stats, customer_behavior, conversion_funnel, staff_performance, revenue_analysis
        )
        
        # 9. Gemini Deep Insights
        gemini_insights = CustomerTrackingAI._generate_gemini_insights(
            medicine_stats, customer_behavior, conversion_funnel, staff_performance, revenue_analysis
        )
        
        return {
            "period": f"Last {days} days",
            "generated_at": datetime.now().isoformat(),
            "medicine_analytics": medicine_stats,
            "customer_behavior": customer_behavior,
            "conversion_funnel": conversion_funnel,
            "staff_performance": staff_performance,
            "revenue_analysis": revenue_analysis,
            "customer_analytics": customer_analytics,
            "conversion_report": conversion_report,
            "ai_insights": ai_insights,
            "gemini_insights": gemini_insights,
            "chart_data": CustomerTrackingAI._generate_chart_data(db, start_date)
        }
    
    @staticmethod
    def _analyze_medicines(db: Session, start_date: datetime) -> Dict[str, Any]:
        """Analyze medicine sales and trends"""
        
        # Top selling medicines
        top_medicines = db.query(
            CustomerPurchase.medicine_name,
            func.count(CustomerPurchase.id).label('sales_count'),
            func.sum(CustomerPurchase.quantity).label('total_quantity'),
            func.sum(CustomerPurchase.total_amount).label('total_revenue'),
            func.avg(CustomerPurchase.unit_price).label('avg_price')
        ).filter(
            CustomerPurchase.purchase_date >= start_date
        ).group_by(
            CustomerPurchase.medicine_name
        ).order_by(
            desc('sales_count')
        ).limit(10).all()
        
        # Generic vs Branded
        generic_count = db.query(CustomerPurchase).filter(
            CustomerPurchase.purchase_date >= start_date,
            CustomerPurchase.is_generic == True
        ).count()
        
        branded_count = db.query(CustomerPurchase).filter(
            CustomerPurchase.purchase_date >= start_date,
            CustomerPurchase.is_generic == False
        ).count()
        
        total_purchases = generic_count + branded_count
        
        # Prescription vs OTC
        prescription_count = db.query(CustomerPurchase).filter(
            CustomerPurchase.purchase_date >= start_date,
            CustomerPurchase.is_prescription == True
        ).count()
        
        otc_count = total_purchases - prescription_count
        
        return {
            "top_selling_medicines": [
                {
                    "medicine_name": med[0],
                    "sales_count": med[1],
                    "total_quantity": med[2],
                    "total_revenue": float(med[3]),
                    "avg_price": float(med[4])
                }
                for med in top_medicines
            ],
            "generic_vs_branded": {
                "generic_count": generic_count,
                "branded_count": branded_count,
                "generic_percentage": round((generic_count / total_purchases * 100) if total_purchases > 0 else 0, 2),
                "branded_percentage": round((branded_count / total_purchases * 100) if total_purchases > 0 else 0, 2)
            },
            "prescription_vs_otc": {
                "prescription_count": prescription_count,
                "otc_count": otc_count,
                "prescription_percentage": round((prescription_count / total_purchases * 100) if total_purchases > 0 else 0, 2)
            }
        }
    
    @staticmethod
    def _analyze_customer_behavior(db: Session, start_date: datetime) -> Dict[str, Any]:
        """Analyze customer behavior patterns"""
        
        total_customers = db.query(CustomerProfile).count()
        new_customers = db.query(CustomerProfile).filter(
            CustomerProfile.first_visit_date >= start_date
        ).count()
        
        # Customer categories
        category_distribution = {}
        for category in CustomerCategory:
            count = db.query(CustomerProfile).filter(
                CustomerProfile.category == category.value
            ).count()
            category_distribution[category.value] = count
        
        # Repeat customer rate
        repeat_customers = db.query(CustomerProfile).filter(
            CustomerProfile.total_visits > 1
        ).count()
        
        # Average purchase value
        avg_purchase = db.query(func.avg(CustomerProfile.total_purchases)).scalar() or 0
        
        # Customer lifetime value (top 10)
        top_customers = db.query(
            CustomerProfile.name,
            CustomerProfile.phone,
            CustomerProfile.total_visits,
            CustomerProfile.total_purchases
        ).order_by(
            desc(CustomerProfile.total_purchases)
        ).limit(10).all()
        
        return {
            "total_customers": total_customers,
            "new_customers_period": new_customers,
            "repeat_customer_rate": round((repeat_customers / total_customers * 100) if total_customers > 0 else 0, 2),
            "category_distribution": category_distribution,
            "avg_purchase_value": round(float(avg_purchase), 2),
            "top_customers": [
                {
                    "name": cust[0],
                    "phone": cust[1],
                    "total_visits": cust[2],
                    "lifetime_value": round(float(cust[3]), 2)
                }
                for cust in top_customers
            ]
        }
    
    @staticmethod
    def _analyze_conversion_funnel(db: Session, start_date: datetime) -> Dict[str, Any]:
        """Analyze conversion funnel from contact to customer"""
        
        total_contacts = db.query(ContactRecord).filter(
            ContactRecord.upload_date >= start_date
        ).count()
        
        contacted = db.query(ContactRecord).filter(
            ContactRecord.upload_date >= start_date,
            ContactRecord.contact_status.in_(['contacted', 'converted', 'yellow'])
        ).count()
        
        converted = db.query(ContactRecord).filter(
            ContactRecord.upload_date >= start_date,
            ContactRecord.contact_status == 'converted'
        ).count()
        
        yellow = db.query(ContactRecord).filter(
            ContactRecord.upload_date >= start_date,
            ContactRecord.contact_status == 'yellow'
        ).count()
        
        return {
            "total_contacts": total_contacts,
            "contacted": contacted,
            "converted": converted,
            "yellow_status": yellow,
            "contact_rate": round((contacted / total_contacts * 100) if total_contacts > 0 else 0, 2),
            "conversion_rate": round((converted / total_contacts * 100) if total_contacts > 0 else 0, 2),
            "yellow_rate": round((yellow / total_contacts * 100) if total_contacts > 0 else 0, 2),
            "funnel_stages": [
                {"stage": "Contacts Uploaded", "count": total_contacts, "percentage": 100},
                {"stage": "Contacted", "count": contacted, "percentage": round((contacted / total_contacts * 100) if total_contacts > 0 else 0, 2)},
                {"stage": "Converted", "count": converted, "percentage": round((converted / total_contacts * 100) if total_contacts > 0 else 0, 2)}
            ]
        }
    
    @staticmethod
    def _analyze_staff_performance(db: Session, start_date: datetime) -> Dict[str, Any]:
        """Analyze staff performance metrics"""
        
        staff_members = db.query(StaffMember).all()
        
        performance = []
        for staff in staff_members:
            contacts_assigned = db.query(ContactRecord).filter(
                ContactRecord.assigned_staff_code == staff.staff_code,
                ContactRecord.assigned_date >= start_date
            ).count()
            
            conversions = db.query(ContactRecord).filter(
                ContactRecord.assigned_staff_code == staff.staff_code,
                ContactRecord.contact_status == 'converted',
                ContactRecord.converted_date >= start_date
            ).count()
            
            interactions = db.query(ContactInteraction).filter(
                ContactInteraction.staff_code == staff.staff_code,
                ContactInteraction.interaction_date >= start_date
            ).count()
            
            performance.append({
                "staff_code": staff.staff_code,
                "name": staff.name,
                "contacts_assigned": contacts_assigned,
                "conversions": conversions,
                "conversion_rate": round((conversions / contacts_assigned * 100) if contacts_assigned > 0 else 0, 2),
                "total_interactions": interactions,
                "avg_interactions_per_contact": round(interactions / contacts_assigned if contacts_assigned > 0 else 0, 2)
            })
        
        return {
            "staff_count": len(staff_members),
            "performance_by_staff": sorted(performance, key=lambda x: x['conversion_rate'], reverse=True)
        }
    
    @staticmethod
    def _analyze_revenue(db: Session, start_date: datetime) -> Dict[str, Any]:
        """Analyze revenue trends"""
        
        total_revenue = db.query(func.sum(CustomerPurchase.total_amount)).filter(
            CustomerPurchase.purchase_date >= start_date
        ).scalar() or 0
        
        total_transactions = db.query(CustomerPurchase).filter(
            CustomerPurchase.purchase_date >= start_date
        ).count()
        
        avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
        
        # Revenue by medicine category
        generic_revenue = db.query(func.sum(CustomerPurchase.total_amount)).filter(
            CustomerPurchase.purchase_date >= start_date,
            CustomerPurchase.is_generic == True
        ).scalar() or 0
        
        branded_revenue = total_revenue - generic_revenue
        
        return {
            "total_revenue": round(float(total_revenue), 2),
            "total_transactions": total_transactions,
            "avg_transaction_value": round(float(avg_transaction), 2),
            "revenue_by_type": {
                "generic": round(float(generic_revenue), 2),
                "branded": round(float(branded_revenue), 2)
            }
        }
    
    @staticmethod
    def _generate_ai_insights(medicine_stats, customer_behavior, conversion_funnel, staff_performance, revenue_analysis) -> List[Dict[str, str]]:
        """Generate AI-powered insights and recommendations"""
        
        insights = []
        
        # Medicine insights
        if medicine_stats['top_selling_medicines']:
            top_med = medicine_stats['top_selling_medicines'][0]
            insights.append({
                "category": "Medicine Trends",
                "insight": f"{top_med['medicine_name']} is your best seller with {top_med['sales_count']} sales",
                "recommendation": f"Ensure adequate stock of {top_med['medicine_name']} to avoid stockouts",
                "priority": "high"
            })
        
        # Generic adoption
        generic_pct = medicine_stats['generic_vs_branded']['generic_percentage']
        if generic_pct < 30:
            insights.append({
                "category": "Generic Adoption",
                "insight": f"Only {generic_pct}% of sales are generic medicines",
                "recommendation": "Train staff to educate customers about generic alternatives to increase margins",
                "priority": "medium"
            })
        elif generic_pct > 60:
            insights.append({
                "category": "Generic Adoption",
                "insight": f"Excellent generic adoption at {generic_pct}%",
                "recommendation": "Continue promoting generic medicines and maintain quality standards",
                "priority": "low"
            })
        
        # Conversion rate
        conv_rate = conversion_funnel['conversion_rate']
        if conv_rate < 20:
            insights.append({
                "category": "Conversion",
                "insight": f"Low conversion rate of {conv_rate}% from contacts",
                "recommendation": "Review contact quality and improve follow-up processes",
                "priority": "high"
            })
        elif conv_rate > 40:
            insights.append({
                "category": "Conversion",
                "insight": f"Strong conversion rate of {conv_rate}%",
                "recommendation": "Document successful practices and train all staff on these methods",
                "priority": "low"
            })
        
        # Repeat customers
        repeat_rate = customer_behavior['repeat_customer_rate']
        if repeat_rate < 40:
            insights.append({
                "category": "Customer Retention",
                "insight": f"Only {repeat_rate}% of customers are repeat buyers",
                "recommendation": "Implement loyalty program and improve refill reminder system",
                "priority": "high"
            })
        
        # Staff performance
        if staff_performance['performance_by_staff']:
            best_staff = staff_performance['performance_by_staff'][0]
            insights.append({
                "category": "Staff Performance",
                "insight": f"{best_staff['name']} has the highest conversion rate at {best_staff['conversion_rate']}%",
                "recommendation": f"Have {best_staff['name']} mentor other staff members on conversion techniques",
                "priority": "medium"
            })
        
        # Revenue insights
        avg_trans = revenue_analysis['avg_transaction_value']
        if avg_trans < 200:
            insights.append({
                "category": "Revenue",
                "insight": f"Average transaction value is low at ₹{avg_trans}",
                "recommendation": "Train staff on upselling and cross-selling complementary products",
                "priority": "medium"
            })
        
        return insights
    
    @staticmethod
    def _generate_chart_data(db: Session, start_date: datetime) -> Dict[str, Any]:
        """Generate data formatted for frontend charts"""
        
        # Daily sales trend
        daily_sales = []
        for i in range(30):
            day = start_date + timedelta(days=i)
            day_end = day + timedelta(days=1)
            
            sales = db.query(func.sum(CustomerPurchase.total_amount)).filter(
                CustomerPurchase.purchase_date >= day,
                CustomerPurchase.purchase_date < day_end
            ).scalar() or 0
            
            daily_sales.append({
                "date": day.strftime("%Y-%m-%d"),
                "sales": round(float(sales), 2)
            })
        
        # Medicine distribution (pie chart)
        top_5_medicines = db.query(
            CustomerPurchase.medicine_name,
            func.sum(CustomerPurchase.total_amount).label('revenue')
        ).filter(
            CustomerPurchase.purchase_date >= start_date
        ).group_by(
            CustomerPurchase.medicine_name
        ).order_by(
            desc('revenue')
        ).limit(5).all()
        
        medicine_distribution = [
            {"name": med[0], "value": round(float(med[1]), 2)}
            for med in top_5_medicines
        ]
        
        # Customer category distribution
        category_data = []
        for category in CustomerCategory:
            count = db.query(CustomerProfile).filter(
                CustomerProfile.category == category.value
            ).count()
            if count > 0:
                category_data.append({
                    "category": category.value.replace('_', ' ').title(),
                    "count": count
                })
        
        return {
            "daily_sales_trend": daily_sales,
            "medicine_distribution": medicine_distribution,
            "customer_categories": category_data
        }

    @staticmethod
    def _generate_gemini_insights(medicine_stats, customer_behavior, conversion_funnel, staff_performance, revenue_analysis) -> Dict[str, Any]:
        """Generate deep insights using Gemini AI"""
        
        try:
            from app.core.config import settings
            
            if not settings.gemini_api_key:
                return {"enabled": False, "message": "Gemini API key not configured"}
            
            client = genai.Client(api_key=settings.gemini_api_key)
            
            data_summary = f"""
Pharmacy Customer Tracking Analytics:

MEDICINES:
- Top Seller: {medicine_stats['top_selling_medicines'][0]['medicine_name'] if medicine_stats['top_selling_medicines'] else 'N/A'}
- Generic: {medicine_stats['generic_vs_branded']['generic_percentage']}%

CUSTOMERS:
- Total: {customer_behavior['total_customers']}
- Repeat Rate: {customer_behavior['repeat_customer_rate']}%
- Avg Purchase: ₹{customer_behavior['avg_purchase_value']}

CONVERSION:
- Rate: {conversion_funnel['conversion_rate']}%

REVENUE:
- Total: ₹{revenue_analysis['total_revenue']}
- Avg Transaction: ₹{revenue_analysis['avg_transaction_value']}
"""
            
            prompt = f"""{data_summary}

Provide 3 strategic insights and 3 actionable recommendations for this pharmacy business."""
            
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            
            return {
                "enabled": True,
                "analysis": response.text,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"enabled": False, "error": str(e)}
    
    @staticmethod
    def _get_customer_analytics(db: Session) -> Dict[str, Any]:
        """Get customer analytics (merged from /analytics/customer-analytics)"""
        
        total_customers = db.query(CustomerProfile).count()
        
        by_category = {}
        for category in CustomerCategory:
            count = db.query(CustomerProfile).filter(
                CustomerProfile.category == category.value
            ).count()
            by_category[category.value] = count
        
        total_contacts = db.query(ContactRecord).count()
        converted_contacts = db.query(ContactRecord).filter(
            ContactRecord.contact_status == ContactStatus.CONVERTED.value
        ).count()
        
        top_medicines = db.query(
            CustomerPurchase.medicine_name,
            func.count(CustomerPurchase.id).label('count'),
            func.sum(CustomerPurchase.total_amount).label('revenue')
        ).group_by(CustomerPurchase.medicine_name).order_by(
            func.count(CustomerPurchase.id).desc()
        ).limit(10).all()
        
        top_medicines_list = [
            {
                'medicine': med[0],
                'sales_count': med[1],
                'revenue': float(med[2]) if med[2] else 0
            }
            for med in top_medicines
        ]
        
        total_purchases = db.query(CustomerPurchase).count()
        generic_purchases = db.query(CustomerPurchase).filter(
            CustomerPurchase.is_generic == True
        ).count()
        
        generic_adoption_rate = (generic_purchases / total_purchases * 100) if total_purchases > 0 else 0
        
        return {
            'total_customers': total_customers,
            'by_category': by_category,
            'conversion_metrics': {
                'total_contacts': total_contacts,
                'converted': converted_contacts,
                'conversion_rate': (converted_contacts / total_contacts * 100) if total_contacts > 0 else 0
            },
            'top_medicines': top_medicines_list,
            'generic_adoption_rate': generic_adoption_rate
        }
    
    @staticmethod
    def _get_conversion_report(db: Session, start_date: datetime) -> Dict[str, Any]:
        """Get conversion report (merged from /analytics/conversion-report)"""
        
        total_contacts = db.query(ContactRecord).filter(
            ContactRecord.upload_date >= start_date
        ).count()
        
        contacted = db.query(ContactRecord).filter(
            ContactRecord.upload_date >= start_date,
            ContactRecord.last_contact_date.isnot(None)
        ).count()
        
        converted = db.query(ContactRecord).filter(
            ContactRecord.upload_date >= start_date,
            ContactRecord.contact_status == ContactStatus.CONVERTED.value
        ).count()
        
        pending = db.query(ContactRecord).filter(
            ContactRecord.upload_date >= start_date,
            ContactRecord.contact_status == ContactStatus.PENDING.value
        ).count()
        
        yellow = db.query(ContactRecord).filter(
            ContactRecord.upload_date >= start_date,
            ContactRecord.contact_status == ContactStatus.YELLOW.value
        ).count()
        
        total_revenue = db.query(func.sum(ContactRecord.conversion_value)).filter(
            ContactRecord.upload_date >= start_date,
            ContactRecord.contact_status == ContactStatus.CONVERTED.value
        ).scalar() or 0
        
        avg_conversion_time = db.query(
            func.avg(
                func.julianday(ContactRecord.converted_date) - func.julianday(ContactRecord.upload_date)
            )
        ).filter(
            ContactRecord.upload_date >= start_date,
            ContactRecord.converted_date.isnot(None)
        ).scalar() or 0
        
        return {
            'total_contacts': total_contacts,
            'contacted': contacted,
            'converted': converted,
            'pending': pending,
            'yellow': yellow,
            'contact_rate': round((contacted / total_contacts * 100) if total_contacts > 0 else 0, 2),
            'conversion_rate': round((converted / total_contacts * 100) if total_contacts > 0 else 0, 2),
            'total_revenue': round(float(total_revenue), 2),
            'avg_conversion_time_days': round(float(avg_conversion_time), 1)
        }
