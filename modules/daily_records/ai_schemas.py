from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, date

# AI Analytics Response Schemas

class SalesTrendData(BaseModel):
    avg_daily_sales: float
    sales_growth_rate: float
    sales_volatility: float
    best_day: Optional[str]
    worst_day: Optional[str]

class CashTrendData(BaseModel):
    avg_cash_difference: float
    cash_accuracy_rate: float
    largest_discrepancy: float
    cash_flow_stability: float

class BillPatternsData(BaseModel):
    avg_bill_value: float
    avg_bills_per_day: float
    bill_value_trend: float
    customer_frequency_trend: float

class TrendsAnalysis(BaseModel):
    sales_trend: SalesTrendData
    cash_trend: CashTrendData
    bill_patterns: BillPatternsData
    day_wise_performance: Dict[str, Dict[str, float]]

class SalesForecast(BaseModel):
    predicted_values: List[float]
    avg_predicted_daily_sales: float
    total_predicted_sales: float
    confidence_score: float

class CashDifferenceForecast(BaseModel):
    predicted_differences: List[float]
    avg_predicted_difference: float
    risk_level: str

class PredictionsData(BaseModel):
    sales_forecast: Optional[SalesForecast]
    cash_difference_forecast: Optional[CashDifferenceForecast]

class ChartDataset(BaseModel):
    label: str
    data: List[float]
    borderColor: Optional[str] = None
    backgroundColor: Optional[str] = None
    yAxisID: Optional[str] = None

class ChartData(BaseModel):
    labels: List[str]
    datasets: List[ChartDataset]

class ChartsCollection(BaseModel):
    sales_trend: ChartData
    cash_differences: ChartData
    day_performance: ChartData
    bills_vs_sales: ChartData

class AIInsights(BaseModel):
    ai_analysis: str
    generated_at: str
    data_period: str
    analysis_type: str

class DataQuality(BaseModel):
    completeness: float
    missing_days: int
    data_consistency: str

class AnalysisSummary(BaseModel):
    total_records: int
    date_range: Dict[str, str]
    analysis_date: str

class ComprehensiveAnalysisResponse(BaseModel):
    analysis_summary: AnalysisSummary
    trends: TrendsAnalysis
    predictions: PredictionsData
    ai_insights: AIInsights
    chart_data: ChartsCollection
    data_quality: DataQuality

class TrendsAnalysisResponse(BaseModel):
    analysis_period: str
    data_points: int
    trends: TrendsAnalysis
    generated_at: str

class PredictionsResponse(BaseModel):
    historical_period: str
    forecast_period: str
    predictions: PredictionsData
    generated_at: str

class ChartDataResponse(BaseModel):
    period: str
    data_points: int
    charts: ChartsCollection
    generated_at: str

class InsightsResponse(BaseModel):
    analysis_period: str
    insights: AIInsights
    data_quality: Dict[str, Any]

class AlertItem(BaseModel):
    type: str  # warning, danger, info, success
    message: str
    priority: str  # low, medium, high, critical

class KeyMetrics(BaseModel):
    avg_daily_sales: float
    sales_growth_rate: float
    cash_accuracy_rate: float
    avg_bill_value: float

class DashboardResponse(BaseModel):
    summary: AnalysisSummary
    key_metrics: KeyMetrics
    predictions: PredictionsData
    chart_data: ChartsCollection
    ai_insights: AIInsights
    data_quality: DataQuality
    alerts: List[AlertItem]

# Frontend Chart Configuration Schemas

class ChartOptions(BaseModel):
    responsive: bool = True
    maintainAspectRatio: bool = False
    plugins: Dict[str, Any] = {}
    scales: Dict[str, Any] = {}

class LineChartConfig(BaseModel):
    type: str = "line"
    data: ChartData
    options: ChartOptions

class BarChartConfig(BaseModel):
    type: str = "bar"
    data: ChartData
    options: ChartOptions

class DoughnutChartConfig(BaseModel):
    type: str = "doughnut"
    data: ChartData
    options: ChartOptions

# Business Intelligence Schemas

class BusinessMetric(BaseModel):
    name: str
    value: float
    unit: str
    trend: str  # up, down, stable
    change_percentage: float
    status: str  # good, warning, critical

class PerformanceIndicator(BaseModel):
    category: str
    metrics: List[BusinessMetric]
    score: float  # 0-100
    recommendations: List[str]

class BusinessIntelligenceReport(BaseModel):
    report_date: datetime
    period_analyzed: str
    overall_score: float
    performance_indicators: List[PerformanceIndicator]
    key_insights: List[str]
    action_items: List[str]
    risk_factors: List[str]
    opportunities: List[str]

# Error Response Schema

class AIAnalyticsError(BaseModel):
    error: str
    message: str
    timestamp: str
    suggested_action: Optional[str] = None