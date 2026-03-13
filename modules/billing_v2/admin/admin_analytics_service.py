import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-generativeai not installed. AI analytics unavailable.")

class BillingAdminAnalytics:
    """AI-powered analytics for billing data using Gemini"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.api_key and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('models/gemini-2.5-flash')
                logger.info("✅ Gemini AI configured for billing analytics")
            except Exception as e:
                logger.error(f"❌ Failed to configure Gemini AI: {e}")
                self.model = None
        else:
            self.model = None

    def generate_comprehensive_analysis(
        self,
        db: Session,
        organization_id: str,
        shop_id: int = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Generate comprehensive AI analysis of billing data"""

        if not self.model:
            return {
                "error": "AI analytics unavailable. Please configure GEMINI_API_KEY."
            }

        data = self._gather_billing_data(db, organization_id, shop_id, days)

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

    def _gather_billing_data(
        self,
        db: Session,
        organization_id: str,
        shop_id: int = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Gather comprehensive billing data for analysis"""
        from modules.billing_v2.models import Bill, BillItem
        from modules.billing_v2.daily_records_models import DailyRecord, DailyExpense
        from modules.auth.models import Shop

        cutoff_date = datetime.now() - timedelta(days=days)

        query = db.query(Bill).join(Shop).filter(
            Shop.organization_id == organization_id,
            Bill.created_at >= cutoff_date
        )

        if shop_id:
            query = query.filter(Bill.shop_id == shop_id)

        bills = query.all()

        total_bills = len(bills)
        total_revenue = sum(b.total_amount for b in bills)
        cash_sales = sum(b.cash_amount for b in bills)
        card_sales = sum(b.card_amount for b in bills)
        online_sales = sum(b.online_amount for b in bills)
        total_discount = sum(b.discount_amount for b in bills)
        total_tax = sum(b.tax_amount for b in bills)

        daily_sales = {}
        for bill in bills:
            day = bill.created_at.date()
            if day not in daily_sales:
                daily_sales[day] = {"bills": 0, "revenue": 0, "cash": 0, "card": 0, "online": 0}
            daily_sales[day]["bills"] += 1
            daily_sales[day]["revenue"] += bill.total_amount
            daily_sales[day]["cash"] += bill.cash_amount
            daily_sales[day]["card"] += bill.card_amount
            daily_sales[day]["online"] += bill.online_amount

        hourly_sales = {}
        for bill in bills:
            hour = bill.created_at.hour
            if hour not in hourly_sales:
                hourly_sales[hour] = {"bills": 0, "revenue": 0}
            hourly_sales[hour]["bills"] += 1
            hourly_sales[hour]["revenue"] += bill.total_amount

        top_items = db.query(
            BillItem.item_name,
            func.sum(BillItem.quantity).label('total_qty'),
            func.sum(BillItem.total_price).label('total_revenue'),
            func.count(BillItem.id).label('transaction_count'),
            func.avg(BillItem.unit_price).label('avg_price')
        ).join(Bill).join(Shop).filter(
            Shop.organization_id == organization_id,
            Bill.created_at >= cutoff_date
        )

        if shop_id:
            top_items = top_items.filter(Bill.shop_id == shop_id)

        top_items = top_items.group_by(BillItem.item_name).order_by(
            func.sum(BillItem.total_price).desc()
        ).limit(20).all()

        expense_query = db.query(DailyExpense).join(DailyRecord).join(Shop).filter(
            Shop.organization_id == organization_id,
            DailyExpense.created_at >= cutoff_date
        )

        if shop_id:
            expense_query = expense_query.filter(DailyExpense.shop_id == shop_id)

        expenses = expense_query.all()
        total_expenses = sum(e.amount for e in expenses)

        expense_breakdown = {}
        daily_expenses = {}
        for exp in expenses:
            if exp.expense_category not in expense_breakdown:
                expense_breakdown[exp.expense_category] = 0
            expense_breakdown[exp.expense_category] += exp.amount

            day = exp.created_at.date()
            if day not in daily_expenses:
                daily_expenses[day] = 0
            daily_expenses[day] += exp.amount

        customer_bills = {}
        for bill in bills:
            if bill.customer_phone:
                if bill.customer_phone not in customer_bills:
                    customer_bills[bill.customer_phone] = {"count": 0}
                customer_bills[bill.customer_phone]["count"] += 1

        unique_customers = len(customer_bills)
        repeat_customers = len([p for p, d in customer_bills.items() if d["count"] > 1])

        bill_ranges = {"0-500": 0, "500-1000": 0, "1000-2000": 0, "2000-5000": 0, "5000+": 0}
        for bill in bills:
            amt = bill.total_amount
            if amt < 500:
                bill_ranges["0-500"] += 1
            elif amt < 1000:
                bill_ranges["500-1000"] += 1
            elif amt < 2000:
                bill_ranges["1000-2000"] += 1
            elif amt < 5000:
                bill_ranges["2000-5000"] += 1
            else:
                bill_ranges["5000+"] += 1

        return {
            "period": {
                "days": days,
                "start_date": cutoff_date.date().isoformat(),
                "end_date": date.today().isoformat()
            },
            "overview": {
                "total_bills": total_bills,
                "total_revenue": round(total_revenue, 2),
                "cash_sales": round(cash_sales, 2),
                "card_sales": round(card_sales, 2),
                "online_sales": round(online_sales, 2),
                "total_discount": round(total_discount, 2),
                "total_tax": round(total_tax, 2),
                "avg_bill_value": round(total_revenue / total_bills, 2) if total_bills > 0 else 0,
                "avg_bills_per_day": round(total_bills / days, 2),
                "total_expenses": round(total_expenses, 2),
                "net_profit": round(total_revenue - total_expenses, 2),
                "profit_margin": round(((total_revenue - total_expenses) / total_revenue * 100), 2) if total_revenue > 0 else 0
            },
            "payment_breakdown": [
                {"method": "Cash", "amount": round(cash_sales, 2), "percentage": round(cash_sales/total_revenue*100, 1) if total_revenue > 0 else 0},
                {"method": "Card", "amount": round(card_sales, 2), "percentage": round(card_sales/total_revenue*100, 1) if total_revenue > 0 else 0},
                {"method": "Online", "amount": round(online_sales, 2), "percentage": round(online_sales/total_revenue*100, 1) if total_revenue > 0 else 0}
            ],
            "expenses": {
                "total_expenses": round(total_expenses, 2),
                "net_profit": round(total_revenue - total_expenses, 2),
                "profit_margin": round(((total_revenue - total_expenses) / total_revenue * 100), 2) if total_revenue > 0 else 0,
                "breakdown": [{"category": k, "amount": round(v, 2)} for k, v in expense_breakdown.items()]
            },
            "customers": {
                "unique_customers": unique_customers,
                "repeat_customers": repeat_customers,
                "repeat_rate": round((repeat_customers / unique_customers * 100), 2) if unique_customers > 0 else 0
            },
            "top_selling": [
                {
                    "item": item.item_name,
                    "quantity": item.total_qty,
                    "revenue": round(item.total_revenue, 2),
                    "transactions": item.transaction_count,
                    "avg_price": round(item.avg_price, 2)
                }
                for item in top_items
            ],
            "daily_trends": [
                {
                    "date": str(day),
                    "bills": data["bills"],
                    "revenue": round(data["revenue"], 2),
                    "cash": round(data["cash"], 2),
                    "card": round(data["card"], 2),
                    "online": round(data["online"], 2),
                    "expenses": round(daily_expenses.get(day, 0), 2),
                    "profit": round(data["revenue"] - daily_expenses.get(day, 0), 2)
                }
                for day, data in sorted(daily_sales.items())
            ],
            "hourly_distribution": [
                {"hour": f"{h:02d}:00", "bills": data["bills"], "revenue": round(data["revenue"], 2)}
                for h, data in sorted(hourly_sales.items())
            ],
            "bill_value_distribution": [{"range": k, "count": v} for k, v in bill_ranges.items()]
        }

    def _build_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Build comprehensive analysis prompt for AI"""

        return f"""
You are a pharmaceutical retail business analyst. Analyze this billing data and provide actionable insights.

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

## 1. REVENUE PERFORMANCE

- **Total Revenue:** ₹{data['overview']['total_revenue']:,.2f} ({data['period']['days']} days)
- **Average Daily Revenue:** ₹{data['overview']['total_revenue'] / data['period']['days']:,.2f}
- **Average Bill Value:** ₹{data['overview']['avg_bill_value']:,.2f}
- **Revenue Trends:** Analyze daily patterns and identify peak/low periods
- **Growth Opportunities:** Suggest ways to increase revenue

## 2. SALES ANALYSIS

- **Total Bills:** {data['overview']['total_bills']} ({data['overview']['avg_bills_per_day']:.1f} bills/day)
- **Payment Mix:** Cash: ₹{data['overview']['cash_sales']:,.2f}, Card: ₹{data['overview']['card_sales']:,.2f}, Online: ₹{data['overview']['online_sales']:,.2f}
- **Payment Preferences:** Analyze customer payment behavior
- **Optimization:** Suggest strategies to improve transaction efficiency

## 3. PROFITABILITY ANALYSIS

- **Total Expenses:** ₹{data['expenses']['total_expenses']:,.2f}
- **Net Profit:** ₹{data['expenses']['net_profit']:,.2f}
- **Profit Margin:** {data['expenses']['profit_margin']:.2f}%
- **Expense Breakdown:** Analyze major expense categories
- **Cost Optimization:** Identify areas to reduce costs without impacting quality

## 4. CUSTOMER INSIGHTS

- **Unique Customers:** {data['customers']['unique_customers']}
- **Repeat Customers:** {data['customers']['repeat_customers']} ({data['customers']['repeat_rate']:.1f}% repeat rate)
- **Customer Retention:** Evaluate loyalty and retention strategies
- **Acquisition vs Retention:** Balance between new and existing customers

## 5. PRODUCT PERFORMANCE

- **Top Selling Items:** Analyze the top 10 products
- **Revenue Concentration:** Assess dependency on top products
- **Inventory Planning:** Suggest stocking strategies based on sales patterns
- **Cross-selling Opportunities:** Identify complementary products

## 6. OPERATIONAL EFFICIENCY

- **Bills per Day:** {data['overview']['avg_bills_per_day']:.1f}
- **Staff Productivity:** Insights on billing efficiency
- **Peak Hours:** Identify busy periods for better staffing
- **Process Improvements:** Suggest workflow optimizations

## 7. FINANCIAL HEALTH

- **Cash Flow:** Analyze payment method distribution
- **Discount Impact:** ₹{data['overview']['total_discount']:,.2f} in discounts
- **Tax Collection:** ₹{data['overview']['total_tax']:,.2f}
- **Financial Risks:** Identify potential concerns

## 8. STRATEGIC RECOMMENDATIONS

### IMMEDIATE ACTIONS (Next 7 Days)
1. **[Action 1]:** Specific urgent task with expected impact
2. **[Action 2]:** Specific urgent task with expected impact
3. **[Action 3]:** Specific urgent task with expected impact

### SHORT-TERM IMPROVEMENTS (1-4 Weeks)
- List 3-5 tactical improvements
- Include specific metrics to track
- Assign clear ownership

### LONG-TERM STRATEGIES (1-3 Months)
- Revenue growth initiatives
- Customer retention programs
- Operational excellence
- Technology investments

### KEY PERFORMANCE INDICATORS

Suggest 5-7 KPIs to track:
- Revenue growth rate
- Average bill value
- Customer retention rate
- Profit margin
- Bills per day

**Format your response with clear sections, bullet points, bold emphasis on key metrics and amounts, and blank lines between sections for maximum readability. Use specific numbers and percentages from the data.**
"""
