# Training Data Export Implementation Summary

## Overview

The Training Data Export feature allows data scientists to export natural language query-SQL pairs for fine-tuning custom models. All exports are privacy-safe with automatic anonymization of sensitive data, and support multiple export formats with comprehensive dataset statistics.

## Implementation Details

### Core Module

**File**: `ai_agent_connector/app/utils/training_data_export.py`

**Key Components**:

1. **TrainingDataExporter Class**: Main exporter manager
   - Query-SQL pair storage
   - Privacy-safe anonymization
   - Format conversion (JSONL, JSON, CSV)
   - Dataset statistics generation
   - Filtering and pagination

2. **Data Classes**:
   - `QuerySQLPair`: Represents a natural language query paired with SQL
   - `DatasetStatistics`: Statistics about the exported dataset
   - `ExportFormat`: Enum for supported export formats

3. **Anonymization**:
   - Email addresses
   - Phone numbers
   - Social Security Numbers
   - Credit card numbers
   - IP addresses
   - Database names

### Features Implemented

#### 1. Privacy-Safe Export

- **Automatic Anonymization**: Sensitive data patterns detected and anonymized using regex
- **Consistent Hashing**: SHA256 hashing ensures same values produce same anonymized values
- **Configurable**: Anonymization can be disabled if needed
- **Database Name Protection**: Database names are hashed to protect sensitive information

#### 2. Format Conversion

- **JSONL Format** (Recommended): One JSON object per line, ideal for fine-tuning
- **JSON Format**: Array format with metadata and statistics
- **CSV Format**: Tabular format for analysis in Excel/spreadsheets

#### 3. Dataset Statistics

- Total pairs count
- Success/failure counts
- Unique tables referenced
- Database types distribution
- Average query and SQL lengths
- Date range (earliest/latest)
- Query type distribution (SELECT, INSERT, UPDATE, DELETE, etc.)

#### 4. Query-SQL Pair Management

- Add pairs with metadata
- List pairs with filtering (date range, success status)
- Get individual pairs by ID
- Delete pairs
- Pagination support

### Export Formats

#### JSONL Format (Recommended for Fine-Tuning)

```jsonl
{"pair_id": "abc-123", "natural_language_query": "Show all users", "sql_query": "SELECT * FROM users", "timestamp": "2024-01-01T00:00:00", "success": true}
{"pair_id": "abc-124", "natural_language_query": "Count orders", "sql_query": "SELECT COUNT(*) FROM orders", "timestamp": "2024-01-01T00:01:00", "success": true}
```

**Advantages**:
- One example per line (easy to stream)
- Compatible with most ML frameworks
- Efficient for large datasets
- Standard format for fine-tuning LLMs

#### JSON Format

Includes metadata and statistics:

```json
{
  "exported_at": "2024-01-01T00:00:00",
  "format_version": "1.0",
  "total_pairs": 1000,
  "pairs": [...],
  "statistics": {...}
}
```

#### CSV Format

Tabular format for analysis:

```csv
pair_id,natural_language_query,sql_query,timestamp,database_type,database_name,table_names,success,execution_time_ms,query_type
```

### API Endpoints

**File**: `TRAINING_DATA_EXPORT_ENDPOINTS.md` (documentation)

**Endpoints** (6 total):
1. `POST /api/training-data/pairs` - Add query-SQL pair
2. `GET /api/training-data/pairs` - List pairs (with filtering/pagination)
3. `GET /api/training-data/pairs/<pair_id>` - Get specific pair
4. `DELETE /api/training-data/pairs/<pair_id>` - Delete pair
5. `GET /api/training-data/statistics` - Get dataset statistics
6. `GET /api/training-data/export` - Export data (JSONL/JSON/CSV)

### Integration Points

1. **Query Execution**: Should integrate with natural language query execution endpoints to automatically collect pairs
2. **API Routes**: Endpoints documented in `TRAINING_DATA_EXPORT_ENDPOINTS.md`
3. **Utils Module**: `training_data_export.py` - Core export module

### Privacy & Security

1. **Sensitive Data Detection**:
   - Regex patterns for emails, phone numbers, SSNs, credit cards, IPs
   - Automatic detection and anonymization
   - Consistent hashing for reproducible anonymization

2. **Database Name Protection**:
   - Database names are hashed
   - Table/column names in SQL are preserved (needed for training)

3. **Configurable Privacy**:
   - Anonymization can be disabled if needed
   - Default is to anonymize (privacy-first)

### Data Storage

Currently uses in-memory storage (list). For production:

1. **Recommendations**:
   - Use database (PostgreSQL, MongoDB, etc.)
   - Implement data retention policies
   - Regular exports to persistent storage
   - Indexing for efficient querying

