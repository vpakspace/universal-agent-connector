# SaaS Metrics Demo Walkthrough

Step-by-step guide to track SaaS metrics in 2 minutes.

## 🎥 Video Walkthrough

**Duration**: 2 minutes  
**Prerequisites**: PostgreSQL installed, AI Agent Connector running

### Step 1: Setup (30 seconds)

```bash
# Create database
createdb saas_demo

# Load sample data
psql -U postgres -d saas_demo -f demos/saas/setup.sql
```

**What happens**: Creates tables, inserts sample data (18 users, 4 plans, 18 subscriptions)

### Step 2: Register Agent (30 seconds)

```bash
curl -X POST http://localhost:5000/api/agents/register \
  -H "Content-Type: application/json" \
  -d @demos/saas/agent_config.json
```

**What happens**: Creates agent "saas-analyst" connected to demo database

### Step 3: Set Permissions (20 seconds)

```bash
# Grant read access to all tables
for table in users subscriptions plans events; do
  curl -X PUT http://localhost:5000/api/agents/saas-analyst/permissions/resources \
    -H "Content-Type: application/json" \
    -d "{\"resource_id\": \"$table\", \"resource_type\": \"table\", \"permissions\": [\"read\"]}"
done
```

**What happens**: Agent can now read all SaaS metrics data

### Step 4: Query MRR (40 seconds)

```bash
curl -X POST http://localhost:5000/api/agents/saas-analyst/query/natural \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{"query": "What is our current Monthly Recurring Revenue?"}'
```

**Result**: Returns current MRR calculation from active subscriptions

## 📊 Try These Queries

1. **"What is our current Monthly Recurring Revenue?"**
   - Returns: Total MRR from all active subscriptions

2. **"Show me the churn rate for last month"**
   - Returns: Percentage of users who cancelled

3. **"How many new users signed up this month?"**
   - Returns: Count of new users in January 2024

4. **"What is the average revenue per user?"**
   - Returns: ARPU calculation

5. **"Show me user growth over the past 6 months"**
   - Returns: Monthly user signup trends

6. **"Which plan has the most subscribers?"**
   - Returns: Plan popularity breakdown

## 🎯 Key Metrics

After running queries, you'll see:

- ✅ **MRR**: Monthly Recurring Revenue tracking
- ✅ **Churn**: Customer cancellation rates
- ✅ **Growth**: User acquisition trends
- ✅ **ARPU**: Average Revenue Per User
- ✅ **LTV**: Customer Lifetime Value
- ✅ **Conversion**: Plan conversion rates

## 🔄 Next Steps

1. Try more complex metrics queries
2. Explore the [E-Commerce Demo](../ecommerce/README.md)
3. Connect your own SaaS database
4. Set up production metrics tracking

---

**Total Time**: ~2 minutes  
**Value Delivered**: Working SaaS metrics dashboard with natural language queries

