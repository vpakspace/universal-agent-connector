# Chargeback and Cost Allocation Guide

Complete guide for chargeback reporting, cost allocation, and invoice generation by team and user.

## 🎯 Overview

The Chargeback system enables accurate cost allocation and reporting:

- **Usage Tracking**: Track resource usage by team and user
- **Cost Allocation Rules**: Define how costs are allocated (by usage, equal split, fixed percentages)
- **Invoice Generation**: Generate invoices from allocated costs
- **Chargeback Reports**: Get detailed reports by team or user

## 🚀 Quick Start

### Record Usage

```bash
POST /api/chargeback/usage
Body: {
  "team_id": "team-123",
  "user_id": "user-456",
  "agent_id": "agent-789",
  "resource_type": "query",
  "quantity": 100.0,
  "cost_usd": 5.50
}
```

### Generate Invoice

```bash
POST /api/chargeback/invoices
Body: {
  "team_id": "team-123",
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-01-31T23:59:59Z"
}
```

### Get Team Report

```bash
GET /api/chargeback/reports/team/team-123?period_start=2024-01-01T00:00:00Z&period_end=2024-01-31T23:59:59Z
```

## 📊 Cost Allocation Rules

### Allocation Types

1. **By Usage** (`by_usage`)
   - Allocate costs based on actual usage
   - Direct allocation to team/user who used the resource
   - Default allocation method

2. **By Team** (`by_team`)
   - Split costs equally among team members
   - Useful when costs should be shared

3. **By User** (`by_user`)
   - Allocate costs to specific users
   - Use when certain users are responsible for costs

4. **Fixed Split** (`fixed_split`)
   - Allocate using fixed percentages
   - Define exact percentage for each entity

5. **Equal Split** (`equal_split`)
   - Split costs equally among entities
   - Distribute evenly across teams/users

### Creating Allocation Rules

```bash
POST /api/chargeback/allocation-rules
Body: {
  "rule_id": "team-equal-split",
  "name": "Team Equal Split",
  "description": "Split costs equally among team members",
  "rule_type": "by_team",
  "enabled": true,
  "team_id": "team-123"
}
```

## 📝 Usage Tracking

### Recording Usage

Usage can be recorded automatically from cost tracking or manually:

**Manual Recording:**
```bash
POST /api/chargeback/usage
Body: {
  "team_id": "team-123",
  "user_id": "user-456",
  "agent_id": "agent-789",
  "resource_type": "query",
  "quantity": 100.0,
  "cost_usd": 5.50,
  "metadata": {
    "query_type": "nl_to_sql",
    "database": "analytics_db"
  }
}
```

### Usage Summary

Get usage summary for a period:

```bash
GET /api/chargeback/usage/summary?period_start=2024-01-01T00:00:00Z&period_end=2024-01-31T23:59:59Z&team_id=team-123
```

**Response:**
```json
{
  "summary": {
    "period_start": "2024-01-01T00:00:00Z",
    "period_end": "2024-01-31T23:59:59Z",
    "team_id": "team-123",
    "total_cost_usd": 1250.50,
    "total_quantity": 15000.0,
    "record_count": 500,
    "by_resource_type": {
      "query": {"cost": 1000.0, "quantity": 10000.0},
      "storage": {"cost": 250.50, "quantity": 5000.0}
    },
    "by_agent": {
      "agent-1": {"cost": 800.0, "quantity": 8000.0},
      "agent-2": {"cost": 450.50, "quantity": 7000.0}
    }
  }
}
```

## 💰 Cost Allocation

### Allocate Costs

Allocate costs for a period:

```bash
POST /api/chargeback/allocate
Body: {
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-01-31T23:59:59Z",
  "team_id": "team-123"  // Optional
}
```

**Response:**
```json
{
  "allocations": [
    {
      "allocation_id": "alloc-123",
      "rule_id": "by_usage",
      "team_id": "team-123",
      "user_id": "user-456",
      "period_start": "2024-01-01T00:00:00Z",
      "period_end": "2024-01-31T23:59:59Z",
      "total_cost_usd": 250.50,
      "usage_records": ["usage-1", "usage-2"],
      "allocation_details": {}
    }
  ]
}
```

