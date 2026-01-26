# MCP Governance Interceptor

A comprehensive governance middleware system for MCP (Model Context Protocol) servers that wraps all tool executions with security policies, PII masking, and audit logging.

## Overview

The Governance Interceptor provides:
- **Policy Validation**: Rate limits, RLS (Row Level Security), complexity checks, PII access permissions
- **PII Masking**: Automatic detection and masking of sensitive data (emails, phones, SSNs, credit cards)
- **Audit Logging**: Complete audit trail of all tool executions with JSONL format
- **Security Enforcement**: Blocks unauthorized access attempts with clear error messages and remediation suggestions
- **Performance**: Designed to complete validation in < 100ms

## Files

1. **`mcp_governance_middleware.py`**: Core middleware with `@governed_mcp_tool` decorator
2. **`policy_engine.py`**: Policy validation engine with async support
3. **`pii_masker.py`**: PII detection and masking system
4. **`mock_audit_logger.py`**: Audit logger that writes to JSONL file
5. **`example_governed_tool.py`**: Example tool demonstrating usage
6. **`test_governance_middleware.py`**: Comprehensive test suite
7. **`benchmark_governance.py`**: Performance benchmark script

## Quick Start

### 1. Basic Usage

```python
from fastmcp import FastMCP
from mcp_governance_middleware import governed_mcp_tool

mcp = FastMCP("My Server")

@governed_mcp_tool(mcp.tool(), requires_pii=True, sensitivity_level="standard")
async def query_customer_data(customer_id: str, user_id: str, tenant_id: str):
    """Query customer data - automatically governed"""
    # Your tool logic here
    return {
        "customer_id": customer_id,
        "email": "customer@example.com",  # Will be masked
        "phone": "555-123-4567"  # Will be masked
    }
```

### 2. Configuration

Before use, configure permissions:

```python
from policy_engine import policy_engine

# Grant tenant access
policy_engine.grant_tenant_access("user1", "tenant1")

# Grant PII permission
policy_engine.grant_pii_permission("user1")
```

## Components

### Policy Engine (`policy_engine.py`)

Validates tool execution requests against four policies:

1. **Rate Limiting**: Max 100 calls/hour per user (configurable)
2. **RLS (Row Level Security)**: User can only access authorized tenants
3. **Complexity Check**: Query complexity score < 100 (prevents resource exhaustion)
4. **PII Access**: User must have PII_READ permission to access sensitive data

**Usage:**
```python
from policy_engine import policy_engine

# Async validation
validation_result = await policy_engine.validate(
    user_id="user1",
    tenant_id="tenant1",
    tool_name="query_customer",
    arguments={"customer_id": "123"}
)

if not validation_result.is_allowed:
    print(f"Blocked: {validation_result.reason}")
    print(f"Suggestions: {validation_result.suggestions}")
```

**ValidationResult:**
- `is_allowed`: bool - Whether request is allowed
- `reason`: str - Reason for allow/deny
- `suggestions`: List[str] - Remediation suggestions
- `failed_policy`: Optional[str] - Which policy failed
- `metadata`: Dict - Additional metadata

### PII Masker (`pii_masker.py`)

Automatically detects and masks sensitive data:

- **Emails**: `user@example.com` → `***@***.com`
- **Phone Numbers** (standard): `(555) 123-4567` → `(***) ***-4567` (keeps last 4)
- **Phone Numbers** (strict): `(555) 123-4567` → `(***) ***-****` (full mask)
- **SSN** (standard): `123-45-6789` → `***-**-6789` (keeps last 4)
- **Credit Cards**: `1234-5678-9012-3456` → `****-****-****-3456` (keeps last 4)

**Usage:**
```python
from pii_masker import mask_sensitive_fields

data = {
    "email": "user@example.com",
    "phone": "(555) 123-4567"
}

masked = mask_sensitive_fields(data, sensitivity_level="standard")
# Result: {"email": "***@***.com", "phone": "(***) ***-4567"}
```

