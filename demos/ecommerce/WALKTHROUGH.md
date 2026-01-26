# E-Commerce Demo Walkthrough

Step-by-step guide to get value in 2 minutes.

## 🎥 Video Walkthrough

**Duration**: 2 minutes  
**Prerequisites**: PostgreSQL installed, AI Agent Connector running

### Step 1: Setup (30 seconds)

```bash
# Create database
createdb ecommerce_demo

# Load sample data
psql -U postgres -d ecommerce_demo -f demos/ecommerce/setup.sql
```

**What happens**: Creates tables, inserts sample data (10 customers, 20 products, 20 orders)

### Step 2: Register Agent (30 seconds)

Open http://localhost:5000/dashboard and click "Register New Agent"

Or use API:

```bash
curl -X POST http://localhost:5000/api/agents/register \
  -H "Content-Type: application/json" \
  -d @demos/ecommerce/agent_config.json
```

**What happens**: Creates agent "ecommerce-analyst" connected to demo database

### Step 3: Set Permissions (20 seconds)

```bash
# Grant read access to all tables
for table in customers products orders order_items categories; do
  curl -X PUT http://localhost:5000/api/agents/ecommerce-analyst/permissions/resources \
    -H "Content-Type: application/json" \
    -d "{\"resource_id\": \"$table\", \"resource_type\": \"table\", \"permissions\": [\"read\"]}"
done
```

**What happens**: Agent can now read all e-commerce data

### Step 4: Query with Natural Language (40 seconds)

```bash
# Get your API key from registration response, then:

curl -X POST http://localhost:5000/api/agents/ecommerce-analyst/query/natural \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{"query": "What are the top 5 best-selling products?"}'
```

**Result**: Returns SQL query and results showing top products by sales

## 📊 Try These Queries

1. **"Show me total sales for last month"**
   - Returns: Total revenue for January 2024

2. **"What are the top 10 customers by revenue?"**
   - Returns: Customer list sorted by total order value

3. **"Which product categories have the highest sales?"**
   - Returns: Sales breakdown by category

4. **"Show me sales trends over the past 6 months"**
   - Returns: Monthly sales summary

5. **"What is the average order value?"**
   - Returns: Average order amount

## 🎯 Key Insights

After running queries, you'll see:

- ✅ **Sales Analytics**: Total revenue, trends, top products
- ✅ **Customer Insights**: Top customers, retention, segmentation
- ✅ **Product Performance**: Best sellers, inventory levels
- ✅ **Revenue Analysis**: Monthly trends, category breakdown

## 🔄 Next Steps

1. Try more complex queries
2. Explore the [SaaS Metrics Demo](../saas/README.md)
3. Connect your own database
4. Set up production permissions

---

**Total Time**: ~2 minutes  
**Value Delivered**: Working analytics system with natural language queries

