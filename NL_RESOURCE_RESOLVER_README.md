# Natural Language to MCP Resource URI Resolver

A natural language processing system that maps natural language queries to MCP resource URIs and tools using concept extraction and ontology-based mapping.

## Overview

The NL Resource Resolver enables agents to use natural language queries like "Show me customer data" instead of technical URIs like "mcp://tenant/db/customers". It:

- **Extracts Business Concepts**: Uses keyword matching to identify business concepts (Customer, Revenue, Inventory, etc.)
- **Maps to Resources**: Resolves concepts to actual MCP resource URIs
- **Suggests Tools**: Recommends relevant tools for the query
- **Provides Confidence Scores**: Indicates how well the query matched

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Natural Language Query                          │
│         "Show me customer purchase history"                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            Concept Extractor                                 │
│  - Keyword matching with weighted scoring                    │
│  - Returns: [("Customer", 0.95), ("Transaction", 0.85)]    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            Resource Mapper                                   │
│  - Maps concepts to resource URIs                            │
│  - Resolves {{tenant}} templates                             │
│  - Suggests relevant tools                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         ResolutionResult                                     │
│  - matched_concepts: ["Customer", "Transaction"]            │
│  - resource_uris: ["mcp://tenant/postgres/customers", ...]  │
│  - suggested_tools: ["query_customer_orders", ...]          │
│  - confidence_score: 0.87                                    │
└─────────────────────────────────────────────────────────────┘
```

## Files

1. **`nl_resource_resolver.py`**: Main resolver with FastMCP tool integration
2. **`concept_extractor.py`**: Concept extraction using keyword matching
3. **`resource_mapper.json`**: Maps concepts to resources and tools
4. **`tests/test_nl_resource_resolver.py`**: Comprehensive test suite
5. **`benchmark_nl_resolver.py`**: Accuracy benchmark script

## Quick Start

### 1. Basic Usage

```python
from nl_resource_resolver import resolve_query

# Resolve a natural language query
result = resolve_query(
    "Show me customer purchase history for last quarter",
    tenant_id="tenant_001"
)

# Access results
print(f"Matched concepts: {result.matched_concepts}")
print(f"Resource URIs: {result.resource_uris}")
print(f"Suggested tools: {result.suggested_tools}")
print(f"Confidence: {result.confidence_score}")
print(f"Explanation: {result.explanation}")
```

### 2. Using FastMCP Tool

```python
from nl_resource_resolver import mcp, resolve_semantic_query

# Use as FastMCP tool
result_dict = resolve_semantic_query(
    nl_query="What was our revenue last quarter?",
    tenant_id="tenant_001",
    available_tools=["query_sales", "aggregate_revenue"]
)

print(result_dict)
```

### 3. Concept Extraction Only

```python
from concept_extractor import extract_concepts, extract_primary_concept

# Extract all concepts with scores
concepts = extract_concepts("Show me customer data and revenue")
# Returns: [("Customer", 0.95), ("Revenue", 0.80)]

# Extract primary concept
primary, score = extract_primary_concept("Show me customer data")
# Returns: ("Customer", 0.95)
```

## Example Queries

### Customer Queries

```python
result = resolve_query("Show me customer data", "tenant_001")
# Matched: ["Customer"]
# Resources: ["mcp://tenant_001/postgres/customers", ...]
# Tools: ["get_customer_list", "search_customers", ...]

result = resolve_query("Customer purchase history", "tenant_001")
# Matched: ["Customer", "Transaction"]
# Resources: [customer resources + transaction resources]
# Tools: ["query_customer_orders", "aggregate_purchases", ...]
```

### Revenue Queries

```python
result = resolve_query("What was our revenue last quarter?", "tenant_001")
# Matched: ["Revenue"]
# Resources: ["mcp://tenant_001/postgres/sales_data", ...]
# Tools: ["aggregate_revenue", "get_revenue_by_period", ...]
```

### Multi-Concept Queries

```python
result = resolve_query(
    "Show me customer purchase history for last quarter",
    "tenant_001"
)
# Matched: ["Customer", "Transaction"]
# Resources: Combined customer and transaction resources
# Tools: ["query_customer_orders", "filter_by_date_range", ...]
```

## Configuration

### Resource Mapper

The `resource_mapper.json` file maps concepts to resources and tools:

```json
{
  "Customer": {
    "resources": [
      "mcp://{{tenant}}/postgres/customers",
      "mcp://{{tenant}}/postgres/customer_profiles"
    ],
    "tools": [
      "get_customer_list",
      "search_customers",
      "customer_segmentation"
    ],
    "requires": ["READ_CUSTOMER_DATA"]
  }
}
```

### Concept Keywords

Keywords are defined in `concept_extractor.py`:

```python
CONCEPT_KEYWORDS = {
    "Customer": {
        "customer": 1.0,
        "client": 0.9,
        "user": 0.8,
        ...
    }
}
```

## API Reference

### `resolve_query(nl_query: str, tenant_id: str, available_tools: Optional[List[str]]) -> ResolutionResult`

Main function to resolve natural language query.

**Parameters:**
- `nl_query`: Natural language query string
- `tenant_id`: Tenant identifier for URI resolution
- `available_tools`: Optional list of available tools for filtering

**Returns:**
- `ResolutionResult` with matched concepts, resource URIs, tools, and confidence

### `ResolutionResult`

Data class containing resolution results:

```python
@dataclass
class ResolutionResult:
    matched_concepts: List[str]          # Matched business concepts
    resource_uris: List[str]             # Resolved MCP resource URIs
    suggested_tools: List[str]           # Recommended tools (top 5)
    confidence_score: float              # Overall confidence (0.0-1.0)
    explanation: str                     # Human-readable explanation
    requires_permissions: List[str]      # Required permissions
