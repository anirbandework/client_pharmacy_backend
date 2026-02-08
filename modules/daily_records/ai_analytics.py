import google.genai as genai
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from .models import DailyRecord
import json
import os
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

class DailyRecordsAIAnalytics:
    def __init__(self, gemini_api_key: str):
        self.client = genai.Client(api_key=gemini_api_key)
        self.scaler = StandardScaler()
    
    def get_records_dataframe(self, db: Session, days: int = 90) -> pd.DataFrame:
        """Convert daily records to pandas DataFrame for analysis"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        records = db.query(DailyRecord).filter(
            DailyRecord.date >= start_date,
            DailyRecord.date <= end_date
        ).order_by(DailyRecord.date).all()
        
        data = []
        for record in records:
            data.append({
                'date': record.date,
                'day': record.day,
                'cash_balance': record.cash_balance or 0,
                'average_bill': record.average_bill or 0,
                'no_of_bills': record.no_of_bills or 0,
                'total_cash': record.total_cash or 0,
                'actual_cash': record.actual_cash or 0,
                'online_sales': record.online_sales or 0,
                'total_sales': record.total_sales or 0,
                'unbilled_sales': record.unbilled_sales or 0,
                'software_figure': record.software_figure or 0,
                'recorded_sales': record.recorded_sales or 0,
                'sales_difference': record.sales_difference or 0,
                'cash_reserve': record.cash_reserve or 0,
                'expense_amount': record.expense_amount or 0
            })
        
        return pd.DataFrame(data)
    
    def calculate_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate statistical trends and patterns"""
        if df.empty:
            return {}
        
        trends = {}
        
        # Sales trends
        trends['sales_trend'] = {
            'avg_daily_sales': df['total_sales'].mean(),
            'sales_growth_rate': self._calculate_growth_rate(df['total_sales']),
            'sales_volatility': df['total_sales'].std(),
            'best_day': df.loc[df['total_sales'].idxmax(), 'day'] if not df['total_sales'].isna().all() else None,
            'worst_day': df.loc[df['total_sales'].idxmin(), 'day'] if not df['total_sales'].isna().all() else None
        }
        
        # Cash management trends
        trends['cash_trend'] = {
            'avg_cash_difference': df['sales_difference'].mean(),
            'cash_accuracy_rate': len(df[abs(df['sales_difference']) <= 100]) / len(df) * 100,
            'largest_discrepancy': df['sales_difference'].abs().max(),
            'cash_flow_stability': df['cash_balance'].std()
        }
        
        # Bill patterns
        trends['bill_patterns'] = {
            'avg_bill_value': df['average_bill'].mean(),
            'avg_bills_per_day': df['no_of_bills'].mean(),
            'bill_value_trend': self._calculate_growth_rate(df['average_bill']),
            'customer_frequency_trend': self._calculate_growth_rate(df['no_of_bills'])
        }
        
        # Day-wise performance
        day_performance = df.groupby('day').agg({
            'total_sales': 'mean',
            'no_of_bills': 'mean',
            'average_bill': 'mean'
        }).to_dict('index')
        trends['day_wise_performance'] = day_performance
        
        return trends
    
    def _calculate_growth_rate(self, series: pd.Series) -> float:
        """Calculate growth rate using linear regression"""
        if len(series) < 2 or series.isna().all():
            return 0.0
        
        valid_data = series.dropna()
        if len(valid_data) < 2:
            return 0.0
        
        X = np.arange(len(valid_data)).reshape(-1, 1)
        y = valid_data.values
        
        try:
            model = LinearRegression()
            model.fit(X, y)
            return float(model.coef_[0])
        except:
            return 0.0
    
    def predict_future_trends(self, df: pd.DataFrame, days_ahead: int = 30) -> Dict[str, Any]:
        """Predict future trends using machine learning"""
        if df.empty or len(df) < 7:
            return {"error": "Insufficient data for predictions"}
        
        predictions = {}
        
        # Prepare features for prediction
        df_clean = df.dropna()
        if len(df_clean) < 7:
            return {"error": "Insufficient clean data for predictions"}
        
        # Sales prediction
        X = np.arange(len(df_clean)).reshape(-1, 1)
        
        # Predict total sales
        if not df_clean['total_sales'].isna().all():
            y_sales = df_clean['total_sales'].values
            sales_model = LinearRegression()
            sales_model.fit(X, y_sales)
            
            future_X = np.arange(len(df_clean), len(df_clean) + days_ahead).reshape(-1, 1)
            future_sales = sales_model.predict(future_X)
            
            predictions['sales_forecast'] = {
                'predicted_values': future_sales.tolist(),
                'avg_predicted_daily_sales': float(np.mean(future_sales)),
                'total_predicted_sales': float(np.sum(future_sales)),
                'confidence_score': max(0, min(100, 100 - (df_clean['total_sales'].std() / df_clean['total_sales'].mean() * 100)))
            }
        
        # Predict cash differences
        if not df_clean['sales_difference'].isna().all():
            y_diff = df_clean['sales_difference'].values
            diff_model = LinearRegression()
            diff_model.fit(X, y_diff)
            
            future_diff = diff_model.predict(future_X)
            predictions['cash_difference_forecast'] = {
                'predicted_differences': future_diff.tolist(),
                'avg_predicted_difference': float(np.mean(future_diff)),
                'risk_level': 'High' if abs(np.mean(future_diff)) > 200 else 'Medium' if abs(np.mean(future_diff)) > 100 else 'Low'
            }
        
        return predictions
    
    async def generate_ai_insights(self, trends: Dict[str, Any], predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights using Gemini"""
        
        prompt = f"""
        As a pharmacy business analyst, analyze the following daily records data and provide detailed insights:

        TRENDS DATA:
        {json.dumps(trends, indent=2)}

        PREDICTIONS DATA:
        {json.dumps(predictions, indent=2)}

        Please provide a comprehensive analysis including:
        1. Business Performance Summary (current state)
        2. Key Strengths and Opportunities
        3. Critical Issues and Risks
        4. Future Predictions Analysis
        5. Specific Improvement Recommendations
        6. Action Items with Priority Levels
        7. Financial Health Assessment
        8. Operational Efficiency Insights

        Format the response as a structured analysis with clear sections and actionable insights.
        Focus on practical, implementable recommendations for a pharmacy business.
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-1.5-pro',
                contents=prompt
            )
            
            # Parse AI response
            ai_insights = {
                "ai_analysis": response.text,
                "generated_at": datetime.now().isoformat(),
                "data_period": "Last 90 days",
                "analysis_type": "Comprehensive Business Intelligence"
            }
            
            return ai_insights
            
        except Exception as e:
            return {
                "error": f"AI analysis failed: {str(e)}",
                "fallback_insights": self._generate_fallback_insights(trends, predictions)
            }
    
    def _generate_fallback_insights(self, trends: Dict[str, Any], predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic insights when AI fails"""
        insights = {
            "performance_summary": "Analysis based on statistical trends",
            "key_findings": [],
            "recommendations": []
        }
        
        # Sales analysis
        if 'sales_trend' in trends:
            sales = trends['sales_trend']
            if sales['sales_growth_rate'] > 0:
                insights["key_findings"].append("Positive sales growth trend detected")
            else:
                insights["key_findings"].append("Sales decline trend - requires attention")
        
        # Cash management
        if 'cash_trend' in trends:
            cash = trends['cash_trend']
            if cash['cash_accuracy_rate'] < 80:
                insights["recommendations"].append("Improve cash handling procedures - accuracy below 80%")
        
        return insights
    
    def generate_chart_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate data formatted for frontend charts"""
        if df.empty:
            return {}
        
        chart_data = {}
        
        # Sales trend chart
        chart_data['sales_trend'] = {
            'labels': [str(d) for d in df['date'].tolist()],
            'datasets': [{
                'label': 'Total Sales',
                'data': df['total_sales'].fillna(0).tolist(),
                'borderColor': 'rgb(75, 192, 192)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)'
            }]
        }
        
        # Cash difference chart
        chart_data['cash_differences'] = {
            'labels': [str(d) for d in df['date'].tolist()],
            'datasets': [{
                'label': 'Cash Differences',
                'data': df['sales_difference'].fillna(0).tolist(),
                'borderColor': 'rgb(255, 99, 132)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)'
            }]
        }
        
        # Day-wise performance
        day_stats = df.groupby('day')['total_sales'].mean().fillna(0)
        chart_data['day_performance'] = {
            'labels': day_stats.index.tolist(),
            'datasets': [{
                'label': 'Average Sales by Day',
                'data': day_stats.values.tolist(),
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 205, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(153, 102, 255, 0.8)',
                    'rgba(255, 159, 64, 0.8)',
                    'rgba(199, 199, 199, 0.8)'
                ]
            }]
        }
        
        # Bills vs Sales correlation
        chart_data['bills_vs_sales'] = {
            'labels': [str(d) for d in df['date'].tolist()],
            'datasets': [
                {
                    'label': 'Number of Bills',
                    'data': df['no_of_bills'].fillna(0).tolist(),
                    'borderColor': 'rgb(54, 162, 235)',
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                    'yAxisID': 'y'
                },
                {
                    'label': 'Total Sales',
                    'data': df['total_sales'].fillna(0).tolist(),
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'yAxisID': 'y1'
                }
            ]
        }
        
        return chart_data
    
    async def comprehensive_analysis(self, db: Session, days: int = 90) -> Dict[str, Any]:
        """Run complete AI analysis pipeline"""
        
        # Get data
        df = self.get_records_dataframe(db, days)
        
        if df.empty:
            return {
                "error": "No data available for analysis",
                "message": "Please ensure daily records are being created"
            }
        
        # Calculate trends
        trends = self.calculate_trends(df)
        
        # Generate predictions
        predictions = self.predict_future_trends(df)
        
        # Generate AI insights
        ai_insights = await self.generate_ai_insights(trends, predictions)
        
        # Generate chart data
        chart_data = self.generate_chart_data(df)
        
        return {
            "analysis_summary": {
                "total_records": len(df),
                "date_range": {
                    "start": str(df['date'].min()) if not df.empty else None,
                    "end": str(df['date'].max()) if not df.empty else None
                },
                "analysis_date": datetime.now().isoformat()
            },
            "trends": trends,
            "predictions": predictions,
            "ai_insights": ai_insights,
            "chart_data": chart_data,
            "data_quality": {
                "completeness": (df.notna().sum().sum() / (len(df) * len(df.columns))) * 100,
                "missing_days": days - len(df),
                "data_consistency": "Good" if len(df) > days * 0.8 else "Poor"
            }
        }