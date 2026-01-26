# 🎮 AI Agent Connector Playground Tutorial

Welcome to the interactive playground! This tutorial will guide you through using AI Agent Connector in just 5 minutes.

## 🎯 What You'll Learn

- How to register an AI agent
- How to query data with natural language
- How to use the demo databases
- How to generate insights and reports

## ⚡ Quick Start (5 Minutes)

### Step 1: Access the Dashboard (30 seconds)

The server should already be running. Open:

**👉 [Dashboard](http://localhost:5000/dashboard)**

You should see the AI Agent Connector dashboard with:
- System status
- Agent management
- Quick actions

### Step 2: Register Your First Agent (2 minutes)

#### Option A: Using the Dashboard (Recommended)

1. Click **"Register New Agent"** or go to the **Wizard**
2. Fill in the form:
   - **Agent ID**: `my-first-agent`
   - **Agent Name**: `My First Agent`
   - **Database**: Select one of the demo databases:
     - `ecommerce_demo` - For e-commerce analytics
     - `saas_demo` - For SaaS metrics
     - `financial_demo` - For financial reporting
   - **Connection String**: 
     ```
     postgresql://postgres:postgres@localhost:5432/ecommerce_demo
     ```
3. Click **"Test Connection"** to verify
4. Click **"Register Agent"**

#### Option B: Using the API

```bash
curl -X POST http://localhost:5000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my-first-agent",
    "agent_info": {
      "name": "My First Agent",
      "type": "analytics"
    },
    "agent_credentials": {
      "api_key": "demo-key",
      "api_secret": "demo-secret"
    },
    "database": {
      "connection_string": "postgresql://postgres:postgres@localhost:5432/ecommerce_demo",
      "connection_name": "ecommerce",
      "type": "postgresql"
    }
  }'
```

**Save the API key** from the response - you'll need it!

### Step 3: Set Permissions (1 minute)

Grant read access to tables:

```bash
# For e-commerce demo
curl -X PUT http://localhost:5000/api/agents/my-first-agent/permissions/resources \
  -H "Content-Type: application/json" \
  -d '{"resource_id": "products", "resource_type": "table", "permissions": ["read"]}'

# Repeat for other tables
for table in customers orders order_items categories; do
  curl -X PUT http://localhost:5000/api/agents/my-first-agent/permissions/resources \
    -H "Content-Type: application/json" \
    -d "{\"resource_id\": \"$table\", \"resource_type\": \"table\", \"permissions\": [\"read\"]}"
done
```

Or use the dashboard to set permissions visually.

### Step 4: Try Your First Query! (1 minute)

Now the fun part - query with natural language:

```bash
curl -X POST http://localhost:5000/api/agents/my-first-agent/query/natural \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key-from-step-2>" \
  -d '{
    "query": "What are the top 5 best-selling products?"
  }'
```

**Result**: You'll get SQL query and results showing top products!

### Step 5: Explore More Queries (30 seconds)

Try these queries:

**E-Commerce Demo:**
- "Show me total sales for last month"
- "What are the top 10 customers by revenue?"
- "Which product categories have the highest sales?"

**SaaS Demo:**
- "What is our current Monthly Recurring Revenue?"
- "Show me the churn rate for last month"
- "How many new users signed up this month?"

**Financial Demo:**
- "What is the total revenue for this month?"
- "Show me expenses by category"
- "What is the profit margin for last quarter?"

## 🎓 Interactive Exercises

### Exercise 1: Sales Analysis

**Goal**: Analyze sales trends

1. Register an agent for `ecommerce_demo`
2. Set permissions on `orders`, `order_items`, `products`
3. Query: "Show me sales trends over the past 6 months"
4. Query: "What is the average order value?"

### Exercise 2: SaaS Metrics

**Goal**: Track key SaaS metrics

1. Register an agent for `saas_demo`
2. Set permissions on `users`, `subscriptions`, `plans`
3. Query: "What is our current MRR?"
4. Query: "Show me user growth over the past 6 months"

### Exercise 3: Financial Reporting

**Goal**: Generate financial reports

1. Register an agent for `financial_demo`
2. Set permissions on `accounts`, `transactions`, `categories`
3. Query: "What is the total revenue for this month?"
4. Query: "Show me expenses by category"

## 📊 Demo Databases Overview

### E-Commerce Demo (`ecommerce_demo`)

**Tables:**
- `customers` - 10 customer records
- `products` - 20 product records
- `categories` - 8 product categories
- `orders` - 20 order records
- `order_items` - Order line items

**Use Cases:**
- Sales analytics
- Customer insights
- Product performance
- Revenue analysis

### SaaS Metrics Demo (`saas_demo`)

**Tables:**
- `users` - 18 user accounts
- `plans` - 4 subscription plans
- `subscriptions` - 18 subscription records
- `events` - 20 user activity events

**Use Cases:**
- MRR tracking
- Churn analysis
- User growth
- Conversion funnels

### Financial Reporting Demo (`financial_demo`)

**Tables:**
- `accounts` - 5 financial accounts
- `transactions` - 25 transaction records
- `categories` - 14 transaction categories
- `budgets` - 5 budget allocations

**Use Cases:**
- Financial reporting
- Expense analysis
- Revenue tracking
- Budget monitoring

## 🛠️ Available Tools

### Dashboard
- **URL**: http://localhost:5000/dashboard
- **Features**: Visual agent management, permission setup, query testing

### API Documentation
- **URL**: http://localhost:5000/api/api-docs
- **Features**: Complete API reference with examples

### GraphQL Playground
- **URL**: http://localhost:5000/graphql/playground
- **Features**: Interactive GraphQL query interface

### Console/Logs
- **URL**: http://localhost:5000/console
- **Features**: View application logs and debug

## 💡 Tips & Tricks

### 1. Use Natural Language
Instead of writing SQL, ask questions:
- ❌ `SELECT * FROM products WHERE price > 100`
- ✅ "Show me products over $100"

### 2. Be Specific
More specific queries get better results:
- ❌ "Show me data"
- ✅ "Show me total sales for January 2024"

### 3. Explore Schema First
Before querying, explore what's available:
```bash
curl http://localhost:5000/api/agents/my-first-agent/tables \
  -H "X-API-Key: <your-api-key>"
```

### 4. Use the Dashboard
The dashboard makes everything easier:
- Visual agent management
- Permission setup
- Query testing
- Result visualization

## 🐛 Troubleshooting

### Server Not Starting

```bash
# Check if server is running
curl http://localhost:5000/api/health

# Check logs
tail -f logs/app.log  # if logs exist
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h localhost -U postgres -d ecommerce_demo -c "SELECT 1"

# Check if databases exist
psql -h localhost -U postgres -l
```

### Permission Errors

```bash
# Verify permissions are set
curl http://localhost:5000/api/agents/my-first-agent/permissions/resources \
  -H "X-API-Key: <your-api-key>"
```

### Query Not Working

1. Check agent has permissions on required tables
2. Verify table names are correct
3. Try simpler queries first
4. Check API key is correct

## 🎯 Next Steps

After completing this tutorial:

1. **Explore All Demos**
   - Try all three demo databases
   - Compare different use cases

2. **Advanced Features**
   - Set up scheduled queries
   - Create visualizations
   - Export results

3. **Connect Your Own Database**
   - Register your own database
   - Set up production permissions
   - Use in your projects

4. **Read Documentation**
   - [Main README](../README.md)
   - [API Documentation](../README.md#api-endpoints)
   - [Security Guide](../SECURITY.md)

## 📚 Resources

- **Demo Projects**: [demos/README.md](../demos/README.md)
- **API Reference**: [README.md#api-endpoints](../README.md#api-endpoints)
- **GraphQL Examples**: [examples/graphql_examples.md](../examples/graphql_examples.md)

## 🎉 Congratulations!

You've completed the playground tutorial! You now know how to:
- ✅ Set up AI agents
- ✅ Query data with natural language
- ✅ Generate insights and reports
- ✅ Use the dashboard and API

**Ready for production?** Check out the [deployment guides](../deployment/README.md)!

---

**Questions?** Check the [troubleshooting](#-troubleshooting) section or review the [main README](../README.md).

