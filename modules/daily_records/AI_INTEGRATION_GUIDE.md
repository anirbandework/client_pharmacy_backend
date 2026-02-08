# AI Analytics Integration Guide

## Overview
This guide provides comprehensive information on integrating the AI-powered analytics system for daily records with your frontend application.

## API Endpoints

### 1. Comprehensive Analysis
**GET** `/api/daily-records/ai-analytics/comprehensive?days=90`

Returns complete AI analysis including trends, predictions, insights, and chart data.

```javascript
// Example Frontend Usage
const getComprehensiveAnalysis = async (days = 90) => {
  try {
    const response = await fetch(`/api/daily-records/ai-analytics/comprehensive?days=${days}`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to fetch comprehensive analysis:', error);
  }
};
```

### 2. Trends Analysis
**GET** `/api/daily-records/ai-analytics/trends?days=90`

Returns statistical trends and patterns.

### 3. Future Predictions
**GET** `/api/daily-records/ai-analytics/predictions?days=90&forecast_days=30`

Returns AI-powered future predictions.

### 4. Chart Data
**GET** `/api/daily-records/ai-analytics/chart-data?days=90`

Returns data formatted for Chart.js or similar charting libraries.

### 5. AI Insights
**GET** `/api/daily-records/ai-analytics/insights?days=90`

Returns AI-generated business insights and recommendations.

### 6. AI Dashboard
**GET** `/api/daily-records/ai-analytics/dashboard`

Returns dashboard-ready data with key metrics and alerts.

## Frontend Implementation Examples

### React.js Implementation