## 📄 Invoice Generation

### Generate Invoice

Generate invoice from allocated costs:

```bash
POST /api/chargeback/invoices
Body: {
  "team_id": "team-123",
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-01-31T23:59:59Z",
  "invoice_number": "INV-20240101-0001"  // Optional
}
```

**Response:**
```json
{
  "invoice": {
    "invoice_id": "inv-123",
    "invoice_number": "INV-20240101-0001",
    "team_id": "team-123",
    "period_start": "2024-01-01T00:00:00Z",
    "period_end": "2024-01-31T23:59:59Z",
    "status": "draft",
    "line_items": [
      {
        "description": "Query Usage - 2024-01-01T00:00:00Z to 2024-01-31T23:59:59Z",
        "quantity": 10,
        "unit_price": 100.0,
        "total_price": 1000.0,
        "resource_type": "query"
      }
    ],
    "subtotal_usd": 1000.0,
    "tax_usd": 0.0,
    "total_usd": 1000.0,
    "currency": "USD",
    "due_date": "2024-02-15T00:00:00Z"
  }
}
```

### Invoice Status

Invoice statuses:
- `draft` - Draft invoice
- `pending` - Pending approval
- `sent` - Sent to customer
- `paid` - Payment received
- `overdue` - Past due date
- `cancelled` - Cancelled invoice

### Update Invoice Status

```bash
PUT /api/chargeback/invoices/{invoice_id}/status
Body: {
  "status": "sent"
}
```

### List Invoices

```bash
GET /api/chargeback/invoices?team_id=team-123&status=sent
```

## 📈 Chargeback Reports

### Team Report

Get comprehensive chargeback report for a team:

```bash
GET /api/chargeback/reports/team/team-123?period_start=2024-01-01T00:00:00Z&period_end=2024-01-31T23:59:59Z
```

**Response includes:**
- Usage summary
- Cost allocations
- Invoices
- Total costs

### User Report

Get chargeback report for a user:

```bash
GET /api/chargeback/reports/user/user-456?period_start=2024-01-01T00:00:00Z&period_end=2024-01-31T23:59:59Z
```

## 🔧 API Reference

### Usage Recording

```
POST /api/chargeback/usage
```

Record resource usage for chargeback.

### Allocation Rules

```
GET /api/chargeback/allocation-rules
POST /api/chargeback/allocation-rules
GET /api/chargeback/allocation-rules/{rule_id}
PUT /api/chargeback/allocation-rules/{rule_id}
DELETE /api/chargeback/allocation-rules/{rule_id}
```

Manage cost allocation rules.

### Cost Allocation

```
POST /api/chargeback/allocate
```

Allocate costs for a period.

### Invoices

```
POST /api/chargeback/invoices
GET /api/chargeback/invoices
GET /api/chargeback/invoices/{invoice_id}
PUT /api/chargeback/invoices/{invoice_id}/status
```

Generate and manage invoices.

### Usage Summary

```
GET /api/chargeback/usage/summary
```

Get usage summary for a period.

### Reports

```
GET /api/chargeback/reports/team/{team_id}
GET /api/chargeback/reports/user/{user_id}
```

Get chargeback reports.

## 🔍 Examples

### Example 1: Team-Based Allocation

```python
import requests

# Create allocation rule
response = requests.post(
    'http://localhost:5000/api/chargeback/allocation-rules',
    json={
        'rule_id': 'team-equal-split',
        'name': 'Team Equal Split',
        'description': 'Split costs equally among team members',
        'rule_type': 'by_team',
        'enabled': True,
        'team_id': 'team-123'
    }
)

# Record usage
for i in range(10):
    requests.post(
        'http://localhost:5000/api/chargeback/usage',
        json={
            'team_id': 'team-123',
            'user_id': f'user-{i}',
            'resource_type': 'query',
            'quantity': 100.0,
            'cost_usd': 10.0
        }
    )

# Allocate costs
response = requests.post(
    'http://localhost:5000/api/chargeback/allocate',
    json={
        'period_start': '2024-01-01T00:00:00Z',
        'period_end': '2024-01-31T23:59:59Z',
        'team_id': 'team-123'
    }
)

allocations = response.json()['allocations']
print(f"Total allocations: {len(allocations)}")
```

