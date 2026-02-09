try:
    import google.genai as genai
    GENAI_AVAILABLE = True
except ImportError:
    try:
        import google.generativeai as genai
        GENAI_AVAILABLE = True
    except ImportError:
        genai = None
        GENAI_AVAILABLE = False
    
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import logging
import os
from dotenv import load_dotenv
from statistics import mean, stdev

# Load environment variables
load_dotenv()

from .models import PurchaseInvoice, PurchaseInvoiceItem, ItemSale, MonthlyInvoiceSummary
from .schemas import AIInsights, MovementAnalytics

logger = logging.getLogger(__name__)

class PurchaseInvoiceAIAnalytics:
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        logger.info(f"Initializing AI Analytics - API key found: {bool(api_key)}")
        
        if api_key and GENAI_AVAILABLE:
            try:
                self.client = genai.Client(api_key=api_key)
                logger.info("AI Analytics initialized successfully with Gemini Client")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.client = None
        else:
            if not GENAI_AVAILABLE:
                logger.warning("google-genai package not installed. AI analytics will use fallback methods.")
            else:
                logger.warning("GEMINI_API_KEY or GOOGLE_API_KEY not found. AI analytics will be limited.")
            self.client = None
    
    def get_comprehensive_analysis(self, db: Session, shop_id: Optional[int] = None) -> AIInsights:
        """Get comprehensive AI analysis of purchase invoices and movement patterns"""
        
        try:
            movement_data = self._get_movement_data(db, shop_id)
            seasonal_data = self._get_seasonal_data(db, shop_id)
            expiry_data = self._get_expiry_data(db, shop_id)
            profit_data = self._get_profit_data(db, shop_id)
            
            movement_patterns = self._analyze_movement_patterns(movement_data)
            seasonal_trends = self._analyze_seasonal_trends(seasonal_data)
            expiry_predictions = self._analyze_expiry_patterns(expiry_data)
            stock_recommendations = self._generate_stock_recommendations(movement_data, expiry_data)
            profit_optimization = self._analyze_profit_optimization(profit_data)
            
            return AIInsights(
                movement_patterns=movement_patterns,
                seasonal_trends=seasonal_trends,
                expiry_predictions=expiry_predictions,
                stock_recommendations=stock_recommendations,
                profit_optimization=profit_optimization
            )
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {str(e)}")
            return self._get_fallback_insights()
    
    def analyze_item_movement_5_parameters(self, db: Session, item_code: str, shop_id: Optional[int] = None) -> Dict[str, Any]:
        """Analyze item movement using 5 key parameters for AI learning"""
        
        query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
            PurchaseInvoiceItem.item_code == item_code
        )
        
        if shop_id:
            query = query.filter(PurchaseInvoice.shop_id == shop_id)
        
        items = query.all()
        
        if not items:
            return {"error": "Item not found"}
        
        parameters = {
            "product_name": items[0].item_name,
            "product_received": sum(item.purchased_quantity for item in items),
            "batch_analysis": self._analyze_batch_performance(items),
            "date_received_pattern": self._analyze_receipt_patterns(items),
            "date_sold_pattern": self._analyze_sales_patterns(items)
        }
        
        conversion_analysis = self._calculate_conversion_rate(items)
        parameters.update(conversion_analysis)
        
        if self.client:
            prediction = self._generate_movement_prediction(parameters, items)
            parameters["ai_prediction"] = prediction
        
        return parameters
    
    def predict_stock_requirements(self, db: Session, months_ahead: int = 3, shop_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Predict stock requirements for the next few months"""
        
        historical_data = self._get_historical_purchase_data(db, months_ahead * 2, shop_id)
        predictions = []
        
        for item_code, data in historical_data.items():
            try:
                monthly_consumption = data["monthly_consumption"]
                seasonal_factors = data["seasonal_factors"]
                
                future_months = []
                for i in range(1, months_ahead + 1):
                    future_date = date.today() + timedelta(days=30 * i)
                    month = future_date.month
                    
                    base_consumption = mean(monthly_consumption) if monthly_consumption else 0
                    seasonal_factor = seasonal_factors.get(month, 1.0)
                    predicted_consumption = base_consumption * seasonal_factor
                    
                    future_months.append({
                        "month": future_date.strftime("%Y-%m"),
                        "predicted_consumption": predicted_consumption,
                        "recommended_stock": predicted_consumption * 1.2
                    })
                
                predictions.append({
                    "item_code": item_code,
                    "item_name": data["item_name"],
                    "current_stock": data["current_stock"],
                    "average_monthly_consumption": mean(monthly_consumption) if monthly_consumption else 0,
                    "predictions": future_months
                })
                
            except Exception as e:
                logger.error(f"Error predicting for item {item_code}: {str(e)}")
                continue
        
        return predictions
    
    def should_suppress_expiry_alert(self, db: Session, item: PurchaseInvoiceItem) -> bool:
        """AI-powered decision to suppress expiry alerts for fast-moving items"""
        
        if not item.expiry_date or not item.days_to_expiry:
            return False
        
        historical_items = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
            PurchaseInvoiceItem.item_code == item.item_code,
            PurchaseInvoice.received_date < item.invoice.received_date
        ).all()
        
        if not historical_items:
            return False
        
        conversion_rates = []
        for hist_item in historical_items:
            if hist_item.sold_quantity >= hist_item.purchased_quantity * 0.95:
                days_to_sellout = self._calculate_days_to_sellout(hist_item)
                if days_to_sellout:
                    conversion_rates.append(days_to_sellout)
        
        if not conversion_rates:
            return False
        
        avg_sellout_days = mean(conversion_rates)
        
        if avg_sellout_days < item.days_to_expiry * 0.8:
            return True
        
        return False
    
    def _get_movement_data(self, db: Session, shop_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get movement data for analysis"""
        
        six_months_ago = date.today() - timedelta(days=180)
        
        query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
            PurchaseInvoice.received_date >= six_months_ago
        )
        
        if shop_id:
            query = query.filter(PurchaseInvoice.shop_id == shop_id)
        
        items = query.all()
        
        movement_data = []
        for item in items:
            days_in_stock = (date.today() - item.invoice.received_date).days or 1
            
            movement_data.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "purchased_quantity": item.purchased_quantity,
                "sold_quantity": item.sold_quantity,
                "movement_rate": item.movement_rate,
                "days_in_stock": days_in_stock,
                "demand_category": item.demand_category,
                "profit_margin": ((item.selling_price - item.unit_cost) / item.unit_cost) * 100,
                "expiry_days": item.days_to_expiry
            })
        
        return movement_data
    
    def _get_seasonal_data(self, db: Session, shop_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get seasonal sales data"""
        
        one_year_ago = date.today() - timedelta(days=365)
        
        query = db.query(
            extract('month', ItemSale.sale_date).label('month'),
            PurchaseInvoiceItem.item_code,
            func.sum(ItemSale.quantity_sold).label('total_sold')
        ).join(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
            ItemSale.sale_date >= one_year_ago
        )
        
        if shop_id:
            query = query.filter(PurchaseInvoice.shop_id == shop_id)
        
        results = query.group_by(
            extract('month', ItemSale.sale_date),
            PurchaseInvoiceItem.item_code
        ).all()
        
        seasonal_data = []
        for result in results:
            seasonal_data.append({
                "month": result.month,
                "item_code": result.item_code,
                "total_sold": result.total_sold
            })
        
        return seasonal_data
    
    def _get_expiry_data(self, db: Session, shop_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get expiry-related data"""
        
        query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
            PurchaseInvoiceItem.expiry_date.isnot(None)
        )
        
        if shop_id:
            query = query.filter(PurchaseInvoice.shop_id == shop_id)
        
        items = query.all()
        
        expiry_data = []
        for item in items:
            if item.expiry_date:
                expiry_data.append({
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "days_to_expiry": item.days_to_expiry,
                    "remaining_quantity": item.remaining_quantity,
                    "movement_rate": item.movement_rate,
                    "is_expiring_soon": item.is_expiring_soon
                })
        
        return expiry_data
    
    def _get_profit_data(self, db: Session, shop_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get profit analysis data"""
        
        query = db.query(ItemSale).join(PurchaseInvoiceItem).join(PurchaseInvoice)
        
        if shop_id:
            query = query.filter(PurchaseInvoice.shop_id == shop_id)
        
        sales = query.all()
        
        profit_data = []
        for sale in sales:
            profit_data.append({
                "item_code": sale.item.item_code,
                "sale_date": sale.sale_date,
                "quantity_sold": sale.quantity_sold,
                "profit_margin": sale.profit_margin,
                "total_profit": sale.quantity_sold * (sale.sale_price - sale.item.unit_cost)
            })
        
        return profit_data
    
    def _get_historical_purchase_data(self, db: Session, months_back: int, shop_id: Optional[int] = None) -> Dict[str, Any]:
        """Get historical purchase data for predictions"""
        
        start_date = date.today() - timedelta(days=30 * months_back)
        
        query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
            PurchaseInvoice.received_date >= start_date
        )
        
        if shop_id:
            query = query.filter(PurchaseInvoice.shop_id == shop_id)
        
        items = query.all()
        historical_data = {}
        
        for item in items:
            item_code = item.item_code
            
            if item_code not in historical_data:
                historical_data[item_code] = {
                    "item_name": item.item_name,
                    "current_stock": 0,
                    "monthly_consumption": [],
                    "seasonal_factors": {}
                }
            
            days_in_stock = (date.today() - item.invoice.received_date).days or 1
            monthly_consumption = (item.sold_quantity / days_in_stock) * 30 if days_in_stock > 0 else 0
            
            historical_data[item_code]["monthly_consumption"].append(monthly_consumption)
            historical_data[item_code]["current_stock"] += item.remaining_quantity
            
            month = item.invoice.received_date.month
            if month not in historical_data[item_code]["seasonal_factors"]:
                historical_data[item_code]["seasonal_factors"][month] = 1.0
        
        return historical_data
    
    def _analyze_movement_patterns(self, movement_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze movement patterns using AI"""
        
        if not self.client or not movement_data:
            return self._get_basic_movement_analysis(movement_data)
        
        try:
            analysis_prompt = f"""
            Analyze pharmacy inventory movement data and provide insights in JSON format:
            {json.dumps(movement_data[:10], default=str)}
            
            Return: {{"patterns": [{{"pattern_type": "fast_moving", "items": ["codes"], "description": "text", "recommendation": "text"}}]}}
            """
            
            response = self.client.models.generate_content(
                model='gemini-1.5-pro',
                contents=analysis_prompt
            )
            
            try:
                ai_analysis = json.loads(response.text)
                return ai_analysis.get("patterns", [])
            except json.JSONDecodeError:
                return self._get_basic_movement_analysis(movement_data)
                
        except Exception as e:
            logger.error(f"Error in AI movement analysis: {str(e)}")
            return self._get_basic_movement_analysis(movement_data)
    
    def _get_basic_movement_analysis(self, movement_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Basic movement analysis without AI"""
        
        if not movement_data:
            return []
        
        fast_moving = [item for item in movement_data if item["movement_rate"] >= 5]
        slow_moving = [item for item in movement_data if item["movement_rate"] < 1]
        
        patterns = []
        
        if fast_moving:
            patterns.append({
                "pattern_type": "fast_moving",
                "items": [item["item_code"] for item in fast_moving[:10]],
                "description": f"Found {len(fast_moving)} fast-moving items",
                "recommendation": "Ensure adequate stock levels"
            })
        
        if slow_moving:
            patterns.append({
                "pattern_type": "slow_moving",
                "items": [item["item_code"] for item in slow_moving[:10]],
                "description": f"Found {len(slow_moving)} slow-moving items",
                "recommendation": "Consider promotional strategies"
            })
        
        return patterns
    
    def _analyze_seasonal_trends(self, seasonal_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return []
    
    def _analyze_expiry_patterns(self, expiry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return []
    
    def _generate_stock_recommendations(self, movement_data: List[Dict[str, Any]], expiry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return []
    
    def _analyze_profit_optimization(self, profit_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return []
    
    def _get_fallback_insights(self) -> AIInsights:
        return AIInsights(
            movement_patterns=[],
            seasonal_trends=[],
            expiry_predictions=[],
            stock_recommendations=[],
            profit_optimization=[]
        )
    
    def _calculate_days_to_sellout(self, item: PurchaseInvoiceItem) -> Optional[int]:
        if not item.sales:
            return None
        
        cumulative_sold = 0
        sellout_threshold = item.purchased_quantity * 0.95
        
        for sale in sorted(item.sales, key=lambda s: s.sale_date):
            cumulative_sold += sale.quantity_sold
            if cumulative_sold >= sellout_threshold:
                return (sale.sale_date - item.invoice.received_date).days
        
        return None
    
    def _analyze_batch_performance(self, items: List[PurchaseInvoiceItem]) -> Dict[str, Any]:
        batch_performance = {}
        for item in items:
            batch = item.batch_number or "NO_BATCH"
            if batch not in batch_performance:
                batch_performance[batch] = {
                    "total_received": 0,
                    "total_sold": 0,
                    "conversion_rate": 0
                }
            
            batch_performance[batch]["total_received"] += item.purchased_quantity
            batch_performance[batch]["total_sold"] += item.sold_quantity
            
            if item.purchased_quantity > 0:
                batch_performance[batch]["conversion_rate"] = (
                    batch_performance[batch]["total_sold"] / 
                    batch_performance[batch]["total_received"]
                ) * 100
        
        return batch_performance
    
    def _analyze_receipt_patterns(self, items: List[PurchaseInvoiceItem]) -> Dict[str, Any]:
        receipt_dates = [item.invoice.received_date for item in items]
        receipt_dates.sort()
        
        return {
            "total_receipts": len(receipt_dates),
            "first_received": receipt_dates[0] if receipt_dates else None,
            "last_received": receipt_dates[-1] if receipt_dates else None
        }
    
    def _analyze_sales_patterns(self, items: List[PurchaseInvoiceItem]) -> Dict[str, Any]:
        all_sales = []
        for item in items:
            for sale in item.sales:
                all_sales.append({
                    "date": sale.sale_date,
                    "quantity": sale.quantity_sold
                })
        
        if not all_sales:
            return {"no_sales": True}
        
        return {
            "total_sales_transactions": len(all_sales),
            "sales_velocity": len(all_sales) / max(1, len(set(sale["date"] for sale in all_sales)))
        }
    
    def _calculate_conversion_rate(self, items: List[PurchaseInvoiceItem]) -> Dict[str, Any]:
        total_purchased = sum(item.purchased_quantity for item in items)
        total_sold = sum(item.sold_quantity for item in items)
        
        conversion_rate = (total_sold / total_purchased * 100) if total_purchased > 0 else 0
        
        return {
            "conversion_rate_percentage": conversion_rate
        }
    
    def _generate_movement_prediction(self, parameters: Dict[str, Any], items: List[PurchaseInvoiceItem]) -> Dict[str, Any]:
        return {
            "category": "medium_moving",
            "recommendation": "Maintain current stock levels"
        }