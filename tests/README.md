# Testing DatabaseConnector

This directory contains tests for the `DatabaseConnector` class.

## Test Files

- **`test_db_connector.py`** - Unit tests with mocks (no database required)
- **`test_db_connector_integration.py`** - Integration tests (requires PostgreSQL)
- **`manual_test.py`** - Manual testing script for quick verification

## Running Tests

### Unit Tests (No Database Required)

Run all unit tests with mocks:
```bash
pytest tests/test_db_connector.py
```

Run with verbose output:
```bash
pytest tests/test_db_connector.py -v
```

### Integration Tests (Requires Database)

1. Set up environment variables:
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=cloudbadal
export DB_PASSWORD=Home1234@
export DB_NAME=test_db
```

2. Run integration tests:
```bash
pytest tests/test_db_connector_integration.py -m integration
```

3. Skip integration tests:
```bash
pytest -m "not integration"
```

### Run All Tests

```bash
# Unit tests only
pytest tests/test_db_connector.py

# All tests (including integration if DB available)
pytest

# Exclude integration tests
pytest -m "not integration"
```

### Manual Testing

Run the manual test script:
```bash
python tests/manual_test.py
```

This script will:
- Test basic connection
- Test query execution
- Test context manager
- Test table creation and data operations

## Test Coverage

The unit tests cover:
- ✅ Initialization with env vars, parameters, and connection strings
- ✅ Connection and disconnection
- ✅ Query execution (SELECT, INSERT, UPDATE, DELETE)
- ✅ Dictionary results
- ✅ Error handling and rollback
- ✅ Bulk operations (execute_many)
- ✅ Context manager usage
- ✅ Connection status checking

## Requirements

- `pytest` - Test framework
- `pytest-mock` - For mocking (installed automatically)
- `psycopg2-binary` - PostgreSQL adapter (for integration tests)

## Troubleshooting

### Import Errors
Make sure you're in the virtual environment:
```bash
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/Mac
```

### Database Connection Errors
Integration tests require a running PostgreSQL database. If you don't have one:
- Use only unit tests: `pytest tests/test_db_connector.py`
- Or set up a test database using Docker:
  ```bash
  docker run --name test-postgres -e POSTGRES_PASSWORD=testpass -e POSTGRES_DB=testdb -p 5432:5432 -d postgres
  ```









