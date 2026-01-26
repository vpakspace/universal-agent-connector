# Financial Reporting Demo

Generate financial reports and analyze transactions with AI-powered queries.

## 🎯 What You'll Learn

- Connect a financial database
- Query transactions and accounts
- Generate financial summaries
- Analyze period comparisons

## ⚡ Quick Start (2 Minutes)

### Step 1: Setup Database

```bash
# Create database
createdb financial_demo

# Load sample data
psql -U postgres -d financial_demo -f demos/financial/setup.sql
```

Or use the automated setup:

```bash
# Linux/Mac
./demos/financial/setup.sh

# Windows
demos\financial\setup.ps1
```

### Step 2: Register Agent

```bash
curl -X POST http://localhost:5000/api/agents/register \
  -H "Content-Type: application/json" \
  -d @demos/financial/agent_config.json
```

### Step 3: Set Permissions

```bash
# Grant read access to all tables
for table in accounts transactions categories budgets; do
  curl -X PUT http://localhost:5000/api/agents/financial-analyst/permissions/resources \
    -H "Content-Type: application/json" \
    -d "{\"resource_id\": \"$table\", \"resource_type\": \"table\", \"permissions\": [\"read\"]}"
done
```

### Step 4: Try Natural Language Queries!

```bash
curl -X POST http://localhost:5000/api/agents/financial-analyst/query/natural \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "query": "What is the total revenue for this month?"
  }'
```

## 📊 Sample Queries

Try these natural language queries:

1. **"What is the total revenue for this month?"**
2. **"Show me expenses by category"**
3. **"What is the profit margin for last quarter?"**
4. **"Compare this month's revenue to last month"**
5. **"Show me the top 5 expense categories"**
6. **"What is the account balance for checking?"**
7. **"Show me transactions over $1000"**
8. **"Generate a financial summary for Q4"**

## 📁 Database Schema

The demo includes:

- **accounts** - Bank and financial accounts
- **transactions** - Financial transactions
- **categories** - Transaction categories
- **budgets** - Budget allocations

See [schema.sql](schema.sql) for full schema details.

## 🎥 Video Walkthrough

Follow the step-by-step guide: [WALKTHROUGH.md](WALKTHROUGH.md)

## 📈 Example Insights

After running queries, you can:

- Generate financial reports
- Analyze revenue and expenses
- Compare periods
- Track budgets
- Reconcile accounts

## 🔄 Next Steps

1. Explore the [E-Commerce Demo](../ecommerce/README.md)
2. Try the [SaaS Metrics Demo](../saas/README.md)
3. Connect your own financial database
4. Set up production financial reporting

---

**Questions?** Check the [main README](../../README.md) or [troubleshooting section](../../README.md#troubleshooting).

