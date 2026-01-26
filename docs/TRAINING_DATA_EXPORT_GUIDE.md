# Training Data Export Guide

The Training Data Export system allows data scientists to export query-SQL pairs for fine-tuning custom models. All exports are privacy-safe with automatic anonymization of sensitive data.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Getting Started](#getting-started)
4. [Privacy & Anonymization](#privacy--anonymization)
5. [Export Formats](#export-formats)
6. [API Reference](#api-reference)
7. [Dataset Statistics](#dataset-statistics)
8. [Integration Guide](#integration-guide)

## Overview

Training Data Export helps data scientists:

- **Export Query-SQL Pairs**: Export natural language queries paired with generated SQL
- **Privacy-Safe Exports**: Automatic anonymization of sensitive data (emails, phone numbers, SSNs, etc.)
- **Multiple Formats**: Export to JSONL (recommended for fine-tuning), JSON, or CSV
- **Dataset Statistics**: Get comprehensive statistics about your training dataset
- **Flexible Filtering**: Filter by date range, success status, and more

## Features

### Privacy-Safe Export

- **Automatic Anonymization**: Sensitive data in queries is automatically anonymized
  - Email addresses: `user_abc123@example.com`
  - Phone numbers: `XXX-XXX-1234`
  - SSNs: `XXX-XX-1234`
  - Credit cards: `XXXX-XXXX-XXXX-1234`
  - IP addresses: `XXX.XXX.XXX.123`
- **Database Name Anonymization**: Database names are hashed to protect sensitive information
- **Configurable**: Anonymization can be disabled if needed (not recommended for production)

### Format Conversion

- **JSONL** (JSON Lines): One JSON object per line - preferred format for fine-tuning
- **JSON**: Array format with metadata and statistics
- **CSV**: Tabular format for analysis in Excel/spreadsheets

### Dataset Statistics

- Total number of pairs
- Success/failure counts
- Unique tables referenced
- Database types distribution
- Average query and SQL lengths
- Date range
- Query type distribution (SELECT, INSERT, UPDATE, etc.)

## Getting Started

### Enabling Training Data Collection

Training data collection is enabled by default. To disable anonymization:

```python
from ai_agent_connector.app.utils.training_data_export import training_data_exporter

training_data_exporter.anonymize_sensitive_data = False
```

### Adding Query-SQL Pairs

Pairs are typically added automatically when natural language queries are executed. You can also add pairs manually:

```bash
curl -X POST http://localhost:5000/api/training-data/pairs \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language_query": "Show me all users",
    "sql_query": "SELECT * FROM users",
    "database_type": "postgresql",
    "database_name": "production_db",
    "success": true,
    "execution_time_ms": 45.5
  }'
```

## Privacy & Anonymization

### What Gets Anonymized

The exporter automatically detects and anonymizes:

1. **Email Addresses**: `john.doe@example.com` → `user_abc123@example.com`
2. **Phone Numbers**: `555-123-4567` → `XXX-XXX-1234`
3. **Social Security Numbers**: `123-45-6789` → `XXX-XX-1234`
4. **Credit Card Numbers**: `1234-5678-9012-3456` → `XXXX-XXXX-XXXX-1234`
5. **IP Addresses**: `192.168.1.1` → `XXX.XXX.XXX.123`
6. **Database Names**: `production_db` → `db_abc123`

### How Anonymization Works

- **Hashing**: Sensitive values are hashed using SHA256
- **Consistent Mapping**: Same original value always produces the same anonymized value
- **Partial Preservation**: Some structure is preserved (email domains, partial numbers) for realism
- **SQL Queries**: SQL queries are **not** anonymized (they may contain table/column names that are needed for training)

### Privacy Best Practices

1. **Review Exports**: Always review exported data before using for training
2. **Database Names**: Database names are anonymized, but table/column names in SQL are preserved
3. **Custom Patterns**: You can extend the anonymization patterns if needed
4. **Audit Access**: Restrict access to training data exports (sensitive information)

## Export Formats

### JSONL Format (Recommended)

JSONL (JSON Lines) format is preferred for fine-tuning LLMs. Each line is a separate JSON object:

```jsonl
{"pair_id": "abc-123", "natural_language_query": "Show all users", "sql_query": "SELECT * FROM users", "timestamp": "2024-01-01T00:00:00", "success": true}
{"pair_id": "abc-124", "natural_language_query": "Count orders", "sql_query": "SELECT COUNT(*) FROM orders", "timestamp": "2024-01-01T00:01:00", "success": true}
```

**Usage for Fine-Tuning**:
- One example per line
- Easy to stream and process
- Compatible with most ML frameworks
- Efficient for large datasets

### JSON Format

JSON format includes metadata and statistics:

```json
{
  "exported_at": "2024-01-01T00:00:00",
  "format_version": "1.0",
  "total_pairs": 1000,
  "pairs": [
    {
      "pair_id": "abc-123",
      "natural_language_query": "Show all users",
      "sql_query": "SELECT * FROM users",
      "timestamp": "2024-01-01T00:00:00",
      "success": true
    }
  ],
  "statistics": {
    "total_pairs": 1000,
    "successful_pairs": 950,
    "failed_pairs": 50,
    "unique_tables": ["users", "orders"],
    "database_types": ["postgresql"],
    "avg_query_length": 45.5,
    "avg_sql_length": 120.3
  }
}
```

### CSV Format

CSV format for analysis in Excel/spreadsheets:

```csv
pair_id,natural_language_query,sql_query,timestamp,database_type,database_name,table_names,success,execution_time_ms,query_type
abc-123,Show all users,SELECT * FROM users,2024-01-01T00:00:00,postgresql,db_abc123,users,true,45.5,SELECT
```

## API Reference

### Add Query-SQL Pair

Add a pair to the training dataset:

```bash
POST /api/training-data/pairs
Content-Type: application/json

{
  "natural_language_query": "Show me all users",
  "sql_query": "SELECT * FROM users",
  "database_type": "postgresql",
  "database_name": "production_db",
  "success": true,
  "execution_time_ms": 45.5,
  "metadata": {}
}
```

**Response** (201 Created):
```json
{
  "pair": {
    "pair_id": "abc-123",
    "natural_language_query": "Show me all users",
    "sql_query": "SELECT * FROM users",
    "timestamp": "2024-01-01T00:00:00",
    "database_type": "postgresql",
    "database_name": "db_abc123",
    "table_names": ["users"],
    "success": true,
    "execution_time_ms": 45.5,
    "metadata": {}
  }
}
```

### List Query-SQL Pairs

List pairs with filtering and pagination:

```bash
GET /api/training-data/pairs?start_date=2024-01-01&end_date=2024-01-31&successful_only=true&limit=100&offset=0
```

**Query Parameters**:
- `start_date`: Filter by start date (ISO format)
- `end_date`: Filter by end date (ISO format)
- `successful_only`: Only return successful pairs (true/false)
- `limit`: Maximum number of pairs to return
- `offset`: Number of pairs to skip

**Response** (200 OK):
```json
{
  "pairs": [
    {
      "pair_id": "abc-123",
      "natural_language_query": "Show all users",
      "sql_query": "SELECT * FROM users",
      "timestamp": "2024-01-01T00:00:00",
      "success": true
    }
  ],
  "total": 100
}
```

### Get Query-SQL Pair

Get a specific pair by ID:

```bash
GET /api/training-data/pairs/abc-123
```

**Response** (200 OK):
```json
{
  "pair": {
    "pair_id": "abc-123",
    "natural_language_query": "Show all users",
    "sql_query": "SELECT * FROM users",
    "timestamp": "2024-01-01T00:00:00",
    "success": true
  }
}
```

### Delete Query-SQL Pair

Delete a pair by ID:

```bash
DELETE /api/training-data/pairs/abc-123
```

**Response** (200 OK):
```json
{
  "message": "Pair deleted successfully"
}
```

### Get Dataset Statistics

Get statistics about the training dataset:

```bash
GET /api/training-data/statistics?start_date=2024-01-01&end_date=2024-01-31
```

**Response** (200 OK):
```json
{
  "statistics": {
    "total_pairs": 1000,
    "successful_pairs": 950,
    "failed_pairs": 50,
    "unique_tables": ["users", "orders", "products"],
    "database_types": ["postgresql", "mysql"],
    "avg_query_length": 45.5,
    "avg_sql_length": 120.3,
    "date_range": {
      "start": "2024-01-01T00:00:00",
      "end": "2024-01-31T23:59:59"
    },
    "query_type_distribution": {
      "SELECT": 800,
      "INSERT": 100,
      "UPDATE": 50,
      "DELETE": 0
    }
  }
}
```

### Export Training Data

Export training data in specified format:

```bash
GET /api/training-data/export?format=jsonl&start_date=2024-01-01&end_date=2024-01-31&successful_only=true
```

**Query Parameters**:
- `format`: Export format (`jsonl`, `json`, `csv`) - default: `jsonl`
- `start_date`: Filter by start date (ISO format)
- `end_date`: Filter by end date (ISO format)
- `successful_only`: Only export successful pairs (true/false)

**Response**: File download with appropriate MIME type

## Dataset Statistics

### Available Statistics

1. **Total Pairs**: Total number of query-SQL pairs
2. **Success/Failure Counts**: Number of successful vs failed pairs
3. **Unique Tables**: Set of unique table names referenced in SQL queries
4. **Database Types**: Distribution of database types (postgresql, mysql, etc.)
5. **Average Lengths**: Average length of natural language queries and SQL queries
6. **Date Range**: Earliest and latest timestamps
7. **Query Type Distribution**: Count of each query type (SELECT, INSERT, UPDATE, DELETE, etc.)

### Using Statistics

Statistics help you:

- **Quality Assessment**: Check success rates and identify patterns
- **Dataset Planning**: Understand data distribution and coverage
- **Training Preparation**: Ensure adequate representation of query types
- **Monitoring**: Track dataset growth and quality over time

## Integration Guide

### Automatic Collection

To automatically collect training pairs when natural language queries are executed:

```python
from ai_agent_connector.app.utils.training_data_export import training_data_exporter
import time

@api_bp.route('/api/agents/<agent_id>/query/natural-language', methods=['POST'])
def execute_natural_language_query(agent_id: str):
    data = request.get_json()
    natural_language_query = data.get('query')
    
    # Get connector and converter
    connector = agent_registry.get_database_connector(agent_id)
    converter = NLToSQLConverter()
    
    try:
        # Convert to SQL
        sql_query = converter.convert_to_sql(natural_language_query, connector)
        
        # Execute query
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
        # Optionally track failed queries
        training_data_exporter.add_query_sql_pair(
            natural_language_query=natural_language_query,
            sql_query='',  # No SQL if conversion failed
            success=False,
            metadata={'error': str(e), 'agent_id': agent_id}
        )
        raise
```

### Manual Collection

You can also add pairs manually:

```python
from ai_agent_connector.app.utils.training_data_export import training_data_exporter

pair = training_data_exporter.add_query_sql_pair(
    natural_language_query="Show me all active users",
    sql_query="SELECT * FROM users WHERE status = 'active'",
    database_type="postgresql",
    success=True
)
```

### Exporting Data

Export in different formats:

```python
# Export to JSONL (recommended for fine-tuning)
count, stats = training_data_exporter.export(
    'training_data.jsonl',
    format=ExportFormat.JSONL,
    start_date='2024-01-01',
    end_date='2024-01-31',
    filter_successful_only=True
)

# Export to JSON
count, stats = training_data_exporter.export(
    'training_data.json',
    format=ExportFormat.JSON
)

# Export to CSV
count, stats = training_data_exporter.export(
    'training_data.csv',
    format=ExportFormat.CSV
)
```

## Fine-Tuning Workflow

### Step 1: Collect Data

Ensure training pairs are being collected automatically or add them manually.

### Step 2: Review Statistics

```bash
curl "http://localhost:5000/api/training-data/statistics"
```

Review the statistics to ensure:
- Adequate number of pairs
- Good success rate
- Diverse query types
- Coverage of different tables

### Step 3: Export Data

Export in JSONL format (recommended):

```bash
curl "http://localhost:5000/api/training-data/export?format=jsonl&successful_only=true" \
  -o training_data.jsonl
```

### Step 4: Prepare for Fine-Tuning

Convert to your fine-tuning format if needed. Most frameworks accept JSONL with format:
```jsonl
{"prompt": "Show me all users", "completion": "SELECT * FROM users"}
```

You may need to transform the exported format:
```python
import json

with open('training_data.jsonl', 'r') as f_in, open('fine_tune_data.jsonl', 'w') as f_out:
    for line in f_in:
        pair = json.loads(line)
        fine_tune_record = {
            "prompt": pair["natural_language_query"],
            "completion": pair["sql_query"]
        }
        f_out.write(json.dumps(fine_tune_record) + '\n')
```

### Step 5: Fine-Tune Model

Use your ML framework (OpenAI, Hugging Face, etc.) to fine-tune your model with the exported data.

## Best Practices

1. **Privacy First**: Always review exported data for any sensitive information
2. **Quality Control**: Filter to only successful pairs for training
3. **Diverse Data**: Ensure coverage of different query types and tables
4. **Regular Exports**: Export regularly to build up training datasets
5. **Version Control**: Tag exports with dates/versions for tracking
6. **Test Sets**: Reserve some data for testing/validation
7. **Anonymization**: Keep anonymization enabled unless absolutely necessary

## Troubleshooting

### No Data to Export

- Check that pairs are being collected (verify integration with query execution)
- Check date range filters
- Verify success filter settings

### Export Fails

- Check file permissions
- Verify date format (must be ISO format: YYYY-MM-DD)
- Check server logs for errors

### Anonymization Issues

- Review anonymization patterns if needed
- Verify anonymization is enabled: `training_data_exporter.anonymize_sensitive_data`
- Check that sensitive data patterns are being detected

### Format Issues

- JSONL: Ensure one JSON object per line
- JSON: Valid JSON array format
- CSV: Standard CSV with proper escaping

## Support

For questions or issues with Training Data Export:

1. Check the [API documentation](#api-reference)
2. Review [integration examples](#integration-guide)
3. Consult the [troubleshooting section](#troubleshooting)
4. Open an issue on GitHub


