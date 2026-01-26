# Demo Projects Quick Start

Get value in 2 minutes with any of our interactive demos!

## 🎯 Choose Your Demo

### 1. E-Commerce Analytics (Recommended for Beginners)
**Best for**: Sales analysis, customer insights, product performance

```bash
createdb ecommerce_demo
psql -U postgres -d ecommerce_demo -f demos/ecommerce/setup.sql
```

**Try this query**: "What are the top 5 best-selling products?"

### 2. SaaS Metrics Dashboard
**Best for**: MRR tracking, churn analysis, user growth

```bash
createdb saas_demo
psql -U postgres -d saas_demo -f demos/saas/setup.sql
```

**Try this query**: "What is our current Monthly Recurring Revenue?"

### 3. Financial Reporting
**Best for**: Revenue analysis, expense tracking, financial summaries

```bash
createdb financial_demo
psql -U postgres -d financial_demo -f demos/financial/setup.sql
```

**Try this query**: "What is the total revenue for this month?"

## ⚡ 2-Minute Setup

### Step 1: Setup Database (30 seconds)

```bash
# Pick one demo and run:
createdb ecommerce_demo
psql -U postgres -d ecommerce_demo -f demos/ecommerce/setup.sql
```

### Step 2: Start AI Agent Connector (10 seconds)

```bash
python main.py
```

### Step 3: Register Agent (30 seconds)

Open http://localhost:5000/dashboard and use the wizard, or:

```bash
curl -X POST http://localhost:5000/api/agents/register \
  -H "Content-Type: application/json" \
  -d @demos/ecommerce/agent_config.json
```

### Step 4: Set Permissions (20 seconds)

```bash
curl -X PUT http://localhost:5000/api/agents/ecommerce-analyst/permissions/resources \
  -H "Content-Type: application/json" \
  -d '{"resource_id": "products", "resource_type": "table", "permissions": ["read"]}'
```

### Step 5: Query with Natural Language (30 seconds)

```bash
curl -X POST http://localhost:5000/api/agents/ecommerce-analyst/query/natural \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{"query": "What are the top 5 best-selling products?"}'
```

**Done!** You now have a working AI-powered analytics system.

## 📚 Full Walkthroughs

- [E-Commerce Walkthrough](ecommerce/WALKTHROUGH.md)
- [SaaS Metrics Walkthrough](saas/WALKTHROUGH.md)
- [Financial Reporting Walkthrough](financial/WALKTHROUGH.md)

## 🎥 Video Guides

Each demo includes a detailed walkthrough with:
- Step-by-step instructions
- Screenshots and examples
- Common queries to try
- Troubleshooting tips

## 🆘 Need Help?

- Check [main README](../README.md) for installation
- See [troubleshooting](#troubleshooting) below
- Review demo-specific README files

## 🔄 Next Steps

After completing a demo:

1. Try more complex queries
2. Explore other demos
3. Connect your own database
4. Set up production permissions

---

**Ready?** Pick a demo above and get started! 🚀