```jsx
import React, { useState, useEffect } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const AIAnalyticsDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/daily-records/ai-analytics/dashboard');
      if (!response.ok) throw new Error('Failed to fetch dashboard data');
      const data = await response.json();
      setDashboardData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading AI Analytics...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!dashboardData) return <div>No data available</div>;

  return (
    <div className="ai-analytics-dashboard">
      {/* Key Metrics Cards */}
      <div className="metrics-grid">
        <MetricCard
          title="Average Daily Sales"
          value={dashboardData.key_metrics.avg_daily_sales}
          format="currency"
          trend={dashboardData.key_metrics.sales_growth_rate > 0 ? 'up' : 'down'}
        />
        <MetricCard
          title="Cash Accuracy Rate"
          value={dashboardData.key_metrics.cash_accuracy_rate}
          format="percentage"
          trend={dashboardData.key_metrics.cash_accuracy_rate > 90 ? 'up' : 'down'}
        />
        <MetricCard
          title="Average Bill Value"
          value={dashboardData.key_metrics.avg_bill_value}
          format="currency"
        />
      </div>

      {/* Alerts */}
      {dashboardData.alerts.length > 0 && (
        <div className="alerts-section">
          <h3>Alerts</h3>
          {dashboardData.alerts.map((alert, index) => (
            <Alert key={index} type={alert.type} priority={alert.priority}>
              {alert.message}
            </Alert>
          ))}
        </div>
      )}

      {/* Charts */}
      <div className="charts-grid">
        <div className="chart-container">
          <h3>Sales Trend</h3>
          <Line
            data={dashboardData.chart_data.sales_trend}
            options={{
              responsive: true,
              plugins: {
                legend: { position: 'top' },
                title: { display: true, text: 'Daily Sales Trend' }
              },
              scales: {
                y: { beginAtZero: true }
              }
            }}
          />
        </div>

        <div className="chart-container">
          <h3>Cash Differences</h3>
          <Line
            data={dashboardData.chart_data.cash_differences}
            options={{
              responsive: true,
              plugins: {
                legend: { position: 'top' },
                title: { display: true, text: 'Cash Differences Over Time' }
              }
            }}
          />
        </div>

        <div className="chart-container">
          <h3>Day-wise Performance</h3>
          <Bar
            data={dashboardData.chart_data.day_performance}
            options={{
              responsive: true,
              plugins: {
                legend: { position: 'top' },
                title: { display: true, text: 'Average Sales by Day of Week' }
              }
            }}
          />
        </div>

        <div className="chart-container">
          <h3>Bills vs Sales Correlation</h3>
          <Line
            data={dashboardData.chart_data.bills_vs_sales}
            options={{
              responsive: true,
              interaction: { mode: 'index', intersect: false },
              plugins: {
                title: { display: true, text: 'Bills Count vs Total Sales' }
              },
              scales: {
                y: { type: 'linear', display: true, position: 'left' },
                y1: { type: 'linear', display: true, position: 'right', grid: { drawOnChartArea: false } }
              }
            }}
          />
        </div>
      </div>

      {/* AI Insights */}
      <div className="ai-insights-section">
        <h3>AI-Generated Insights</h3>
        <div className="insights-content">
          <pre>{dashboardData.ai_insights.ai_analysis}</pre>
        </div>
      </div>

      {/* Predictions */}
      {dashboardData.predictions.sales_forecast && (
        <div className="predictions-section">
          <h3>Future Predictions</h3>
          <div className="prediction-cards">
            <div className="prediction-card">
              <h4>Sales Forecast</h4>
              <p>Next 30 days average: ₹{dashboardData.predictions.sales_forecast.avg_predicted_daily_sales.toFixed(2)}</p>
              <p>Confidence: {dashboardData.predictions.sales_forecast.confidence_score.toFixed(1)}%</p>
            </div>
            {dashboardData.predictions.cash_difference_forecast && (
              <div className="prediction-card">
                <h4>Cash Difference Risk</h4>
                <p>Risk Level: {dashboardData.predictions.cash_difference_forecast.risk_level}</p>
                <p>Avg Difference: ₹{dashboardData.predictions.cash_difference_forecast.avg_predicted_difference.toFixed(2)}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Helper Components
const MetricCard = ({ title, value, format, trend }) => {
  const formatValue = (val, fmt) => {
    switch (fmt) {
      case 'currency': return `₹${val.toFixed(2)}`;
      case 'percentage': return `${val.toFixed(1)}%`;
      default: return val.toString();
    }
  };

  return (
    <div className={`metric-card ${trend}`}>
      <h4>{title}</h4>
      <div className="metric-value">{formatValue(value, format)}</div>
      {trend && <div className={`trend-indicator ${trend}`}>
        {trend === 'up' ? '↗️' : '↘️'}
      </div>}
    </div>
  );
};

const Alert = ({ type, priority, children }) => (
  <div className={`alert alert-${type} priority-${priority}`}>
    {children}
  </div>
);

export default AIAnalyticsDashboard;
```

### Vue.js Implementation

```vue
<template>
  <div class="ai-analytics-dashboard">
    <div v-if="loading" class="loading">Loading AI Analytics...</div>
    <div v-else-if="error" class="error">Error: {{ error }}</div>
    <div v-else-if="dashboardData">
      <!-- Key Metrics -->
      <div class="metrics-grid">
        <metric-card
          v-for="metric in keyMetrics"
          :key="metric.key"
          :title="metric.title"
          :value="metric.value"
          :format="metric.format"
          :trend="metric.trend"
        />
      </div>

      <!-- Charts -->
      <div class="charts-grid">
        <div class="chart-container">
          <h3>Sales Trend</h3>
          <Line :data="dashboardData.chart_data.sales_trend" :options="chartOptions.line" />
        </div>
        
        <div class="chart-container">
          <h3>Day-wise Performance</h3>
          <Bar :data="dashboardData.chart_data.day_performance" :options="chartOptions.bar" />
        </div>
      </div>

      <!-- AI Insights -->
      <div class="ai-insights">
        <h3>AI Insights</h3>
        <div class="insights-content">{{ dashboardData.ai_insights.ai_analysis }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { Line, Bar } from 'vue-chartjs/legacy';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend);

export default {
  name: 'AIAnalyticsDashboard',
  components: { Line, Bar },
  data() {
    return {
      dashboardData: null,
      loading: true,
      error: null,
      chartOptions: {
        line: {
          responsive: true,
          plugins: { legend: { position: 'top' } },
          scales: { y: { beginAtZero: true } }
        },
        bar: {
          responsive: true,
          plugins: { legend: { position: 'top' } }
        }
      }
    };
  },
  computed: {
    keyMetrics() {
      if (!this.dashboardData) return [];
      const metrics = this.dashboardData.key_metrics;
      return [
        { key: 'sales', title: 'Avg Daily Sales', value: metrics.avg_daily_sales, format: 'currency', trend: metrics.sales_growth_rate > 0 ? 'up' : 'down' },
        { key: 'accuracy', title: 'Cash Accuracy', value: metrics.cash_accuracy_rate, format: 'percentage' },
        { key: 'bill', title: 'Avg Bill Value', value: metrics.avg_bill_value, format: 'currency' }
      ];
    }
  },
  async mounted() {
    await this.fetchDashboardData();
  },
  methods: {
    async fetchDashboardData() {
      try {
        this.loading = true;
        const response = await fetch('/api/daily-records/ai-analytics/dashboard');
        if (!response.ok) throw new Error('Failed to fetch data');
        this.dashboardData = await response.json();
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

## CSS Styling Examples

```css
.ai-analytics-dashboard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.metric-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  position: relative;
}

