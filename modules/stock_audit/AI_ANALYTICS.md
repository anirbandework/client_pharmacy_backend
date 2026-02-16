# Stock Audit AI Analytics

AI-powered analytics for stock audit data using Google Gemini API.

## Features

### 1. Comprehensive Analysis
**Endpoint:** `GET /api/stock-audit/ai-analytics/comprehensive?days=30`

Returns complete analysis including:
- Summary statistics
- Chart data for visualization
- AI-generated insights and recommendations

**Response:**
```json
{
  "summary": {
    "total_audits": 50,
    "total_items": 100,
    "items_with_discrepancies": 15,
    "total_discrepancy_value": 250,
    "audit_completion_rate": 95.5
  },
  "charts": {
    "discrepancy_trend": {...},
    "section_discrepancies": {...},
    "staff_performance": {...}
  },
  "ai_insights": {
    "findings": ["Key finding 1", "Key finding 2"],
    "risks": ["Risk area 1", "Risk area 2"],
    "recommendations": ["Action 1", "Action 2"],
    "predictions": ["Prediction 1", "Prediction 2"]
  },
  "generated_at": "2024-02-16T10:30:00"
}
```

### 2. Chart Data Only
**Endpoint:** `GET /api/stock-audit/ai-analytics/charts?days=30`

Returns data formatted for frontend charts:
- **Discrepancy Trend**: Line chart showing daily average discrepancies
- **Section Discrepancies**: Pie chart of discrepancies by section
- **Staff Performance**: Bar chart comparing staff audit counts and discrepancies found

### 3. AI Insights Only
**Endpoint:** `GET /api/stock-audit/ai-analytics/insights?days=30`

Returns AI-generated insights:
- **Findings**: Key observations from the data
- **Risks**: Areas requiring immediate attention
- **Recommendations**: Specific actionable steps
- **Predictions**: Forecasted issues if trends continue

## Configuration

Add to `.env`:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your API key from: https://makersuite.google.com/app/apikey

## Frontend Integration

### React Example

```javascript
// Fetch comprehensive analysis
const response = await fetch('/api/stock-audit/ai-analytics/comprehensive?days=30', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const data = await response.json();

// Use with Chart.js
<Line data={data.charts.discrepancy_trend} />
<Pie data={data.charts.section_discrepancies} />
<Bar data={data.charts.staff_performance} />

// Display insights
<div>
  <h3>Key Findings</h3>
  {data.ai_insights.findings.map(f => <li>{f}</li>)}
  
  <h3>Recommendations</h3>
  {data.ai_insights.recommendations.map(r => <li>{r}</li>)}
</div>
```

## Use Cases

1. **Daily Dashboard**: Show real-time audit performance with AI insights
2. **Weekly Reports**: Generate automated reports with trend analysis
3. **Staff Training**: Identify areas where staff need additional training
4. **Inventory Optimization**: Get recommendations for reducing discrepancies
5. **Risk Management**: Early warning system for potential stock issues

## Data Analyzed

- Audit records (last N days)
- Stock discrepancies by item, section, and date
- Staff audit performance
- Completion rates and trends
- Section-wise problem areas

## AI Capabilities

The Gemini AI analyzes:
- Patterns in discrepancies
- Staff performance variations
- Section-specific issues
- Temporal trends
- Risk assessment
- Predictive insights

## Error Handling

If Gemini API is unavailable or returns invalid data, the service gracefully falls back to basic insights.

## Performance

- Analysis typically completes in 2-5 seconds
- Caching recommended for frequently accessed data
- Consider running analysis during off-peak hours for large datasets
