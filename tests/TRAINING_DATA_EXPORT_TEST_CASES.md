# Training Data Export Test Cases

This document describes comprehensive test scenarios for the training data export system.

## Test Categories

1. [Query-SQL Pair Management](#query-sql-pair-management)
2. [Privacy & Anonymization](#privacy--anonymization)
3. [Export Formats](#export-formats)
4. [Dataset Statistics](#dataset-statistics)
5. [Filtering & Pagination](#filtering--pagination)
6. [API Endpoints](#api-endpoints)
7. [Edge Cases and Error Handling](#edge-cases-and-error-handling)

---

## Query-SQL Pair Management

### Test Case: Create Query-SQL Pair
**Objective**: Verify that query-SQL pairs can be created successfully

**Steps**:
1. Create a pair with natural language query and SQL query
2. Verify pair is stored with correct fields
3. Verify pair_id is auto-generated
4. Verify timestamp is set
5. Verify table names are extracted from SQL

**Expected Result**: Pair created successfully with all fields populated

---

### Test Case: Create Pair with Metadata
**Objective**: Verify that pairs can include metadata

**Steps**:
1. Create a pair with metadata dictionary
2. Verify metadata is stored correctly
3. Retrieve pair and verify metadata is preserved

**Expected Result**: Metadata stored and retrieved correctly

---

### Test Case: Create Pair with Database Information
**Objective**: Verify that database type and name can be stored

**Steps**:
1. Create a pair with database_type and database_name
2. Verify database information is stored
3. Verify database_name is anonymized if anonymization is enabled

**Expected Result**: Database information stored correctly

---

### Test Case: Extract Table Names from SQL
**Objective**: Verify that table names are correctly extracted from SQL

**Steps**:
1. Create pair with SQL containing FROM clause
2. Verify table names are extracted
3. Create pair with SQL containing JOIN clause
4. Verify multiple table names are extracted
5. Verify duplicate table names are removed

**Expected Result**: Table names extracted correctly from SQL

---

### Test Case: Detect Query Type
**Objective**: Verify that SQL query type is correctly detected

**Steps**:
1. Create pairs with different query types (SELECT, INSERT, UPDATE, DELETE)
2. Verify query type is detected correctly for each
3. Test with CREATE, ALTER, DROP statements
4. Verify OTHER type for unknown query types

**Expected Result**: Query types detected correctly

---

## Privacy & Anonymization

### Test Case: Anonymize Email Addresses
**Objective**: Verify that email addresses are anonymized in natural language queries

**Steps**:
1. Create pair with natural language query containing email address
2. Verify email is anonymized (user_hash@example.com)
3. Verify domain is preserved
4. Verify same email produces same anonymized value

**Expected Result**: Email addresses anonymized consistently

---

### Test Case: Anonymize Phone Numbers
**Objective**: Verify that phone numbers are anonymized

**Steps**:
1. Create pair with natural language query containing phone number
2. Verify phone number is anonymized (XXX-XXX-####)
3. Test with different phone number formats
4. Verify consistent anonymization

**Expected Result**: Phone numbers anonymized correctly

---

### Test Case: Anonymize SSNs
**Objective**: Verify that Social Security Numbers are anonymized

**Steps**:
1. Create pair with natural language query containing SSN
2. Verify SSN is anonymized (XXX-XX-####)
3. Test with different SSN formats
4. Verify consistent anonymization

**Expected Result**: SSNs anonymized correctly

---

### Test Case: Anonymize Credit Card Numbers
**Objective**: Verify that credit card numbers are anonymized

**Steps**:
1. Create pair with natural language query containing credit card number
2. Verify credit card is anonymized (XXXX-XXXX-XXXX-####)
3. Test with different credit card formats
4. Verify consistent anonymization

**Expected Result**: Credit card numbers anonymized correctly

---

### Test Case: Anonymize IP Addresses
**Objective**: Verify that IP addresses are anonymized

**Steps**:
1. Create pair with natural language query containing IP address
2. Verify IP is anonymized (XXX.XXX.XXX.###)
3. Test with different IP formats
4. Verify consistent anonymization

**Expected Result**: IP addresses anonymized correctly

---

### Test Case: Anonymize Database Names
**Objective**: Verify that database names are anonymized

**Steps**:
1. Create pair with database_name
2. Verify database name is anonymized (db_hash)
3. Verify same database name produces same anonymized value
4. Test with anonymization disabled

**Expected Result**: Database names anonymized correctly

---

### Test Case: Anonymization Disabled
**Objective**: Verify that anonymization can be disabled

**Steps**:
1. Create exporter with anonymize_sensitive_data=False
2. Create pair with sensitive data
3. Verify sensitive data is NOT anonymized
4. Verify original values are preserved

**Expected Result**: Anonymization disabled correctly

---

### Test Case: Multiple Sensitive Data Types
**Objective**: Verify that multiple types of sensitive data are anonymized in same query

**Steps**:
1. Create pair with query containing email, phone, SSN, credit card, IP
2. Verify all sensitive data types are anonymized
3. Verify non-sensitive data is preserved

**Expected Result**: All sensitive data types anonymized

---

## Export Formats

### Test Case: Export to JSONL Format
**Objective**: Verify that data can be exported to JSONL format

**Steps**:
1. Create multiple query-SQL pairs
2. Export to JSONL format
3. Verify file is created
4. Verify each line is valid JSON
5. Verify all pairs are exported
6. Verify format is correct (one JSON object per line)

**Expected Result**: JSONL export successful with correct format

---

### Test Case: Export to JSON Format
**Objective**: Verify that data can be exported to JSON format

**Steps**:
1. Create multiple query-SQL pairs
2. Export to JSON format
3. Verify file is created
4. Verify file is valid JSON
5. Verify structure includes exported_at, format_version, total_pairs, pairs, statistics
6. Verify all pairs are in the array

**Expected Result**: JSON export successful with correct structure

---

### Test Case: Export to CSV Format
**Objective**: Verify that data can be exported to CSV format

**Steps**:
1. Create multiple query-SQL pairs
2. Export to CSV format
3. Verify file is created
4. Verify CSV headers are correct
5. Verify all pairs are exported as rows
6. Verify data is properly escaped

**Expected Result**: CSV export successful with correct format

---

### Test Case: Export Format Comparison
**Objective**: Verify that different formats export same data

**Steps**:
1. Create set of query-SQL pairs
2. Export to JSONL format
3. Export to JSON format
4. Export to CSV format
5. Verify all exports contain same number of pairs
6. Verify data is consistent across formats

**Expected Result**: All formats export same data correctly

---

### Test Case: Export with Date Range Filter
**Objective**: Verify that exports can be filtered by date range

**Steps**:
1. Create pairs on different dates
2. Export with start_date and end_date
3. Verify only pairs in date range are exported
4. Verify pairs outside range are excluded

**Expected Result**: Date range filter works correctly

---

### Test Case: Export with Success Filter
**Objective**: Verify that exports can be filtered by success status

**Steps**:
1. Create successful and failed pairs
2. Export with successful_only=true
3. Verify only successful pairs are exported
4. Verify failed pairs are excluded

**Expected Result**: Success filter works correctly

---

## Dataset Statistics

### Test Case: Get Basic Statistics
**Objective**: Verify that basic statistics are calculated correctly

**Steps**:
1. Create multiple query-SQL pairs (some successful, some failed)
2. Get statistics
3. Verify total_pairs count is correct
4. Verify successful_pairs and failed_pairs counts are correct
5. Verify unique_tables includes all tables

**Expected Result**: Basic statistics calculated correctly

---

### Test Case: Statistics Unique Tables
**Objective**: Verify that unique tables are tracked correctly

**Steps**:
1. Create pairs referencing different tables
2. Create pairs referencing same tables multiple times
3. Get statistics
4. Verify unique_tables contains correct unique table names
5. Verify no duplicates

**Expected Result**: Unique tables tracked correctly

---

### Test Case: Statistics Database Types
**Objective**: Verify that database types are tracked correctly

**Steps**:
1. Create pairs with different database types (postgresql, mysql, etc.)
2. Get statistics
3. Verify database_types contains all unique database types
4. Verify correct counts

**Expected Result**: Database types tracked correctly

---

### Test Case: Statistics Average Lengths
**Objective**: Verify that average query and SQL lengths are calculated correctly

**Steps**:
1. Create pairs with queries of different lengths
2. Get statistics
3. Calculate expected averages manually
4. Verify avg_query_length matches expected
5. Verify avg_sql_length matches expected

**Expected Result**: Average lengths calculated correctly

---

### Test Case: Statistics Date Range
**Objective**: Verify that date range is calculated correctly

**Steps**:
1. Create pairs on different dates
2. Get statistics
3. Verify date_range.start is earliest timestamp
4. Verify date_range.end is latest timestamp
5. Verify format is ISO format

**Expected Result**: Date range calculated correctly

---

### Test Case: Statistics Query Type Distribution
**Objective**: Verify that query type distribution is calculated correctly

**Steps**:
1. Create pairs with different query types (SELECT, INSERT, UPDATE, DELETE)
2. Get statistics
3. Verify query_type_distribution contains all query types
4. Verify counts match number of each type
5. Verify distribution is accurate

**Expected Result**: Query type distribution calculated correctly

---

### Test Case: Statistics with Date Filter
**Objective**: Verify that statistics respect date filters

**Steps**:
1. Create pairs on different dates
2. Get statistics with start_date and end_date
3. Verify statistics only include pairs in date range
4. Verify counts are correct for filtered data

**Expected Result**: Statistics filtered correctly by date

---

### Test Case: Statistics Empty Dataset
**Objective**: Verify that statistics handle empty datasets gracefully

**Steps**:
1. Get statistics with no pairs
2. Verify total_pairs is 0
3. Verify all counts are 0
4. Verify no errors occur

**Expected Result**: Empty dataset handled gracefully

---

## Filtering & Pagination

### Test Case: List Pairs with Limit
**Objective**: Verify that pairs can be limited

**Steps**:
1. Create multiple pairs
2. List pairs with limit parameter
3. Verify number of returned pairs matches limit
4. Verify pairs are returned in correct order

**Expected Result**: Limit parameter works correctly

---

### Test Case: List Pairs with Offset
**Objective**: Verify that pairs can be paginated with offset

**Steps**:
1. Create multiple pairs
2. List pairs with offset parameter
3. Verify returned pairs skip first N pairs
4. Verify correct pairs are returned

**Expected Result**: Offset parameter works correctly

---

### Test Case: List Pairs with Limit and Offset
**Objective**: Verify that limit and offset work together

**Steps**:
1. Create multiple pairs
2. List pairs with both limit and offset
3. Verify pagination works correctly
4. Verify correct subset is returned

**Expected Result**: Limit and offset work together correctly

---

### Test Case: Filter by Success Status
**Objective**: Verify that pairs can be filtered by success status

**Steps**:
1. Create successful and failed pairs
2. List pairs with successful_only=true
3. Verify only successful pairs are returned
4. List pairs with successful_only=false (or omitted)
5. Verify all pairs are returned

**Expected Result**: Success filter works correctly

---

### Test Case: Filter by Date Range
**Objective**: Verify that pairs can be filtered by date range

**Steps**:
1. Create pairs on different dates
2. List pairs with start_date and end_date
3. Verify only pairs in date range are returned
4. Test with dates outside range
5. Verify no pairs returned

**Expected Result**: Date range filter works correctly

---

## API Endpoints

### Test Case: POST /api/training-data/pairs
**Objective**: Verify add pair endpoint

**Steps**:
1. POST pair with valid data
2. Verify 201 status code
3. Verify pair is returned
4. Test with missing required fields
5. Verify 400 error

**Expected Result**: Add pair endpoint works correctly

---

### Test Case: GET /api/training-data/pairs
**Objective**: Verify list pairs endpoint

**Steps**:
1. Create multiple pairs
2. GET pairs list
3. Verify 200 status code
4. Verify pairs are returned
5. Test with query parameters (limit, offset, filters)
6. Verify filters work correctly

**Expected Result**: List pairs endpoint works correctly

---

### Test Case: GET /api/training-data/pairs/<pair_id>
**Objective**: Verify get pair endpoint

**Steps**:
1. Create a pair
2. GET pair by ID
3. Verify 200 status code
4. Verify pair data is returned
5. GET non-existent pair
6. Verify 404 error

**Expected Result**: Get pair endpoint works correctly

---

### Test Case: DELETE /api/training-data/pairs/<pair_id>
**Objective**: Verify delete pair endpoint

**Steps**:
1. Create a pair
2. DELETE pair by ID
3. Verify 200 status code
4. Verify pair is deleted
5. DELETE non-existent pair
6. Verify 404 error

**Expected Result**: Delete pair endpoint works correctly

---

### Test Case: GET /api/training-data/statistics
**Objective**: Verify statistics endpoint

**Steps**:
1. Create multiple pairs
2. GET statistics
3. Verify 200 status code
4. Verify statistics are returned
5. Test with date range filters
6. Verify statistics are filtered correctly

**Expected Result**: Statistics endpoint works correctly

---

### Test Case: GET /api/training-data/export
**Objective**: Verify export endpoint

**Steps**:
1. Create multiple pairs
2. GET export with format=jsonl
3. Verify 200 status code
4. Verify file is returned with correct content-type
5. Test with format=json
6. Test with format=csv
7. Test with invalid format
8. Verify 400 error for invalid format

**Expected Result**: Export endpoint works for all formats

---

## Edge Cases and Error Handling

### Test Case: Empty Dataset Export
**Objective**: Verify that exporting empty dataset is handled

**Steps**:
1. Attempt to export with no pairs
2. Verify appropriate response (404 or empty file)
3. Verify no errors occur

**Expected Result**: Empty dataset export handled gracefully

---

### Test Case: Large Dataset Export
**Objective**: Verify that large datasets can be exported

**Steps**:
1. Create large number of pairs (e.g., 1000)
2. Export to JSONL format
3. Verify export completes successfully
4. Verify all pairs are exported
5. Verify performance is acceptable

**Expected Result**: Large datasets exported successfully

---

### Test Case: Invalid Date Formats
**Objective**: Verify that invalid date formats are handled

**Steps**:
1. List pairs with invalid date format
2. Verify appropriate error handling
3. Test with malformed dates
4. Verify error messages are clear

**Expected Result**: Invalid dates handled with errors

---

### Test Case: SQL Without Tables
**Objective**: Verify that SQL queries without tables are handled

**Steps**:
1. Create pair with SQL like "SELECT 1" (no tables)
2. Verify pair is created successfully
3. Verify table_names is empty list
4. Verify statistics handle empty table lists

**Expected Result**: SQL without tables handled correctly

---

### Test Case: Complex SQL Queries
**Objective**: Verify that complex SQL queries are handled

**Steps**:
1. Create pairs with complex SQL (CTEs, subqueries, multiple JOINs)
2. Verify table names are extracted correctly
3. Verify query type is detected correctly
4. Verify export includes all data

**Expected Result**: Complex SQL handled correctly

---

### Test Case: Unicode and Special Characters
**Objective**: Verify that Unicode and special characters are handled

**Steps**:
1. Create pair with Unicode characters in natural language query
2. Create pair with special characters in SQL
3. Export to all formats
4. Verify characters are preserved correctly
5. Verify no encoding errors

**Expected Result**: Unicode and special characters handled correctly

---

### Test Case: Very Long Queries
**Objective**: Verify that very long queries are handled

**Steps**:
1. Create pair with very long natural language query (e.g., 10,000 characters)
2. Create pair with very long SQL query
3. Verify pair is created successfully
4. Verify export includes full queries
5. Verify statistics calculate lengths correctly

**Expected Result**: Very long queries handled correctly

---

### Test Case: Concurrent Operations
**Objective**: Verify that concurrent operations work correctly

**Steps**:
1. Add pairs concurrently (simulated)
2. Get statistics concurrently
3. Export concurrently
4. Verify no data corruption
5. Verify all operations complete successfully

**Expected Result**: Concurrent operations handled correctly

---

## Integration Tests

### Test Case: End-to-End Export Workflow
**Objective**: Verify complete export workflow

**Steps**:
1. Add multiple query-SQL pairs
2. Get statistics
3. List pairs with filters
4. Export to JSONL format
5. Verify exported file is valid
6. Import exported data (if applicable)
7. Verify data integrity

**Expected Result**: Complete workflow executes successfully

---

### Test Case: Automatic Pair Collection Integration
**Objective**: Verify automatic pair collection from query execution

**Steps**:
1. Execute natural language query via API
2. Verify pair is automatically added to training data
3. Verify pair contains correct data
4. Verify anonymization is applied
5. Export pairs
6. Verify exported data is correct

**Expected Result**: Automatic collection works correctly

---

## Performance Tests

### Test Case: Export Performance
**Objective**: Verify that exports perform well with large datasets

**Steps**:
1. Create large number of pairs (e.g., 10,000)
2. Measure time to export to JSONL
3. Measure time to export to JSON
4. Measure time to export to CSV
5. Verify all exports complete within acceptable time

**Expected Result**: Exports perform efficiently

---

### Test Case: Statistics Calculation Performance
**Objective**: Verify that statistics calculation is efficient

**Steps**:
1. Create large number of pairs
2. Measure time to calculate statistics
3. Verify calculation completes within acceptable time
4. Verify statistics are accurate

**Expected Result**: Statistics calculation performs efficiently

---

### Test Case: Anonymization Performance
**Objective**: Verify that anonymization doesn't significantly slow down operations

**Steps**:
1. Create pairs with queries containing multiple sensitive data patterns
2. Measure time to add pairs
3. Compare with anonymization disabled
4. Verify performance impact is acceptable

**Expected Result**: Anonymization has minimal performance impact