```

### `extract_concepts(text: str, min_confidence: float = 0.3) -> List[Tuple[str, float]]`

Extract business concepts from text with confidence scores.

**Parameters:**
- `text`: Input text
- `min_confidence`: Minimum confidence threshold

**Returns:**
- List of (concept_name, confidence_score) tuples

### `resolve_template(template: str, tenant_id: str) -> str`

Resolve URI template by replacing `{{tenant}}` placeholder.

**Example:**
```python
resolve_template("mcp://{{tenant}}/postgres/customers", "tenant_001")
# Returns: "mcp://tenant_001/postgres/customers"
```

## Testing

### Run Tests

```bash
# Run all tests
pytest tests/test_nl_resource_resolver.py -v

# Run specific test class
pytest tests/test_nl_resource_resolver.py::TestQueryResolution -v
```

### Run Accuracy Benchmark

```bash
python benchmark_nl_resolver.py
```

**Expected Results:**
- Accuracy: > 80% for well-formed queries
- Average F1 score: > 0.85
- Confidence scores: > 0.7 for clear queries

## Supported Concepts

The resolver recognizes these business concepts:

1. **Revenue**: Sales, income, earnings, invoices, payments
2. **Customer**: Customers, clients, users, accounts, segments
3. **Inventory**: Stock, products, warehouses, suppliers
4. **Employee**: Staff, personnel, payroll, attendance, HR
5. **Transaction**: Payments, orders, purchases, refunds

## Edge Cases

### No Concepts Matched

When no concepts are detected:
- Returns generic search tools
- Low confidence score (< 0.3)
- Generic resource URI: `mcp://{tenant}/postgres/*`

```python
result = resolve_query("What is the weather today?", "tenant_001")
# Returns: Generic tools with low confidence
```

### Ambiguous Queries

For ambiguous queries:
- Returns all matched concepts with scores
- Multiple resource URIs and tools
- Explanation indicates multiple concepts detected

```python
result = resolve_query("Show me data", "tenant_001")
# Returns: Generic tools with low confidence
```

### Multiple Equally-Matched Concepts

When multiple concepts match equally:
- All concepts included in result
- Combined resources and tools
- Explanation lists all matched concepts

```python
result = resolve_query("customer revenue data", "tenant_001")
# Returns: ["Customer", "Revenue"] with combined resources
```

## Integration with Semantic Router (US-082)

The resolver integrates with the semantic router from US-082:

```python
# Use resolver to get concepts
from nl_resource_resolver import resolve_query
from mcp_semantic_router import resolve_concept

query = "Show me customer data"
resolution = resolve_query(query, "tenant_001")

# Use concepts with semantic router
for concept in resolution.matched_concepts:
    tools = get_tools_for_concept(concept)  # From semantic router
    # Use tools...
```

## Performance

- **Resolution Time**: < 10ms per query
- **Accuracy**: > 80% for well-formed queries
- **Confidence Scores**: Reliable for queries with clear business context

## Limitations

1. **Keyword-Based**: Uses keyword matching (not advanced NLP)
2. **English Only**: Currently supports English keywords only
3. **Fixed Ontology**: Concepts and keywords are predefined
4. **No Context**: Doesn't consider conversation context

## Future Enhancements

1. **Machine Learning**: Use ML models for better concept extraction
2. **Multi-Language**: Support multiple languages
3. **Context Awareness**: Consider conversation history
4. **Learning**: Learn from user corrections
5. **Fuzzy Matching**: Better handling of typos and variations

## License

This implementation is part of the AI Agent Connector project.

