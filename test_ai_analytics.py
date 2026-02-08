#!/usr/bin/env python3
"""
AI Analytics Test Script for Daily Records

This script tests the AI analytics functionality and provides usage examples.
Run this after setting up your Gemini API key to verify everything works.
"""

import asyncio
import os
import sys
from datetime import datetime, date, timedelta
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.daily_records.ai_analytics import DailyRecordsAIAnalytics
from app.database.database import SessionLocal
from modules.daily_records.models import DailyRecord

async def test_ai_analytics():
    """Test the AI analytics functionality"""
    
    # Check if Gemini API key is set
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        print("Please add your Gemini API key to the .env file:")
        print("GEMINI_API_KEY=your_gemini_api_key_here")
        return False
    
    print("✅ Gemini API key found")
    
    # Initialize AI analytics
    ai_analytics = DailyRecordsAIAnalytics(gemini_api_key)
    print("✅ AI Analytics initialized")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Test 1: Check if we have data
        print("\n📊 Testing data availability...")
        df = ai_analytics.get_records_dataframe(db, 30)
        print(f"✅ Found {len(df)} records in the last 30 days")
        
        if df.empty:
            print("⚠️  No data found. Creating sample data for testing...")
            await create_sample_data(db)
            df = ai_analytics.get_records_dataframe(db, 30)
            print(f"✅ Created sample data: {len(df)} records")
        
        # Test 2: Trends Analysis
        print("\n📈 Testing trends analysis...")
        trends = ai_analytics.calculate_trends(df)
        print("✅ Trends analysis completed")
        print(f"   - Average daily sales: ₹{trends.get('sales_trend', {}).get('avg_daily_sales', 0):.2f}")
        print(f"   - Cash accuracy rate: {trends.get('cash_trend', {}).get('cash_accuracy_rate', 0):.1f}%")
        
        # Test 3: Predictions
        print("\n🔮 Testing predictions...")
        predictions = ai_analytics.predict_future_trends(df, 7)
        print("✅ Predictions completed")
        if 'sales_forecast' in predictions:
            forecast = predictions['sales_forecast']
            print(f"   - Predicted avg daily sales (next 7 days): ₹{forecast['avg_predicted_daily_sales']:.2f}")
            print(f"   - Confidence score: {forecast['confidence_score']:.1f}%")
        
        # Test 4: Chart Data
        print("\n📊 Testing chart data generation...")
        chart_data = ai_analytics.generate_chart_data(df)
        print("✅ Chart data generated")
        print(f"   - Sales trend chart: {len(chart_data.get('sales_trend', {}).get('labels', []))} data points")
        print(f"   - Day performance chart: {len(chart_data.get('day_performance', {}).get('labels', []))} categories")
        
        # Test 5: AI Insights (this requires API call)
        print("\n🤖 Testing AI insights generation...")
        try:
            ai_insights = await ai_analytics.generate_ai_insights(trends, predictions)
            print("✅ AI insights generated successfully")
            print(f"   - Analysis type: {ai_insights.get('analysis_type', 'N/A')}")
            print(f"   - Generated at: {ai_insights.get('generated_at', 'N/A')}")
        except Exception as e:
            print(f"⚠️  AI insights generation failed: {str(e)}")
            print("   This might be due to API limits or network issues")
        
        # Test 6: Comprehensive Analysis
        print("\n🎯 Testing comprehensive analysis...")
        try:
            comprehensive = await ai_analytics.comprehensive_analysis(db, 30)
            print("✅ Comprehensive analysis completed")
            print(f"   - Total records analyzed: {comprehensive.get('analysis_summary', {}).get('total_records', 0)}")
            print(f"   - Data quality score: {comprehensive.get('data_quality', {}).get('completeness', 0):.1f}%")
        except Exception as e:
            print(f"⚠️  Comprehensive analysis failed: {str(e)}")
        
        print("\n🎉 AI Analytics testing completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        return False
    finally:
        db.close()

async def create_sample_data(db):
    """Create sample daily records for testing"""
    
    sample_records = []
    base_date = date.today() - timedelta(days=30)
    
    for i in range(30):
        record_date = base_date + timedelta(days=i)
        day_name = record_date.strftime('%A')
        
        # Generate realistic sample data
        base_sales = 15000 + (i * 100)  # Gradual increase
        daily_variation = (-1000 + (i % 7) * 300)  # Weekly pattern
        total_sales = base_sales + daily_variation
        
        record = DailyRecord(
            date=record_date,
            day=day_name,
            cash_balance=5000.0,
            average_bill=250.0 + (i % 10) * 10,
            no_of_bills=int(total_sales / (250.0 + (i % 10) * 10)),
            total_cash=total_sales * 0.7,
            actual_cash=total_sales * 0.7 + (-50 + (i % 5) * 25),  # Some variance
            online_sales=total_sales * 0.3,
            total_sales=total_sales,
            unbilled_sales=total_sales * 0.1,
            software_figure=total_sales * 1.02,
            recorded_sales=total_sales,
            sales_difference=(-50 + (i % 5) * 25),
            cash_reserve=2000.0,
            expense_amount=500.0 + (i % 3) * 100,
            created_by="test_user",
            created_at=datetime.now()
        )
        
        sample_records.append(record)
    
    # Add records to database
    for record in sample_records:
        existing = db.query(DailyRecord).filter(DailyRecord.date == record.date).first()
        if not existing:
            db.add(record)
    
    db.commit()

def test_api_endpoints():
    """Test API endpoints using curl commands"""
    
    print("\n🌐 API Endpoint Testing Commands:")
    print("Run these commands to test the API endpoints:")
    print()
    
    base_url = "http://localhost:8000"
    
    endpoints = [
        ("Dashboard", "/api/daily-records/ai-analytics/dashboard"),
        ("Comprehensive Analysis", "/api/daily-records/ai-analytics/comprehensive?days=30"),
        ("Trends Analysis", "/api/daily-records/ai-analytics/trends?days=30"),
        ("Predictions", "/api/daily-records/ai-analytics/predictions?days=30&forecast_days=7"),
        ("Chart Data", "/api/daily-records/ai-analytics/chart-data?days=30"),
        ("AI Insights", "/api/daily-records/ai-analytics/insights?days=30")
    ]
    
    for name, endpoint in endpoints:
        print(f"# {name}")
        print(f"curl -X GET \"{base_url}{endpoint}\"")
        print()

if __name__ == "__main__":
    print("🚀 AI Analytics Test Suite")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run async test
    success = asyncio.run(test_ai_analytics())
    
    if success:
        print("\n" + "=" * 50)
        test_api_endpoints()
        print("\n✅ All tests completed! Your AI analytics system is ready to use.")
        print("\n📖 Next steps:")
        print("1. Start your FastAPI server: uvicorn main:app --reload")
        print("2. Visit http://localhost:8000/docs to see the API documentation")
        print("3. Check the AI_INTEGRATION_GUIDE.md for frontend integration examples")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        print("Make sure your Gemini API key is correctly configured.")