.metric-card h4 {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 14px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.trend-indicator {
  position: absolute;
  top: 15px;
  right: 15px;
  font-size: 20px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 30px;
  margin-bottom: 30px;
}

.chart-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chart-container h3 {
  margin: 0 0 20px 0;
  color: #333;
}

.alerts-section {
  margin-bottom: 30px;
}

.alert {
  padding: 12px 16px;
  border-radius: 4px;
  margin-bottom: 10px;
}

.alert-warning { background: #fff3cd; border-left: 4px solid #ffc107; }
.alert-danger { background: #f8d7da; border-left: 4px solid #dc3545; }
.alert-info { background: #d1ecf1; border-left: 4px solid #17a2b8; }

.ai-insights-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

.insights-content {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.5;
}

.predictions-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.prediction-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.prediction-card {
  background: #f8f9fa;
  border-radius: 4px;
  padding: 15px;
  border-left: 4px solid #007bff;
}

.loading, .error {
  text-align: center;
  padding: 40px;
  font-size: 18px;
}

.error { color: #dc3545; }
```

## Integration Steps

1. **Install Dependencies**
   ```bash
   npm install chart.js react-chartjs-2  # For React
   npm install vue-chartjs chart.js      # For Vue
   ```

2. **Set up API Configuration**
   ```javascript
   const API_BASE_URL = 'http://localhost:8000';
   
   const apiClient = {
     get: async (endpoint) => {
       const response = await fetch(`${API_BASE_URL}${endpoint}`);
       if (!response.ok) throw new Error(`HTTP ${response.status}`);
       return response.json();
     }
   };
   ```

3. **Configure Gemini API Key**
   - Add your Gemini API key to the `.env` file
   - Restart the backend server

4. **Test the Integration**
   ```javascript
   // Test API connectivity
   const testAPI = async () => {
     try {
       const data = await apiClient.get('/api/daily-records/ai-analytics/dashboard');
       console.log('AI Analytics working:', data);
     } catch (error) {
       console.error('API Error:', error);
     }
   };
   ```

## Best Practices

1. **Error Handling**: Always implement proper error handling for API calls
2. **Loading States**: Show loading indicators during data fetching
3. **Caching**: Consider caching AI analysis results to reduce API calls
4. **Responsive Design**: Ensure charts are responsive across devices
5. **Performance**: Use lazy loading for heavy chart components
6. **User Experience**: Provide clear feedback when AI analysis is running

## Troubleshooting

- **API Key Issues**: Ensure Gemini API key is correctly set in environment variables
- **CORS Errors**: Configure CORS settings in FastAPI if needed
- **Chart Rendering**: Ensure Chart.js is properly registered with required components
- **Data Format**: Verify API response format matches expected schema

This integration provides a comprehensive AI-powered analytics system that can help identify trends, predict future performance, and provide actionable business insights for your pharmacy management system.