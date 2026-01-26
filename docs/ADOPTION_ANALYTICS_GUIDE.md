# Adoption Analytics Guide

The Adoption Analytics system provides comprehensive insights into how your AI Agent Connector platform is being used, including daily active users (DAU), query patterns, and feature usage statistics. All telemetry is opt-in and uses anonymous data collection to protect user privacy.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Getting Started](#getting-started)
4. [Telemetry Opt-In/Opt-Out](#telemetry-opt-inopt-out)
5. [Dashboard](#dashboard)
6. [API Reference](#api-reference)
7. [Exporting Data](#exporting-data)
8. [Privacy & Security](#privacy--security)
9. [Integration Guide](#integration-guide)

## Overview

Adoption Analytics helps product managers and administrators understand:

- **Daily Active Users (DAU)**: Track how many unique users interact with the platform each day
- **Query Patterns**: Analyze the types of queries being executed and their performance
- **Feature Usage**: Understand which features are most popular and how often they're used
- **Adoption Trends**: Identify growth trends and feature adoption rates

All data is collected anonymously (with user/agent IDs hashed) and respects user privacy preferences.

## Features

### Daily Active Users (DAU)

Track unique users per day with:
- Current DAU (today's active users)
- Historical DAU timeseries
- User activity patterns

### Query Patterns

Analyze query execution patterns:
- Query types (SELECT, INSERT, UPDATE, DELETE, etc.)
- Execution time statistics
- Success rates
- User distribution per pattern type

### Feature Usage

Track feature adoption:
- Total usage counts per feature
- Unique users per feature
- Unique agents per feature
- Daily usage trends
- Most popular features

### Export to BI Tools

Export data in formats suitable for business intelligence tools:
- JSON export (structured data)
- CSV export (tabular data for Excel, Tableau, etc.)

## Getting Started

### Enabling Analytics

Analytics are enabled by default. To disable globally:

```python
from ai_agent_connector.app.utils.adoption_analytics import adoption_analytics

adoption_analytics.telemetry_enabled = False
```

### Accessing the Dashboard

Navigate to `/analytics` in your browser to view the analytics dashboard:

```
http://localhost:5000/analytics
```

The dashboard provides:
- Key metrics overview (DAU, unique users, total events)
- Interactive charts (DAU timeseries, feature usage)
- Detailed tables (top features, query patterns)
- Export functionality

## Telemetry Opt-In/Opt-Out

### Default Behavior

By default, all users are opted-in to telemetry collection. Users can opt-out at any time.

### Opt-In

Users can opt-in to telemetry via the API:

```bash
curl -X POST http://localhost:5000/api/analytics/telemetry/opt-in \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123"}'
```

### Opt-Out

Users can opt-out of telemetry:

```bash
curl -X POST http://localhost:5000/api/analytics/telemetry/opt-out \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123"}'
```

### Check Status

Check if a user has opted-in:

```bash
curl http://localhost:5000/api/analytics/telemetry/status/user-123
```

Response:
```json
{
  "user_id": "user-123",
  "opted_in": true,
  "telemetry_enabled": true
}
```

## Dashboard

### Key Metrics

The dashboard displays:

1. **Daily Active Users (Today)**: Number of unique users active today
2. **Unique Users (Period)**: Total unique users in the selected date range
3. **Total Events (Period)**: Total number of events tracked in the period
4. **Top Feature**: Most used feature

### Charts

#### DAU Timeseries

Shows daily active users over time with a line chart. Use date range controls to adjust the period.

#### Feature Usage

Bar chart showing the top 10 most used features. Helps identify popular features and adoption patterns.

### Tables

#### Top Features

Table showing:
- Feature type
- Total uses
- Unique users
- Unique agents
- Last used timestamp

#### Query Patterns

Table showing:
- Pattern type (SELECT, INSERT, etc.)
- Count (number of times executed)
- Average execution time (milliseconds)
- Success rate (percentage)
- Unique users

## API Reference

### Track Event

Track a feature usage event (typically called internally by other endpoints):

```bash
curl -X POST http://localhost:5000/api/analytics/events \
  -H "Content-Type: application/json" \
  -d '{
    "feature_type": "query_execution",
    "user_id": "user-123",
    "agent_id": "agent-456",
    "metadata": {"query_type": "SELECT"}
  }'
```

Available feature types:
- `query_execution`
- `natural_language_query`
- `widget_query`
- `query_optimization`
- `multi_agent_collaboration`
- `scheduled_query`
- `query_sharing`
- `visualization`
- `export`
- `prompt_studio`
- `sso_login`
- `agent_registration`
- `database_connection`

### Get DAU

Get daily active users for a specific date:

```bash
curl "http://localhost:5000/api/analytics/dau?date=2024-01-15"
```

Response:
```json
{
  "date": "2024-01-15",
  "dau": 42
}
```

### Get DAU Timeseries

Get DAU data for a date range:

```bash
curl "http://localhost:5000/api/analytics/dau/timeseries?start_date=2024-01-01&end_date=2024-01-31"
```

Response:
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "timeseries": [
    {"date": "2024-01-01", "dau": 35},
    {"date": "2024-01-02", "dau": 42},
    ...
  ]
}
```

### Get Query Patterns

Get query pattern statistics:

```bash
curl http://localhost:5000/api/analytics/query-patterns
```

Response:
```json
{
  "patterns": {
    "SELECT": {
      "pattern_type": "SELECT",
      "count": 1250,
      "avg_execution_time_ms": 145.5,
      "success_rate": 0.98,
      "unique_users": ["user1", "user2", ...]
    },
    ...
  }
}
```

### Get Feature Usage

Get feature usage statistics:

```bash
# All features
curl http://localhost:5000/api/analytics/features

# Specific feature
curl "http://localhost:5000/api/analytics/features?feature_type=query_execution"
```

### Get Top Features

Get top used features:

```bash
curl "http://localhost:5000/api/analytics/features/top?limit=10"
```

### Get Adoption Summary

Get comprehensive adoption summary:

```bash
curl "http://localhost:5000/api/analytics/summary?start_date=2024-01-01&end_date=2024-01-31"
```

Response includes:
- Period information
- DAU timeseries
- Unique users
- Total events
- Top features
- Feature adoption breakdown
- Query patterns

## Exporting Data

### Export to JSON

Export all analytics data to JSON:

```bash
curl "http://localhost:5000/api/analytics/export?format=json&start_date=2024-01-01&end_date=2024-01-31" \
  -o analytics-2024-01-01-to-2024-01-31.json
```

### Export to CSV

Export specific data types to CSV:

```bash
# DAU data
curl "http://localhost:5000/api/analytics/export?format=csv&data_type=dau&start_date=2024-01-01&end_date=2024-01-31" \
  -o dau-data.csv

# Feature usage
curl "http://localhost:5000/api/analytics/export?format=csv&data_type=features" \
  -o feature-usage.csv

# Query patterns
curl "http://localhost:5000/api/analytics/export?format=csv&data_type=patterns" \
  -o query-patterns.csv

# Summary
curl "http://localhost:5000/api/analytics/export?format=csv&data_type=summary&start_date=2024-01-01&end_date=2024-01-31" \
  -o summary.csv
```

### Using in BI Tools

The exported CSV files can be imported into:

- **Excel**: Direct import
- **Tableau**: Import as CSV data source
- **Power BI**: Get Data → Text/CSV
- **Google Sheets**: File → Import → Upload

JSON exports can be used with:
- **Python/Pandas**: `pd.read_json()`
- **R**: `jsonlite` package
- **JavaScript**: `JSON.parse()`

## Privacy & Security

### Anonymous Data Collection

All user and agent IDs are anonymized using SHA256 hashing before storage:

```python
# Original ID: "user-123"
# Stored as: "a1b2c3d4e5f6g7h8" (hashed)
```

Original IDs are never stored in analytics data.

### Opt-In by Default

Users are opted-in to telemetry by default. They can opt-out at any time, and their existing data will be removed.

### Data Retention

Analytics data is stored in-memory by default. In production, you should:

1. **Use a database**: Store analytics data in a database (PostgreSQL, MongoDB, etc.)
2. **Set retention policies**: Implement data retention policies to automatically delete old data
3. **Regular exports**: Export data regularly to persistent storage

### Compliance

The analytics system is designed to be compliant with:
- **GDPR**: Users can opt-out and data is anonymized
- **CCPA**: Users can request deletion of their data (opt-out)
- **HIPAA**: With proper configuration (anonymization enabled)

## Integration Guide

### Tracking Events in Your Code

To track feature usage in your endpoints, use the analytics module:

```python
from ai_agent_connector.app.utils.adoption_analytics import (
    adoption_analytics,
    FeatureType,
    QueryPatternType
)

# Track feature usage
adoption_analytics.track_event(
    FeatureType.QUERY_EXECUTION,
    user_id=user_id,
    agent_id=agent_id,
    metadata={'query_type': 'SELECT', 'success': True}
)

# Track query pattern
adoption_analytics.track_query_pattern(
    QueryPatternType.SELECT,
    user_id=user_id,
    agent_id=agent_id,
    execution_time_ms=145.5,
    success=True
)
```

### Example: Integrating with Query Execution

```python
@api_bp.route('/api/agents/<agent_id>/query', methods=['POST'])
def execute_query(agent_id: str):
    # ... existing query execution code ...
    
    start_time = time.time()
    try:
        results = connector.execute_query(query)
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Track analytics event
        adoption_analytics.track_event(
            FeatureType.QUERY_EXECUTION,
            user_id=user_id,
            agent_id=agent_id,
            metadata={'query_type': query_type, 'success': True}
        )
        
        # Track query pattern
        pattern_type = QueryPatternType.SELECT  # Determine from query
        adoption_analytics.track_query_pattern(
            pattern_type,
            user_id=user_id,
            agent_id=agent_id,
            execution_time_ms=execution_time_ms,
            success=True
        )
        
        return jsonify({'results': results}), 200
    except Exception as e:
        # Track failure
        adoption_analytics.track_event(
            FeatureType.QUERY_EXECUTION,
            user_id=user_id,
            agent_id=agent_id,
            metadata={'query_type': query_type, 'success': False, 'error': str(e)}
        )
        raise
```

### Example: Integrating with Feature Usage

```python
# Track widget query
adoption_analytics.track_event(
    FeatureType.WIDGET_QUERY,
    user_id=user_id,
    agent_id=agent_id
)

# Track query optimization
adoption_analytics.track_event(
    FeatureType.QUERY_OPTIMIZATION,
    user_id=user_id,
    agent_id=agent_id
)

# Track multi-agent collaboration
adoption_analytics.track_event(
    FeatureType.MULTI_AGENT_COLLABORATION,
    user_id=user_id,
    agent_id=agent_id
)
```

## Best Practices

1. **Respect Opt-Out**: Always check if telemetry is enabled before tracking:
   ```python
   if adoption_analytics.telemetry_enabled:
       adoption_analytics.track_event(...)
   ```

2. **Track Meaningful Events**: Only track events that provide value for product decisions

3. **Use Appropriate Metadata**: Include relevant context in metadata, but avoid sensitive data

4. **Regular Exports**: Export analytics data regularly to persistent storage

5. **Monitor Privacy**: Regularly review what data is being collected and ensure compliance

## Troubleshooting

### Dashboard Not Showing Data

- Check that telemetry is enabled: `adoption_analytics.telemetry_enabled`
- Verify events are being tracked (check API logs)
- Ensure date range includes dates with activity

### Export Fails

- Check file permissions for the export directory
- Verify date format is `YYYY-MM-DD`
- Check server logs for error messages

### Opt-Out Not Working

- Verify user_id is correct
- Check that opt-out endpoint was called successfully
- New events should not be tracked after opt-out

## Support

For questions or issues with Adoption Analytics:

1. Check the [API documentation](#api-reference)
2. Review [integration examples](#integration-guide)
3. Consult the [troubleshooting section](#troubleshooting)
4. Open an issue on GitHub

