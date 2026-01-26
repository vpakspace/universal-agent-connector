# Analytics API Endpoints to Add

The following endpoints should be added to `ai_agent_connector/app/api/routes.py`.

## Import Statement

Add this import with the other imports at the top of the file:

```python
from ..utils.adoption_analytics import (
    adoption_analytics,
    FeatureType,
    QueryPatternType
)
```

## Endpoints to Add

Add these endpoints in a new section (e.g., before "Result Explanation Endpoints"):

```python
# ============================================================================
# Adoption Analytics Endpoints
# ============================================================================

@api_bp.route('/analytics/telemetry/opt-in', methods=['POST'])
def opt_in_telemetry():
    """
    Opt-in a user to telemetry collection.
    
    Request body:
    {
        "user_id": "user-123"
    }
    
    Returns success message.
    """
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    adoption_analytics.opt_in_telemetry(user_id)
    
    return jsonify({
        'message': 'Telemetry opt-in successful',
        'user_id': user_id
    }), 200


@api_bp.route('/analytics/telemetry/opt-out', methods=['POST'])
def opt_out_telemetry():
    """
    Opt-out a user from telemetry collection.
    
    Request body:
    {
        "user_id": "user-123"
    }
    
    Returns success message.
    """
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    adoption_analytics.opt_out_telemetry(user_id)
    
    return jsonify({
        'message': 'Telemetry opt-out successful',
        'user_id': user_id
    }), 200


@api_bp.route('/analytics/telemetry/status/<user_id>', methods=['GET'])
def get_telemetry_status(user_id: str):
    """
    Get telemetry opt-in status for a user.
    
    Returns opt-in status.
    """
    is_opted_in = adoption_analytics.is_opted_in(user_id)
    
    return jsonify({
        'user_id': user_id,
        'opted_in': is_opted_in,
        'telemetry_enabled': adoption_analytics.telemetry_enabled
    }), 200


@api_bp.route('/analytics/events', methods=['POST'])
def track_analytics_event():
    """
    Track an analytics event (usually called internally by other endpoints).
    
    Request body:
    {
        "feature_type": "query_execution",
        "user_id": "user-123",
        "agent_id": "agent-456",
        "session_id": "session-789",
        "metadata": {}
    }
    
    Returns event ID.
    """
    data = request.get_json() or {}
    
    feature_type_str = data.get('feature_type')
    if not feature_type_str:
        return jsonify({'error': 'feature_type is required'}), 400
    
    try:
        feature_type = FeatureType(feature_type_str)
    except ValueError:
        return jsonify({'error': f'Invalid feature_type: {feature_type_str}'}), 400
    
    event = adoption_analytics.track_event(
        feature_type=feature_type,
        user_id=data.get('user_id'),
        agent_id=data.get('agent_id'),
        session_id=data.get('session_id'),
        metadata=data.get('metadata')
    )
    
    if event:
        return jsonify({
            'event_id': event.event_id,
            'message': 'Event tracked successfully'
        }), 201
    else:
        return jsonify({
            'message': 'Event not tracked (telemetry disabled or user opted out)'
        }), 200


@api_bp.route('/analytics/dau', methods=['GET'])
def get_dau():
    """
    Get daily active users for a date.
    
    Query parameters:
    - date: Date in YYYY-MM-DD format (defaults to today)
    
    Returns DAU count.
    """
    date = request.args.get('date')
    
    dau = adoption_analytics.get_dau(date)
    
    return jsonify({
        'date': date or datetime.utcnow().strftime('%Y-%m-%d'),
        'dau': dau
    }), 200


@api_bp.route('/analytics/dau/timeseries', methods=['GET'])
def get_dau_timeseries():
    """
    Get DAU timeseries data.
    
    Query parameters:
    - start_date: Start date in YYYY-MM-DD format (required)
    - end_date: End date in YYYY-MM-DD format (required)
    
    Returns timeseries data.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date are required'}), 400
    
    timeseries = adoption_analytics.get_dau_timeseries(start_date, end_date)
    
    return jsonify({
        'start_date': start_date,
        'end_date': end_date,
        'timeseries': timeseries
    }), 200


@api_bp.route('/analytics/query-patterns', methods=['GET'])
def get_query_patterns():
    """
    Get query pattern statistics.
    
    Returns query pattern statistics.
    """
    patterns = adoption_analytics.get_query_patterns()
    
    return jsonify({
        'patterns': patterns
    }), 200


@api_bp.route('/analytics/features', methods=['GET'])
def get_feature_usage():
    """
    Get feature usage statistics.
    
    Query parameters:
    - feature_type: Optional feature type to filter by
    
    Returns feature usage statistics.
    """
    feature_type = request.args.get('feature_type')
    
    usage = adoption_analytics.get_feature_usage(feature_type)
    
    return jsonify({
        'feature_usage': usage
    }), 200


@api_bp.route('/analytics/features/top', methods=['GET'])
def get_top_features():
    """
    Get top used features.
    
    Query parameters:
    - limit: Maximum number of features to return (default: 10)
    
    Returns top features.
    """
    limit = int(request.args.get('limit', 10))
    
    top_features = adoption_analytics.get_top_features(limit)
    
    return jsonify({
        'top_features': top_features
    }), 200


@api_bp.route('/analytics/summary', methods=['GET'])
def get_adoption_summary():
    """
    Get adoption analytics summary.
    
    Query parameters:
    - start_date: Optional start date in YYYY-MM-DD format (defaults to 30 days ago)
    - end_date: Optional end date in YYYY-MM-DD format (defaults to today)
    
    Returns adoption summary.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    summary = adoption_analytics.get_adoption_summary(start_date, end_date)
    
    return jsonify({
        'summary': summary
    }), 200


@api_bp.route('/analytics/export', methods=['GET'])
def export_analytics():
    """
    Export analytics data.
    
    Query parameters:
    - format: Export format (json or csv, default: json)
    - start_date: Optional start date in YYYY-MM-DD format
    - end_date: Optional end date in YYYY-MM-DD format
    - data_type: For CSV, type of data to export (dau, features, patterns, summary)
    
    Returns exported data file.
    """
    from flask import send_file
    import tempfile
    import os
    
    export_format = request.args.get('format', 'json').lower()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    data_type = request.args.get('data_type', 'summary')
    
    if export_format not in ['json', 'csv']:
        return jsonify({'error': 'format must be json or csv'}), 400
    
    try:
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix=f'.{export_format}')
        
        try:
            if export_format == 'json':
                adoption_analytics.export_to_json(temp_path, start_date, end_date)
                mimetype = 'application/json'
            else:
                adoption_analytics.export_to_csv(temp_path, data_type, start_date, end_date)
                mimetype = 'text/csv'
            
            # Generate filename
            start_str = start_date or (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
            end_str = end_date or datetime.utcnow().strftime('%Y-%m-%d')
            filename = f'analytics-{start_str}-to-{end_str}.{export_format}'
            
            return send_file(
                temp_path,
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename
            )
        finally:
            # Close file descriptor
            os.close(fd)
            
            # Note: File will be deleted after send_file completes
            # In production, consider using a background task to clean up
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

```

## Additional Notes

1. **Telemetry Tracking Integration**: To automatically track events, you should integrate telemetry tracking into existing endpoints. For example:

```python
# In query execution endpoint
adoption_analytics.track_event(
    FeatureType.QUERY_EXECUTION,
    user_id=user_id,
    agent_id=agent_id,
    metadata={'query_type': 'SELECT', 'success': True}
)

adoption_analytics.track_query_pattern(
    QueryPatternType.SELECT,
    user_id=user_id,
    agent_id=agent_id,
    execution_time_ms=execution_time,
    success=True
)
```

2. **Date Format**: All dates should be in `YYYY-MM-DD` format (ISO 8601 date format).

3. **Import datetime**: Make sure to import `datetime` and `timedelta` at the top of routes.py:
```python
from datetime import datetime, timedelta
```

4. **Telemetry Opt-In Default**: By default, users are opted-in to telemetry. They can opt-out at any time.

5. **Anonymous Data**: All user and agent IDs are anonymized using SHA256 hashing before storage. The original IDs are never stored.