### Example 2: Fixed Percentage Split

```python
# Create fixed split rule
response = requests.post(
    'http://localhost:5000/api/chargeback/allocation-rules',
    json={
        'rule_id': 'fixed-split-rule',
        'name': 'Fixed Split',
        'description': '60% team A, 40% team B',
        'rule_type': 'fixed_split',
        'enabled': True,
        'split_percentages': {
            'team-123': 60.0,
            'team-456': 40.0
        },
        'allocation_metadata': {
            'entity_type': 'team'
        }
    }
)
```

### Example 3: Generate Monthly Invoice

```python
from datetime import datetime, timedelta

# Calculate last month
today = datetime.utcnow()
first_day = today.replace(day=1)
last_month_end = first_day - timedelta(days=1)
last_month_start = last_month_end.replace(day=1)

# Generate invoice
response = requests.post(
    'http://localhost:5000/api/chargeback/invoices',
    json={
        'team_id': 'team-123',
        'period_start': last_month_start.isoformat() + 'Z',
        'period_end': last_month_end.isoformat() + 'Z'
    }
)

invoice = response.json()['invoice']
print(f"Invoice {invoice['invoice_number']}: ${invoice['total_usd']}")
```

### Example 4: Get Team Report

```python
response = requests.get(
    'http://localhost:5000/api/chargeback/reports/team/team-123',
    params={
        'period_start': '2024-01-01T00:00:00Z',
        'period_end': '2024-01-31T23:59:59Z'
    }
)

report = response.json()['report']
print(f"Total cost: ${report['total_cost_usd']}")
print(f"Invoices: {len(report['invoices'])}")
print(f"Allocations: {len(report['allocations'])}")
```

## 🎨 Best Practices

### Allocation Rules

1. **Start Simple**: Begin with by_usage allocation
2. **Document Rules**: Clearly document allocation logic
3. **Test Rules**: Test allocation rules before production
4. **Review Regularly**: Review and update rules as needed

### Usage Tracking

1. **Record Accurately**: Ensure usage records are accurate
2. **Include Metadata**: Add metadata for better tracking
3. **Link to Resources**: Link usage to agents/resources
4. **Track Regularly**: Record usage consistently

### Invoice Management

1. **Generate Regularly**: Generate invoices on schedule
2. **Review Before Sending**: Review invoices before sending
3. **Track Status**: Update invoice status accurately
4. **Archive Invoices**: Keep invoice history

### Reporting

1. **Regular Reports**: Generate reports regularly
2. **Compare Periods**: Compare across time periods
3. **Identify Trends**: Look for cost trends
4. **Optimize Costs**: Use reports to optimize costs

## 🐛 Troubleshooting

### No Allocations Generated

**Issue**: Allocation returns empty list
**Solution**: Check that usage records exist for the period and match filters

### Incorrect Allocation Amounts

**Issue**: Allocated costs don't match expectations
**Solution**: Review allocation rules, check rule configuration

### Invoice Missing Line Items

**Issue**: Invoice has no line items
**Solution**: Ensure costs are allocated before generating invoice

### Usage Not Recorded

**Issue**: Usage summary shows no usage
**Solution**: Verify usage records are being created, check date filters

## 📈 Production Considerations

### Integration with Cost Tracker

- Integrate with existing CostTracker
- Automatically record usage from cost records
- Link agent usage to teams/users

### Data Storage

- Use database for production (currently in-memory)
- Implement data retention policies
- Archive old invoices and allocations

### Performance

- Index usage records by date/team/user
- Cache allocation results
- Batch allocation processing

### Security

- Restrict access to chargeback endpoints
- Audit allocation rule changes
- Secure invoice data

---

**Questions?** Check [GitHub Discussions](https://github.com/your-repo/ai-agent-connector/discussions) or open an issue!

