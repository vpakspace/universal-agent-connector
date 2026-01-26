# E-Commerce Analytics Demo

Analyze sales, customers, and products with AI-powered natural language queries.

## 🎯 What You'll Learn

- Connect a database to an AI agent
- Query sales data with natural language
- Generate insights and reports
- Visualize data trends

## ⚡ Quick Start (2 Minutes)

### Step 1: Setup Database

```bash
# Create database
createdb ecommerce_demo

# Load sample data
psql -U postgres -d ecommerce_demo -f demos/ecommerce/setup.sql
```

Or use the automated setup:

```bash
# Linux/Mac
./demos/ecommerce/setup.sh

# Windows
demos\ecommerce\setup.ps1
```

### Step 2: Start AI Agent Connector

```bash
python main.py
```

### Step 3: Register Agent

Open the dashboard: http://localhost:5000/dashboard

Or use the API:

```bash
curl -X POST http://localhost:5000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "ecommerce-analyst",
    "agent_info": {
      "name": "E-Commerce Analytics Agent",
      "type": "analytics"
    },
    "agent_credentials": {
      "api_key": "demo-key",
      "api_secret": "demo-secret"
    },
    "database": {
      "connection_string": "postgresql://postgres:password@localhost:5432/ecommerce_demo",
      "connection_name": "ecommerce",
      "type": "postgresql"
    }
  }'
```

### Step 4: Set Permissions

```bash
# Grant read access to all tables
curl -X PUT http://localhost:5000/api/agents/ecommerce-analyst/permissions/resources \
  -H "Content-Type: application/json" \
  -d '{
    "resource_id": "products",
    "resource_type": "table",
    "permissions": ["read"]
  }'

# Repeat for: orders, customers, order_items, categories
```

### Step 5: Try Natural Language Queries!

```bash
curl -X POST http://localhost:5000/api/agents/ecommerce-analyst/query/natural \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "query": "What are the top 5 best-selling products?"
  }'
```

## 📊 Sample Queries

Try these natural language queries:

1. **"Show me total sales for last month"**
2. **"What are the top 10 customers by revenue?"**
3. **"Which product categories have the highest sales?"**
4. **"Show me sales trends over the past 6 months"**
5. **"What is the average order value?"**
6. **"Which products have the lowest inventory?"**
7. **"Show me customer retention rate"**
8. **"What are the most popular products in each category?"**

## 📁 Database Schema

The demo includes:

- **customers** - Customer information
- **products** - Product catalog
- **categories** - Product categories
- **orders** - Order transactions
- **order_items** - Order line items

See [schema.sql](schema.sql) for full schema details.

## 🎥 Video Walkthrough

Follow the step-by-step guide: [WALKTHROUGH.md](WALKTHROUGH.md)

## 📈 Example Insights

After running queries, you can:

- Generate sales reports
- Identify top customers
- Analyze product performance
- Track revenue trends
- Monitor inventory levels

## 🔄 Next Steps

1. Explore the [SaaS Metrics Demo](../saas/README.md)
2. Try the [Financial Reporting Demo](../financial/README.md)
3. Connect your own database
4. Set up production permissions

---

**Questions?** Check the [main README](../../README.md) or [troubleshooting section](../../README.md#troubleshooting).

