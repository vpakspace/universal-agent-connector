# Self-Healing Query System

A self-healing query system that uses MCP sampling to recover from SQL errors by asking the host LLM for corrections when schema changes cause query failures.

## Overview

When SQL queries fail due to schema changes (e.g., column renamed, table structure modified), the system:
1. **Detects the error** (ColumnNotFoundError, TableNotFoundError)
2. **Finds semantic alternatives** from ontology
3. **Asks LLM for help** via MCP sampling
4. **Retries with corrected query**
5. **Learns the mapping** for future use

## Files

1. **`self_healing_mcp_tools.py`**: Main MCP server with `query_with_healing` tool
2. **`ontology_matcher.py`**: Finds semantically similar column names
3. **`column_ontology.json`**: Maps concepts to column name lists
4. **`mock_sql_executor.py`**: Mock SQL executor for testing
5. **`test_self_healing.py`**: Test script demonstrating healing flow
6. **`learned_mappings.json`**: Auto-generated file storing learned mappings

## Quick Start

### 1. Basic Usage

```python
from self_healing_mcp_tools import query_with_healing

# Query with a column that might not exist
result = await query_with_healing(
    table="customers",
    column="tax_id",  # This might not exist, but "vat_number" does
    filter="id = 1"
)

if result["success"]:
    print("Query succeeded:", result["result"])
    if result["healing_applied"]:
        print("Healing was applied:", result["healing_history"])
else:
    print("Query failed:", result["error"])
```

### 2. Run Test Script

```bash
python test_self_healing.py
```

This will demonstrate:
- Query fails with "tax_id" column
- System finds alternatives: ["vat_number", "ein", "gst_id"]
- System asks LLM via sampling
- LLM suggests "vat_number"
- Query succeeds with corrected column
- Mapping saved to `learned_mappings.json`

## Components

### Self-Healing Tool (`self_healing_mcp_tools.py`)

The `query_with_healing` tool:
- Executes SQL query
- Catches ColumnNotFoundError
- Finds semantic alternatives
- Uses MCP sampling to ask LLM for correction
- Retries with corrected query (max 2 retries)
- Saves successful mappings

**Tool Signature:**
```python
@mcp.tool()
async def query_with_healing(
    table: str,
    column: str,
    filter: Optional[str] = None
) -> Dict[str, Any]
```

**Response Format:**
```python
{
    "success": bool,
    "query": str,  # Final query (may be modified)
    "result": List[Dict],  # Query results
    "attempt": int,  # Number of attempts
    "healing_applied": bool,
    "healing_history": [
        {
            "failed_column": str,
            "alternatives": List[str],
            "suggested_column": str,
            "llm_response": str
        }
    ]
}
```

### Ontology Matcher (`ontology_matcher.py`)

Finds semantically similar column names:

```python
from ontology_matcher import find_semantic_alternatives

alternatives = find_semantic_alternatives("tax_id", "customers")
# Returns: ["vat_number", "ein", "gst_id", "tax_number"]
```

**Features:**
- Checks learned mappings first (highest priority)
- Searches ontology for concepts containing the column
- Returns all alternatives from matching concepts
- Handles fuzzy matching for similar words

### Column Ontology (`column_ontology.json`)

Maps concepts to column name lists:

```json
{
  "tax_identifier": ["tax_id", "vat_number", "ein", "gst_id"],
  "customer_name": ["name", "full_name", "customer_name"],
  "email": ["email", "email_address", "contact_email"]
}
```

### MCP Sampling

Uses MCP's sampling protocol to ask the host LLM:

```python
response = await request_sampling(
    prompt="A SQL query failed...",
    system_prompt="You are a database schema expert."
)
```

**Note**: The actual MCP sampling implementation depends on FastMCP's API. The code includes:
- Attempts to use `mcp.sample()` if available
- Attempts to use `mcp.request_sampling()` if available
- Fallback mock implementation for testing

### Mock SQL Executor (`mock_sql_executor.py`)

Simulates SQL execution with configurable failures:

```python
from mock_sql_executor import MockSQLExecutor

executor = MockSQLExecutor()

# Configure a column to fail
executor.set_failing_column("customers", "tax_id")

# Execute query
try:
    result = executor.execute("SELECT tax_id FROM customers")
except ColumnNotFoundError as e:
    print(f"Column not found: {e}")
```

## Healing Flow

### Example: Query Fails with "tax_id"

1. **Initial Query**: `SELECT tax_id FROM customers`
2. **Error**: `ColumnNotFoundError: Column 'tax_id' not found`
3. **Find Alternatives**: `["vat_number", "ein", "gst_id", "tax_number"]`
4. **Build Prompt**:
   ```
   A SQL query failed because column 'tax_id' does not exist in table 'customers'.
   Available alternatives: vat_number, ein, gst_id, tax_number
   Suggest the most likely correct column name.
   ```
5. **LLM Response** (via MCP sampling): `"vat_number"`
6. **Rebuild Query**: `SELECT vat_number FROM customers`
7. **Retry**: Query succeeds
8. **Learn**: Save mapping `tax_id → vat_number` for table `customers`

### Healing Prompt Builder

The `build_healing_prompt()` function creates a clear prompt:

```
A SQL query failed because column 'tax_id' does not exist in table 'customers'.

Error: Column 'tax_id' not found in table 'customers'. Available columns: id, vat_number, name, email...

Available alternative column names (based on semantic similarity): vat_number, ein, gst_id

Based on the error and the available alternatives, suggest the MOST LIKELY correct column name to use instead of 'tax_id'.

Respond with ONLY the column name (no quotes, no explanation, just the column name).
```