### Audit Logger (`mock_audit_logger.py`)

Logs all tool executions to `audit_log.jsonl` (JSON Lines format):

**Log Entry Structure:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "user_id": "user1",
  "tenant_id": "tenant1",
  "tool_name": "query_customer_data",
  "arguments": {"customer_id": "123"},
  "result": {...},
  "validation": {...},
  "execution_time_ms": 45.2,
  "error": null,
  "status": "success"
}
```

**Usage:**
```python
from mock_audit_logger import AuditLogger

logger = AuditLogger("audit_log.jsonl")
logs = logger.read_logs(limit=100)
```

## Governance Middleware

### `@governed_mcp_tool` Decorator

Wraps MCP tools with governance:

```python
@governed_mcp_tool(mcp.tool(), requires_pii=True, sensitivity_level="standard")
async def my_tool(...):
    ...
```

**Parameters:**
- `mcp_tool_decorator`: MCP tool decorator from FastMCP (optional)
- `requires_pii`: Whether tool requires PII_READ permission (default: False)
- `sensitivity_level`: PII masking level - "standard" or "strict" (default: "standard")

**What it does:**
1. Extracts `user_id` and `tenant_id` from execution context
2. Validates against all policies BEFORE execution
3. Logs the attempt to audit log
4. Executes tool only if validation passes
5. Applies PII masking to results
6. Logs the result

### Execution Context Extraction

The middleware automatically extracts `user_id` and `tenant_id` from:
1. Function keyword arguments (`user_id=..., tenant_id=...`)
2. First positional argument if it's a dict
3. MCP request metadata (if available)
4. Defaults to `user_id="default_user"` if not found

## Error Handling

### MCPSecurityError

When policy validation fails, a `MCPSecurityError` is raised:

```python
from mcp_governance_middleware import MCPSecurityError

try:
    result = await query_customer_data(...)
except MCPSecurityError as e:
    print(f"Blocked: {e.message}")
    print(f"Policy: {e.failed_policy}")
    print(f"Suggestions: {e.suggestions}")
```

**Error Attributes:**
- `message`: Error message
- `validation_result`: ValidationResult object
- `failed_policy`: Which policy failed (rate_limit, rls, complexity, pii_access)
- `suggestions`: List of remediation suggestions

## Testing

### Run Tests

```bash
# Run all tests
pytest test_governance_middleware.py -v

# Run specific test class
pytest test_governance_middleware.py::TestBlockedCall -v

# Run with coverage
pytest test_governance_middleware.py --cov=mcp_governance_middleware --cov-report=html
```

### Test Coverage

Tests cover:
- ✅ Blocked calls (rate limit, RLS, PII permission)
- ✅ Successful calls with masking
- ✅ Audit logging
- ✅ Context extraction
- ✅ PII masking (various formats)
- ✅ Error handling and suggestions

## Performance Benchmarking

### Run Benchmarks

```bash
python benchmark_governance.py
```

### Performance Targets

- **Validation**: < 100ms (mean, p95, p99)
- **Masking**: < 100ms for 100 records
- **Full Execution**: < 100ms (validation + masking + execution)

Benchmark results show:
- Mean execution time
- Median, min, max
- Standard deviation
- 95th and 99th percentiles

## Configuration

### Policy Engine Configuration

```python
from policy_engine import PolicyEngine

# Create custom policy engine
engine = PolicyEngine(
    max_calls_per_hour=200,  # Increase rate limit
    max_complexity_score=150  # Increase complexity limit
)
```

### Grant Permissions

```python
from policy_engine import policy_engine

# Grant tenant access
policy_engine.grant_tenant_access("user1", "tenant1")
policy_engine.grant_tenant_access("user1", "tenant2")

# Grant PII permission
policy_engine.grant_pii_permission("user1")

