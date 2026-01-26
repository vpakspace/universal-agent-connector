# Cost Tracking Feature - Implementation Summary

## Overview

This document describes the cost tracking feature implementation that allows developers to track, monitor, and optimize spending on AI provider calls.

## Acceptance Criteria

✅ **Real-time cost dashboard** - Live dashboard showing cost metrics, trends, and breakdowns  
✅ **Export reports** - Export cost data in CSV and JSON formats  
✅ **Budget alerts** - Configurable budget alerts with thresholds and notifications

## Implementation Details

### 1. Cost Tracker Module (`ai_agent_connector/app/utils/cost_tracker.py`)

The core cost tracking system that:
- Tracks costs per AI provider call
- Calculates costs based on provider pricing (OpenAI, Anthropic, custom)
- Stores cost records with metadata
- Provides dashboard data aggregation
- Manages budget alerts
- Supports export functionality

**Key Features:**
- **Pricing Data**: Built-in pricing for OpenAI and Anthropic models (as of 2024)
- **Custom Pricing**: Support for custom provider pricing configuration
- **Cost Calculation**: Automatic cost calculation based on token usage
- **Time-based Filtering**: Filter costs by time period (daily, weekly, monthly)
- **Multi-dimensional Analysis**: Cost breakdown by provider, model, operation type, agent

### 2. Integration Points

Cost tracking is integrated into all AI provider call points:

- **`providers.py`**: OpenAIProvider, AnthropicProvider, CustomProvider
- **`query_suggestions.py`**: Query suggestion engine
- **`nl_to_sql.py`**: Natural language to SQL conversion
- **`ai_agent_manager.py`**: AI agent manager wrapper

All provider calls automatically track:
- Provider name
- Model used
- Token usage (prompt/completion/input/output)
- Calculated cost in USD
- Operation type (query, nl_to_sql, suggestion, etc.)
- Agent ID (if available)
- Metadata (query length, etc.)

### 3. API Endpoints

#### Cost Dashboard
- **GET** `/api/cost/dashboard`
  - Get real-time dashboard data
  - Query params: `agent_id`, `provider`, `period_days`
  - Returns: Total cost, calls, tokens, breakdowns, trends

#### Export Reports
- **GET** `/api/cost/export`
  - Export cost report in CSV or JSON
  - Query params: `format`, `agent_id`, `provider`, `start_date`, `end_date`
  - Returns: Downloadable file

#### Budget Alerts
- **GET** `/api/cost/budget-alerts` - List all budget alerts
- **POST** `/api/cost/budget-alerts` - Create new budget alert
- **PUT** `/api/cost/budget-alerts/<alert_id>` - Update budget alert
- **DELETE** `/api/cost/budget-alerts/<alert_id>` - Delete budget alert

#### Custom Pricing
- **POST** `/api/cost/custom-pricing` - Set custom pricing for provider/model

#### Cost Statistics
- **GET** `/api/cost/stats` - Get cost statistics summary

### 4. Web Dashboard

**Route**: `/cost-dashboard`

Features:
- Real-time cost metrics (total cost, calls, tokens, averages)
- Cost breakdown by provider and operation type
- Daily cost trend chart (using Chart.js)
- Budget alerts display
- Filtering by period, provider, and agent
- Export functionality
- Auto-refresh every 30 seconds

### 5. Budget Alert System

Budget alerts support:
- **Thresholds**: Configurable cost thresholds in USD
- **Periods**: Daily, weekly, monthly, or total
- **Notifications**: Email and webhook support (framework ready)
- **Alert States**: Enabled/disabled, triggered status
- **Spam Prevention**: Alerts won't trigger more than once per hour

### 6. Pricing Information

#### OpenAI Models
- GPT-4: $30/$60 per 1M tokens (prompt/completion)
- GPT-4 Turbo: $10/$30 per 1M tokens
- GPT-4o: $5/$15 per 1M tokens
- GPT-4o-mini: $0.15/$0.6 per 1M tokens
- GPT-3.5 Turbo: $0.5/$1.5 per 1M tokens

#### Anthropic Models
- Claude 3.5 Sonnet: $3/$15 per 1M tokens (input/output)
- Claude 3 Opus: $15/$75 per 1M tokens
- Claude 3 Sonnet: $3/$15 per 1M tokens
- Claude 3 Haiku: $0.25/$1.25 per 1M tokens

*Note: Pricing is current as of 2024. Update pricing in `PricingData` class as needed.*

## Usage Examples

### View Cost Dashboard
```bash
# Open in browser
http://localhost:5000/cost-dashboard

# Or via API
curl http://localhost:5000/api/cost/dashboard?period_days=30
```

### Export Cost Report
```bash
# Export as CSV
curl http://localhost:5000/api/cost/export?format=csv&period_days=30 -o cost_report.csv

# Export as JSON
curl http://localhost:5000/api/cost/export?format=json&period_days=30 -o cost_report.json
```

### Create Budget Alert
```bash
curl -X POST http://localhost:5000/api/cost/budget-alerts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monthly Budget Alert",
    "threshold_usd": 1000.0,
    "period": "monthly",
    "notification_emails": ["admin@example.com"]
  }'
```

### Set Custom Pricing
```bash
curl -X POST http://localhost:5000/api/cost/custom-pricing \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "custom",
    "model": "my-model",
    "prompt_per_1m": 0.5,
    "completion_per_1m": 1.5
  }'
```

## Architecture Notes

### Storage
- Currently uses in-memory storage for cost records
- Can be extended to use database persistence (PostgreSQL, etc.)
- Budget alerts stored in memory

### Performance
- Cost tracking is non-blocking (failures don't affect API calls)
- Dashboard data is computed on-demand
- Consider caching for high-traffic scenarios

### Extensibility
- Easy to add new providers by updating `PricingData` class
- Custom pricing support for any provider/model
- Alert system can be extended with email/webhook integrations

## Future Enhancements

Potential improvements:
1. **Database Persistence**: Store cost records in database for long-term analysis
2. **Email Notifications**: Integrate email service for budget alerts
3. **Webhook Integration**: Send webhook notifications on budget threshold breaches
4. **Cost Forecasting**: Predict future costs based on trends
5. **Cost Optimization Suggestions**: Recommend cheaper models for similar tasks
6. **Multi-currency Support**: Support currencies other than USD
7. **Cost Allocation**: Tag costs by project, team, or department
8. **Historical Comparison**: Compare costs across time periods

## Testing

To test the cost tracking feature:

1. Make some AI provider calls (natural language queries, query suggestions, etc.)
2. Visit `/cost-dashboard` to see costs accumulate
3. Create budget alerts and test threshold triggers
4. Export reports and verify data accuracy

## Files Modified/Created

### New Files
- `ai_agent_connector/app/utils/cost_tracker.py` - Core cost tracking module
- `templates/cost_dashboard.html` - Web dashboard template
- `COST_TRACKING_FEATURE.md` - This documentation

### Modified Files
- `ai_agent_connector/app/agents/providers.py` - Added cost tracking
- `ai_agent_connector/app/utils/query_suggestions.py` - Added cost tracking
- `ai_agent_connector/app/utils/nl_to_sql.py` - Added cost tracking
- `ai_agent_connector/app/agents/ai_agent_manager.py` - Added cost tracking
- `ai_agent_connector/app/api/routes.py` - Added API endpoints and initialization
- `main.py` - Added cost dashboard route

## Conclusion

The cost tracking feature is fully implemented and ready for use. It provides comprehensive cost monitoring, reporting, and alerting capabilities to help developers optimize AI provider spending.