## Error Scenarios

### Handled (Will Attempt Healing)
- ✅ **ColumnNotFoundError**: Finds alternatives, asks LLM, retries
- ✅ **TableNotFoundError**: Returns error (no healing attempted)

### Not Handled (Fail Immediately)
- ❌ **TypeMismatchError**: Returns error (type issues can't be healed by renaming)
- ❌ **Permission Denied**: Returns error (security issue, not schema issue)
- ❌ **Syntax Errors**: Returns error (query structure issue)

## Learning Component

### Learned Mappings

After successful healing, mappings are saved to `learned_mappings.json`:

```json
{
  "customers": {
    "tax_id": "vat_number",
    "customer_name": "name"
  },
  "orders": {
    "order_total": "total_amount"
  }
}
```

### Mapping Priority

1. **Learned mappings** (highest priority - checked first)
2. **Ontology matches** (semantic similarity)
3. **Fuzzy matching** (word-based similarity)

### Adding Mappings Manually

You can manually add mappings to `column_ontology.json`:

```json
{
  "new_concept": ["column1", "column2", "column3"]
}
```

## MCP Sampling Implementation

### FastMCP Integration

The code attempts multiple methods for MCP sampling:

```python
# Method 1: mcp.sample() (if available)
response = await mcp.sample(
    messages=[{"role": "user", "content": prompt}],
    system_prompt="You are a database schema expert.",
    max_tokens=100
)

# Method 2: mcp.request_sampling() (if available)
response = await mcp.request_sampling({
    "messages": [{"role": "user", "content": prompt}],
    "systemPrompt": "You are a database schema expert.",
    "maxTokens": 100
})
```

### Fallback Implementation

For testing without MCP sampling, a mock implementation is provided that:
- Extracts alternatives from the prompt
- Returns the first alternative as suggestion
- This is NOT used in production (real MCP sampling should be implemented)

## Testing

### Run Test Script

```bash
python test_self_healing.py
```

### Expected Output

```
======================================================================
SELF-HEALING QUERY SYSTEM TEST
======================================================================

Step 1: Configuring test scenario
----------------------------------------------------------------------
Table: customers
Available columns: ['address', 'created_at', 'email', 'id', 'name', 'phone', 'updated_at', 'vat_number']
Query will attempt to use: tax_id (does not exist)
Expected alternative: vat_number (exists and is semantically similar)

Step 2: Executing query with non-existent column 'tax_id'
----------------------------------------------------------------------
Query: SELECT tax_id FROM customers

Step 3: Healing Results
----------------------------------------------------------------------
Success: True
Attempts: 2
Healing Applied: True

✓ Query succeeded after healing!

Healing History:
  Attempt 1:
    Failed column: tax_id
    Alternatives found: ['vat_number', 'ein', 'gst_id', 'tax_number']
    LLM suggested: vat_number

Final Query: SELECT vat_number FROM customers

Results:
  {'id': 1, 'vat_number': 'VAT123'}
  {'id': 2, 'vat_number': 'VAT456'}

Step 4: Checking Learned Mappings
----------------------------------------------------------------------
✓ Learned mapping saved: tax_id → vat_number
```

## Configuration

### Max Retries

Default: 2 retries. To change:

```python
# In self_healing_mcp_tools.py, modify:
max_retries = 2  # Change to desired number
```

### Ontology File

Edit `column_ontology.json` to add/modify concept mappings:

```json
{
  "your_concept": ["column1", "column2", "column3"]
}
```

### SQL Executor

Replace `MockSQLExecutor` with your actual SQL executor:

```python
from self_healing_mcp_tools import sql_executor
from your_module import YourSQLExecutor

sql_executor = YourSQLExecutor()
```

## Integration with Existing Systems

### Using Real Database

Replace the mock executor:

```python
from your_database_module import DatabaseConnector

class RealSQLExecutor:
    def execute(self, query: str):
        connector = DatabaseConnector()
        return connector.execute_query(query, as_dict=True)
```

### Using Existing Ontology

If you have an existing ontology system, integrate it:

```python
from ontology_matcher import find_semantic_alternatives

# Modify to use your ontology
def find_semantic_alternatives(failed_column: str, table: str):
    # Use your ontology system
    return your_ontology.find_alternatives(failed_column, table)
```

## Limitations

1. **MCP Sampling**: Actual implementation depends on FastMCP's sampling API
2. **SQL Parsing**: Simple regex-based parsing (may not handle all SQL dialects)
3. **Error Detection**: Only handles specific error types
4. **Learning**: Simple file-based storage (consider database for production)

## Future Enhancements

1. **Table Healing**: Handle table name changes
2. **Query Rewriting**: More sophisticated SQL query modification
3. **Confidence Scores**: Score LLM suggestions by confidence
4. **Multi-Column Healing**: Handle multiple failed columns in one query
5. **Schema Caching**: Cache table schemas for faster lookups
6. **Versioned Mappings**: Track mapping versions over time

## Troubleshooting

### "No semantic alternatives found"
- Add the column concept to `column_ontology.json`
- Check that the concept contains the failed column

### "MCP sampling failed"
- Ensure FastMCP supports sampling
- Check MCP server configuration
- Verify LLM is accessible

### "Max retries exceeded"
- Check that alternatives actually exist in the table
- Verify LLM is suggesting valid column names
- Review healing history for patterns

## License

This implementation is part of the AI Agent Connector project.

