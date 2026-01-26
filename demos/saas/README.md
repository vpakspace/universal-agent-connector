# SaaS Metrics Dashboard Demo

Track key SaaS metrics like MRR, churn, and user growth with AI-powered analytics.

## 🎯 What You'll Learn

- Connect a database to track SaaS metrics
- Query MRR, churn, and growth metrics
- Generate SaaS dashboards
- Analyze user behavior and retention

## ⚡ Quick Start (2 Minutes)

### Step 1: Setup Database

```bash
# Create database
createdb saas_demo

# Load sample data
psql -U postgres -d saas_demo -f demos/saas/setup.sql
```

Or use the automated setup:

```bash
# Linux/Mac
./demos/saas/setup.sh

# Windows
demos\saas\setup.ps1
```

### Step 2: Register Agent

```bash
curl -X POST http://localhost:5000/api/agents/register \
  -H "Content-Type: application/json" \
  -d @demos/saas/agent_config.json
```

### Step 3: Set Permissions

```bash
# Grant read access to all tables
for table in users subscriptions plans events; do
  curl -X PUT http://localhost:5000/api/agents/saas-analyst/permissions/resources \
    -H "Content-Type: application/json" \
    -d "{\"resource_id\": \"$table\", \"resource_type\": \"table\", \"permissions\": [\"read\"]}"
done
```

### Step 4: Try Natural Language Queries!

```bash
curl -X POST http://localhost:5000/api/agents/saas-analyst/query/natural \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "query": "What is our current MRR?"
  }'
```

## 📊 Sample Queries

Try these natural language queries:

1. **"What is our current Monthly Recurring Revenue?"**
2. **"Show me the churn rate for last month"**
3. **"How many new users signed up this month?"**
4. **"What is the average revenue per user?"**
5. **"Show me user growth over the past 6 months"**
6. **"Which plan has the most subscribers?"**
7. **"What is our customer lifetime value?"**
8. **"Show me conversion rates by plan"**

## 📁 Database Schema

The demo includes:

- **users** - User accounts and profiles
- **subscriptions** - Active and past subscriptions
- **plans** - Subscription plan details
- **events** - User activity events

See [schema.sql](schema.sql) for full schema details.

## 🎥 Video Walkthrough

Follow the step-by-step guide: [WALKTHROUGH.md](WALKTHROUGH.md)

## 📈 Example Insights

After running queries, you can:

- Track MRR growth
- Monitor churn rates
- Analyze user acquisition
- Measure conversion funnels
- Calculate LTV and ARPU

## 🔄 Next Steps

1. Explore the [E-Commerce Demo](../ecommerce/README.md)
2. Try the [Financial Reporting Demo](../financial/README.md)
3. Connect your own database
4. Set up production metrics tracking

---

**Questions?** Check the [main README](../../README.md) or [troubleshooting section](../../README.md#troubleshooting).

