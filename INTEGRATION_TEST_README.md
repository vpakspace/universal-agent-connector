# Production-Ready Integration Test

## Overview

This integration test demonstrates all MCP system components working together in a complex, production-ready scenario. It validates that the Semantic Router, Governance Middleware, Self-Healing, PII Masking, and Audit Logging all function correctly as an integrated system.

## Test Scenario

**Complex Multi-Story Scenario:**
```
"I need to analyze customer revenue for Q4 2024. I am user_alice in the US region. 
Make sure any customer names are masked. Log this request for audit purposes. 
If any column names are wrong, try to fix them automatically."
```

## What Happens Behind the Scenes

### 1. Semantic Router (US-082) ✅
- Filters tools to Revenue concept only
- Reduces context bloat by showing only relevant tools
- Matches natural language query to business concept

### 2. Row-Level Security (US-021) ✅
- Checks `user_alice`'s region permissions
- Validates access to US region data
- Enforces tenant isolation

### 3. PII Masking (US-022) ✅
- Replaces customer names with `***MASKED***`
- Protects sensitive personal information
- Applies configurable sensitivity levels

### 4. Audit Logging (US-005) ✅
- Writes all tool calls to `audit_log.jsonl`
- Records user, tenant, tool, arguments, and results
- Provides complete audit trail

### 5. Self-Healing (US-084) ✅
- Detects column name errors (`total_spend` → `revenue`)
- Uses MCP sampling to ask LLM for correction
- Retries query with corrected column name
- Learns mappings for future use

## Expected Results

**The user sees:**
- Clean, accurate results
- No errors
- No delays
- No security leaks

**The system enforces:**
- Every security policy
- Every audit requirement
- Every governance rule

## Running the Test

### Prerequisites

```bash
# Install dependencies
pip install fastmcp pytest asyncio

# Ensure all required files exist:
# - mcp_semantic_router.py
# - mcp_governance_middleware.py
# - policy_engine.py
# - pii_masker.py
# - self_healing_mcp_tools.py
# - ontology_matcher.py
# - mock_sql_executor.py
# - business_ontology.json
# - column_ontology.json
```

### Run the Integration Test

```bash
# Run the full integration test
python test_integrated_mcp_system.py
```

### Expected Output

```
================================================================================
PRODUCTION-READY INTEGRATION TEST
================================================================================

📋 Test Scenario:
   Query: 'I need to analyze customer revenue for Q4 2024'
   User: user_alice
   Region: US
   Requirements:
     - Mask customer names (PII)
     - Log for audit purposes
     - Fix column name errors automatically (self-healing)

🔍 Step 1: Semantic Router - Filtering to Revenue tools...
   ✓ Matched concept: Revenue
   ✓ Filtered tools: 10 Revenue tools
   ✓ Sample tools: ['query_sales', 'aggregate_revenue', 'get_revenue_by_period']

🛡️  Step 2: Governance Middleware - Applying security policies...
   - Extracting user_id and tenant_id from context
   - Validating RLS (user_alice can access US region)
   - Checking PII permissions
   - Logging to audit trail

   ✓ Policy validation passed
   ✓ RLS check passed (user_alice has US region access)
   ✓ PII permission check passed

🔧 Step 3: Self-Healing - Correcting column name errors...
   ✓ Column name corrected: total_spend → revenue
   ✓ Query retried successfully

🔒 Step 4: PII Masking - Masking sensitive customer data...
   ✓ Customer names masked: '***MASKED***'
   ✓ PII fields protected

📊 Step 5: Results - Clean, accurate data returned...
   ✓ Total Revenue: $155,000.00
   ✓ Customer Count: 3
   ✓ Period: Q4 2024
   ✓ Region: US

📝 Step 6: Audit Logging - Verifying audit trail...
   ✓ Audit log entry created
   ✓ User: user_alice
   ✓ Tenant: US-082
   ✓ Tool: analyze_customer_revenue
   ✓ Timestamp: 2024-01-15T10:30:00
   ✓ Status: success

================================================================================
✅ INTEGRATION TEST PASSED
================================================================================

All components working together:
  ✅ Semantic Router: Filtered to Revenue tools
  ✅ Row-Level Security: Validated user_alice's US region access
  ✅ PII Masking: Customer names masked
  ✅ Audit Logging: Request logged to audit_log.jsonl
  ✅ Self-Healing: Column name corrected (total_spend → revenue)

The user sees: Clean, accurate results. No errors, no delays, no security leaks.
The system enforces: Every security policy. Every audit requirement. Every governance rule.
```