2. **Current Limits**:
   - No explicit limit (all pairs stored in memory)
   - Should implement limits/archival for production

### Documentation

1. **User Guide**: `docs/TRAINING_DATA_EXPORT_GUIDE.md`
   - Overview and features
   - Privacy and anonymization
   - Export formats
   - API reference
   - Integration guide
   - Fine-tuning workflow
   - Best practices
   - Troubleshooting

2. **API Endpoints**: `TRAINING_DATA_EXPORT_ENDPOINTS.md`
   - Endpoint documentation
   - Request/response examples
   - Integration notes

3. **README Update**: Added feature to main README

## Usage Examples

### Add Query-SQL Pair

```python
from ai_agent_connector.app.utils.training_data_export import training_data_exporter

pair = training_data_exporter.add_query_sql_pair(
    natural_language_query="Show me all active users",
    sql_query="SELECT * FROM users WHERE status = 'active'",
    database_type="postgresql",
    database_name="production_db",
    success=True,
    execution_time_ms=45.5
)
```

### Export Data

```python
from ai_agent_connector.app.utils.training_data_export import (
    training_data_exporter,
    ExportFormat
)

# Export to JSONL (recommended)
count, stats = training_data_exporter.export(
    'training_data.jsonl',
    format=ExportFormat.JSONL,
    start_date='2024-01-01',
    end_date='2024-01-31',
    filter_successful_only=True
)

print(f"Exported {count} pairs")
print(f"Statistics: {stats.to_dict()}")
```

### Get Statistics

```python
stats = training_data_exporter.get_statistics(
    start_date='2024-01-01',
    end_date='2024-01-31'
)

print(f"Total pairs: {stats.total_pairs}")
print(f"Success rate: {stats.successful_pairs / stats.total_pairs * 100:.1f}%")
print(f"Unique tables: {len(stats.unique_tables)}")
```

## Next Steps

1. **API Integration**: Add endpoints from `TRAINING_DATA_EXPORT_ENDPOINTS.md` to `routes.py`

2. **Automatic Collection**: Integrate pair collection into natural language query execution:
   - Add pairs when queries are executed successfully
   - Optionally track failed queries
   - Include execution time and metadata

3. **Database Storage**: Implement database storage for production:
   - Create database schema
   - Migrate from in-memory storage
   - Implement data retention policies

4. **Testing**: Create unit and integration tests:
   - Test anonymization patterns
   - Test export formats
   - Test statistics generation
   - Test API endpoints

5. **Documentation**: 
   - Add integration examples to user guide
   - Create developer documentation
   - Add troubleshooting guide

## Files Created/Modified

### New Files

1. `ai_agent_connector/app/utils/training_data_export.py` - Core export module
2. `docs/TRAINING_DATA_EXPORT_GUIDE.md` - User guide
3. `TRAINING_DATA_EXPORT_ENDPOINTS.md` - API endpoints documentation
4. `TRAINING_DATA_EXPORT_SUMMARY.md` - This file

### Modified Files

1. `README.md` - Added feature description

## Acceptance Criteria Status

✅ **Privacy-safe export**: Implemented with regex-based anonymization for emails, phone numbers, SSNs, credit cards, IPs, and database names

✅ **Format conversion**: JSONL (recommended), JSON, and CSV formats supported

✅ **Dataset stats**: Comprehensive statistics including total pairs, success rates, unique tables, database types, average lengths, date range, and query type distribution

## Compliance Considerations

- **GDPR**: Anonymization of personal data (emails, phone numbers)
- **HIPAA**: With proper configuration and review
- **Privacy by Design**: Automatic anonymization enabled by default
- **Data Minimization**: Only necessary data included in exports

## Performance Considerations

1. **In-Memory Storage**: Current implementation uses in-memory storage which is fast but limited
2. **Anonymization Performance**: Regex-based anonymization is efficient but may slow down for very large datasets
3. **Export Performance**: Large exports may take time, consider streaming for very large datasets
4. **Database Migration**: For production, migrate to database for scalability

## Future Enhancements

1. **Additional Anonymization Patterns**:
   - Custom regex patterns
   - Configuration-based patterns
   - Domain-specific anonymization rules

2. **Advanced Statistics**:
   - Query complexity metrics
   - SQL pattern analysis
   - Data quality scores

3. **Export Enhancements**:
   - Streaming exports for large datasets
   - Compression options
   - Incremental exports

4. **Integration Enhancements**:
   - Automatic collection from audit logs
   - Batch import from external sources
   - Integration with ML pipelines

5. **Quality Control**:
   - Duplicate detection
   - Quality scoring
   - Automated filtering rules


