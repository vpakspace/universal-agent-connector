# Financial Reporting Demo Walkthrough

Step-by-step guide to generate financial reports in 2 minutes.

## 🎥 Video Walkthrough

**Duration**: 2 minutes  
**Prerequisites**: PostgreSQL installed, AI Agent Connector running

### Step 1: Setup (30 seconds)

```bash
# Create database
createdb financial_demo

# Load sample data
psql -U postgres -d financial_demo -f demos/financial/setup.sql
```

**What happens**: Creates tables, inserts sample data (5 accounts, 25 transactions, 14 categories, 5 budgets)

### Step 2: Register Agent (30 seconds)

```bash
curl -X POST http://localhost:5000/api/agents/register \
  -H "Content-Type: application/json" \
  -d @demos/financial/agent_config.json
```

**What happens**: Creates agent "financial-analyst" connected to demo database

### Step 3: Set Permissions (20 seconds)

```bash
# Grant read access to all tables
for table in accounts transactions categories budgets; do
  curl -X PUT http://localhost:5000/api/agents/financial-analyst/permissions/resources \
    -H "Content-Type: application/json" \
    -d "{\"resource_id\": \"$table\", \"resource_type\": \"table\", \"permissions\": [\"read\"]}"
done
```

**What happens**: Agent can now read all financial data

### Step 4: Query Revenue (40 seconds)

```bash
curl -X POST http://localhost:5000/api/agents/financial-analyst/query/natural \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{"query": "What is the total revenue for this month?"}'
```

**Result**: Returns total revenue for January 2024

## 📊 Try These Queries

1. **"What is the total revenue for this month?"**
   - Returns: Total revenue for January 2024

2. **"Show me expenses by category"**
   - Returns: Expense breakdown by category

3. **"What is the profit margin for last quarter?"**
   - Returns: Profit calculation (revenue - expenses)

4. **"Compare this month's revenue to last month"**
   - Returns: Month-over-month comparison

5. **"Show me the top 5 expense categories"**
   - Returns: Highest expense categories

6. **"What is the account balance for checking?"**
   - Returns: Current checking account balance

## 🎯 Key Reports

After running queries, you can:

- ✅ **Revenue Reports**: Monthly/quarterly revenue summaries
- ✅ **Expense Analysis**: Category-wise expense breakdown
- ✅ **Profit & Loss**: P&L statements
- ✅ **Budget Tracking**: Actual vs. budgeted amounts
- ✅ **Account Reconciliation**: Account balance verification
- ✅ **Period Comparisons**: Month-over-month, quarter-over-quarter

## 🔄 Next Steps

1. Try more complex financial queries
2. Explore the [E-Commerce Demo](../ecommerce/README.md)
3. Connect your own financial database
4. Set up production financial reporting

---

**Total Time**: ~2 minutes  
**Value Delivered**: Working financial reporting system with natural language queries