## Test Components

### 1. Component Verification Tests

The test first verifies each component individually:

- **Semantic Router**: Concept resolution and tool filtering
- **Policy Engine**: RLS validation
- **PII Masking**: Customer name masking
- **Self-Healing**: Column name correction
- **Audit Logging**: Log entry creation

### 2. Full Integration Test

The main test runs the complete scenario:

1. **Semantic Router** filters to Revenue tools
2. **Governance Middleware** validates policies
3. **Self-Healing** corrects column name errors
4. **PII Masking** masks sensitive data
5. **Audit Logging** records the request
6. **Results** are returned clean and accurate

## Test Configuration

### User Setup

```python
# Configure policy engine for user_alice
policy_engine._user_tenants["user_alice"] = ["US", "US-082"]  # US region access
policy_engine._pii_permissions["user_alice"] = True  # Has PII_READ permission
```

### SQL Executor Setup

```python
# Configure failing column for self-healing test
sql_executor.set_failing_column("sales_data", "total_spend")  # Will fail, should heal to "revenue"
sql_executor.add_column_to_schema("sales_data", "revenue")  # Correct column exists
sql_executor.add_column_to_schema("sales_data", "customer_name")  # For PII masking test
```

### Mock Data

```python
sql_executor.mock_data["sales_data"] = [
    {
        "id": 1,
        "customer_name": "Alice Johnson",
        "revenue": 50000.00,
        "quarter": 4,
        "year": 2024,
        "region": "US"
    },
    # ... more records
]
```

## Verification Checklist

After running the test, verify:

- [ ] Semantic Router matched "Revenue" concept
- [ ] Policy validation passed (RLS check)
- [ ] PII permission check passed
- [ ] Self-healing corrected column name
- [ ] Customer names are masked in results
- [ ] Audit log entry created in `audit_log.jsonl`
- [ ] Results contain correct revenue data
- [ ] No errors or exceptions occurred

## Troubleshooting

### Issue: "Concept not matched"

**Solution**: Check that `business_ontology.json` contains "Revenue" concept with appropriate keywords.

### Issue: "RLS validation failed"

**Solution**: Ensure `policy_engine._user_tenants["user_alice"]` includes the test tenant ID.

### Issue: "Self-healing didn't trigger"

**Solution**: Verify that `sql_executor.set_failing_column()` is called before the test, and that `column_ontology.json` contains the mapping.

### Issue: "PII not masked"

**Solution**: Check that `mask_sensitive_fields()` is called with the correct sensitivity level, and that customer names are in the data.

### Issue: "Audit log not created"

**Solution**: Verify that `audit_logger.clear_logs()` is called before the test, and that the log file is writable.

## Performance Expectations

- **Semantic Router**: < 10ms (concept resolution)
- **Policy Validation**: < 100ms (cached results)
- **Self-Healing**: < 500ms (including LLM sampling)
- **PII Masking**: < 50ms (for typical data sizes)
- **Audit Logging**: < 10ms (file write)

**Total Expected Time**: < 1 second for complete flow

## Integration with Cursor AI

This test is designed to be run with Cursor AI as the test agent. The scenario demonstrates:

1. **Natural Language Understanding**: Query parsed and routed correctly
2. **Security Enforcement**: All policies applied automatically
3. **Error Recovery**: Self-healing fixes schema issues
4. **Data Protection**: PII automatically masked
5. **Audit Compliance**: Complete audit trail maintained

## Next Steps

After running this test successfully:

1. **Extend Test Scenarios**: Add more complex multi-concept queries
2. **Performance Testing**: Run load tests with multiple concurrent requests
3. **Security Testing**: Test policy violations and edge cases
4. **Production Deployment**: Deploy to production environment
5. **Monitoring**: Set up monitoring for all components

## Related Documentation

- [Semantic Router README](MCP_SEMANTIC_ROUTER_README.md)
- [Governance Interceptor README](GOVERNANCE_INTERCEPTOR_README.md)
- [Self-Healing Query README](SELF_HEALING_QUERY_README.md)
- [Multi-Tenant MCP README](MULTI_TENANT_MCP_README.md)
- [NL Resource Resolver README](NL_RESOURCE_RESOLVER_README.md)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review component-specific READMEs
3. Check audit logs for detailed error information
4. Review test output for specific failure points

