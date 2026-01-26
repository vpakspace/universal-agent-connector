# Training Data Export API Endpoints to Add

The following endpoints should be added to `ai_agent_connector/app/api/routes.py`.

## Import Statement

Add this import with the other imports at the top of the file:

```python
from ..utils.training_data_export import (
    training_data_exporter,
    QuerySQLPair,
    ExportFormat
)
from datetime import datetime
```

## Endpoints to Add

Add these endpoints in a new section (e.g., before "Result Explanation Endpoints"):

```python
# ============================================================================
# Training Data Export Endpoints
# ============================================================================

@api_bp.route('/training-data/pairs', methods=['POST'])
def add_training_pair():
    """
    Add a query-SQL pair to training data (typically called internally by query execution endpoints).
    
    Request body:
    {
        "natural_language_query": "Show me all users",
        "sql_query": "SELECT * FROM users",
        "database_type": "postgresql",
        "database_name": "production_db",
        "success": true,
        "execution_time_ms": 45.5,
        "metadata": {}
    }
    
    Returns the created pair.
    """
    data = request.get_json() or {}
    
    natural_language_query = data.get('natural_language_query')
    sql_query = data.get('sql_query')
    
    if not natural_language_query or not sql_query:
        return jsonify({'error': 'natural_language_query and sql_query are required'}), 400
    
    try:
        pair = training_data_exporter.add_query_sql_pair(
            natural_language_query=natural_language_query,
            sql_query=sql_query,
            database_type=data.get('database_type'),
            database_name=data.get('database_name'),
            success=data.get('success', True),
            execution_time_ms=data.get('execution_time_ms'),
            metadata=data.get('metadata')
        )
        
        return jsonify({
            'pair': pair.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': f'Failed to add training pair: {str(e)}'}), 500


@api_bp.route('/training-data/pairs', methods=['GET'])
def list_training_pairs():
    """
    List query-SQL pairs with filtering and pagination.
    
    Query parameters:
    - start_date: Filter by start date (ISO format)
    - end_date: Filter by end date (ISO format)
    - successful_only: Only return successful pairs (true/false)
    - limit: Maximum number of pairs to return
    - offset: Number of pairs to skip
    
    Returns list of pairs.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    successful_only = request.args.get('successful_only', 'false').lower() == 'true'
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', 0, type=int)
    
    pairs = training_data_exporter.list_pairs(
        start_date=start_date,
        end_date=end_date,
        filter_successful_only=successful_only,
        limit=limit,
        offset=offset
    )
    
    return jsonify({
        'pairs': [p.to_dict() for p in pairs],
        'total': len(pairs)
    }), 200


@api_bp.route('/training-data/pairs/<pair_id>', methods=['GET'])
def get_training_pair(pair_id: str):
    """
    Get a specific query-SQL pair by ID.
    
    Returns pair details.
    """
    pair = training_data_exporter.get_pair(pair_id)
    if not pair:
        return jsonify({'error': 'Pair not found'}), 404
    
    return jsonify({
        'pair': pair.to_dict()
    }), 200


@api_bp.route('/training-data/pairs/<pair_id>', methods=['DELETE'])
def delete_training_pair(pair_id: str):
    """
    Delete a query-SQL pair by ID.
    
    Returns success message.
    """
    if training_data_exporter.delete_pair(pair_id):
        return jsonify({
            'message': 'Pair deleted successfully'
        }), 200
    else:
        return jsonify({'error': 'Pair not found'}), 404


@api_bp.route('/training-data/statistics', methods=['GET'])
def get_training_statistics():
    """
    Get statistics about the training dataset.
    
    Query parameters:
    - start_date: Filter by start date (ISO format)
    - end_date: Filter by end date (ISO format)
    
    Returns dataset statistics.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    stats = training_data_exporter.get_statistics(
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify({
        'statistics': stats.to_dict()
    }), 200


@api_bp.route('/training-data/export', methods=['GET'])
def export_training_data():
    """
    Export training data in specified format.
    
    Query parameters:
    - format: Export format (jsonl, json, csv) - default: jsonl
    - start_date: Filter by start date (ISO format)
    - end_date: Filter by end date (ISO format)
    - successful_only: Only export successful pairs (true/false)
    
    Returns exported data file.
    """
    from flask import send_file
    import tempfile
    import os
    
    format_str = request.args.get('format', 'jsonl').lower()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    successful_only = request.args.get('successful_only', 'false').lower() == 'true'
    
    # Validate format
    try:
        export_format = ExportFormat(format_str)
    except ValueError:
        return jsonify({'error': f'Invalid format: {format_str}. Must be one of: jsonl, json, csv'}), 400
    
    try:
        # Create temporary file
        file_ext = format_str
        fd, temp_path = tempfile.mkstemp(suffix=f'.{file_ext}')
        
        try:
            # Export data
            count, stats = training_data_exporter.export(
                temp_path,
                format=export_format,
                start_date=start_date,
                end_date=end_date,
                filter_successful_only=successful_only
            )
            
            if count == 0:
                return jsonify({'error': 'No data to export'}), 404
            
            # Determine MIME type
            mimetypes = {
                'jsonl': 'application/x-ndjson',
                'json': 'application/json',
                'csv': 'text/csv'
            }
            mimetype = mimetypes.get(format_str, 'application/octet-stream')
            
            # Generate filename
            start_str = start_date or 'all'
            end_str = end_date or 'all'
            filename = f'training-data-{start_str}-to-{end_str}.{file_ext}'
            
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
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

```

## Additional Notes

1. **Automatic Pair Collection**: To automatically collect training pairs, integrate pair collection into natural language query execution endpoints. For example:

```python
# In execute_natural_language_query endpoint
try:
    sql_query = converter.convert_to_sql(natural_language_query, connector)
    start_time = time.time()
    results = connector.execute_query(sql_query)
    execution_time_ms = (time.time() - start_time) * 1000
    
    # Add to training data
    training_data_exporter.add_query_sql_pair(
        natural_language_query=natural_language_query,
        sql_query=sql_query,
        database_type=connector.database_type,
        database_name=connector.config.get('database'),
        success=True,
        execution_time_ms=execution_time_ms,
        metadata={'agent_id': agent_id}
    )
    
    return jsonify({'results': results}), 200
except Exception as e:
    # Track failed queries too (optional)
    training_data_exporter.add_query_sql_pair(
        natural_language_query=natural_language_query,
        sql_query='',  # No SQL if conversion failed
        success=False,
        metadata={'error': str(e)}
    )
    raise
```

2. **Privacy Considerations**: The exporter automatically anonymizes sensitive data (emails, phone numbers, SSNs, credit cards, IPs) in natural language queries. Database names are also anonymized if `anonymize_sensitive_data` is enabled.

3. **Format Details**:
   - **JSONL** (recommended): One JSON object per line, ideal for fine-tuning LLMs
   - **JSON**: Array of objects with metadata and statistics
   - **CSV**: Tabular format for analysis in Excel/spreadsheets

4. **Statistics Included**:
   - Total pairs
   - Success/failure counts
   - Unique tables
   - Database types
   - Average query/SQL lengths
   - Date range
   - Query type distribution

5. **Import datetime**: Make sure to import `datetime` at the top of routes.py if not already imported.