# Revoke permissions
policy_engine.revoke_tenant_access("user1", "tenant2")
policy_engine.revoke_pii_permission("user1")
```

## Integration with Existing Systems

### Using Existing AuditLogger

If you have an existing `AuditLogger` (from `ai_agent_connector.app.utils.audit_logger`):

```python
# In mcp_governance_middleware.py, you can replace:
from mock_audit_logger import AuditLogger

# With:
try:
    from ai_agent_connector.app.utils.audit_logger import AuditLogger
except ImportError:
    from mock_audit_logger import AuditLogger
```

### Using Existing Column Masker

If you have existing masking (from `ai_agent_connector.app.utils.column_masking`):

```python
# You can integrate with ColumnMasker for table-level masking
from ai_agent_connector.app.utils.column_masking import ColumnMasker

# Use alongside pii_masker for comprehensive masking
```

## Example: Complete Tool

```python
from fastmcp import FastMCP
from mcp_governance_middleware import governed_mcp_tool, MCPSecurityError

mcp = FastMCP("Customer Service")

@governed_mcp_tool(mcp.tool(), requires_pii=True, sensitivity_level="standard")
async def get_customer_profile(
    customer_id: str,
    user_id: str,
    tenant_id: str
) -> dict:
    """
    Get customer profile with governance.
    
    This tool automatically:
    - Validates user has access to tenant
    - Checks PII permissions
    - Masks sensitive data in results
    - Logs to audit trail
    """
    # Your business logic here
    customer_data = {
        "customer_id": customer_id,
        "name": "John Doe",
        "email": "john@example.com",  # Will be masked to ***@***.com
        "phone": "555-123-4567",  # Will be masked to (***) ***-4567
        "ssn": "123-45-6789"  # Will be masked to ***-**-6789
    }
    
    return customer_data
```

## Security Features

### Rate Limiting
- Tracks calls per user per hour
- Configurable limit (default: 100/hour)
- Automatic cleanup of old timestamps

### Row Level Security (RLS)
- Tenant-based access control
- User can only access authorized tenants
- Clear error messages with remediation

### Complexity Checks
- Prevents resource exhaustion
- Scores queries based on:
  - Query length
  - Number of arguments
  - Nested structure depth
- Configurable maximum score (default: 100)

### PII Access Control
- Requires PII_READ permission for sensitive tools
- Automatic detection of PII-accessing tools
- Permission-based enforcement

### PII Masking
- Automatic detection of sensitive data
- Two masking levels: standard (partial) and strict (full)
- Recursive masking for nested structures
- Preserves data structure

### Audit Logging
- Complete audit trail
- JSONL format (one JSON per line)
- Includes: user, tenant, tool, args, result, validation, timing
- Security violations logged with error status

## Troubleshooting

### "Rate limit exceeded"
- Wait for the rate limit window to expire
- Request higher rate limit from administrator
- Check: `policy_engine.max_calls_per_hour`

### "RLS check failed"
- Request access to the tenant
- Check: `policy_engine.grant_tenant_access(user_id, tenant_id)`

### "PII access check failed"
- Request PII_READ permission
- Check: `policy_engine.grant_pii_permission(user_id)`

### "Complexity check failed"
- Simplify the query
- Reduce number of arguments
- Split into multiple simpler queries

### Performance Issues
- Run benchmark: `python benchmark_governance.py`
- Check cache: Validation results are cached for 5 minutes
- Monitor: Check audit logs for execution times

## Best Practices

1. **Always use `@governed_mcp_tool`** for tools that access data
2. **Set `requires_pii=True`** for tools that access sensitive data
3. **Use appropriate `sensitivity_level`** based on data sensitivity
4. **Grant permissions** before tool execution
5. **Monitor audit logs** for security violations
6. **Run benchmarks** regularly to ensure performance
7. **Handle MCPSecurityError** with user-friendly messages

## License

This implementation is part of the AI Agent Connector project.

