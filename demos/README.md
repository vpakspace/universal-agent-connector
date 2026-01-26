# Interactive Demo Projects

Get started with AI Agent Connector in 2 minutes! These interactive demos showcase real-world use cases with sample data.

## 🚀 Quick Start

1. **Choose a demo** from the list below
2. **Run the setup script** to create sample data
3. **Follow the walkthrough** to see the value

## 📚 Available Demos

### 1. E-Commerce Analytics Demo
**Time**: 2 minutes | **Complexity**: Beginner

Analyze sales, customers, and products with natural language queries.

- 📊 Sales analytics and trends
- 👥 Customer segmentation
- 📦 Product performance
- 💰 Revenue analysis

[Get Started →](ecommerce/README.md)

### 2. SaaS Metrics Dashboard Demo
**Time**: 2 minutes | **Complexity**: Beginner

Track key SaaS metrics like MRR, churn, and user growth.

- 📈 Monthly Recurring Revenue (MRR)
- 👤 User growth and retention
- 💸 Churn analysis
- 🎯 Conversion funnels

[Get Started →](saas/README.md)

### 3. Financial Reporting Demo
**Time**: 2 minutes | **Complexity**: Intermediate

Generate financial reports and analyze transactions.

- 💵 Transaction analysis
- 📊 Financial summaries
- 📅 Period comparisons
- 💼 Account reconciliation

[Get Started →](financial/README.md)

## 🎥 Video Walkthroughs

Each demo includes a step-by-step walkthrough. Watch the videos or follow the written guides:

- [E-Commerce Demo Walkthrough](ecommerce/WALKTHROUGH.md)
- [SaaS Metrics Demo Walkthrough](saas/WALKTHROUGH.md)
- [Financial Reporting Demo Walkthrough](financial/WALKTHROUGH.md)

## 🛠️ Prerequisites

Before running any demo:

1. **PostgreSQL** installed and running
2. **Python 3.8+** installed
3. **AI Agent Connector** installed (see main README)
4. **OpenAI API Key** (optional, for natural language queries)

## 📦 Setup All Demos

Run all setup scripts at once:

```bash
# Setup all demo databases
./demos/setup_all_demos.sh

# Or on Windows
demos\setup_all_demos.ps1
```

## 🎯 What You'll Learn

Each demo teaches you:

- ✅ How to connect databases to AI agents
- ✅ How to set up permissions
- ✅ How to query data with natural language
- ✅ How to generate insights and reports
- ✅ Best practices for production use

## 🆘 Need Help?

- Check the [main README](../README.md) for installation
- See [troubleshooting](#troubleshooting) below
- Review [API documentation](../README.md#api-endpoints)

## 🔄 Next Steps

After completing the demos:

1. Connect your own database
2. Register your own agents
3. Set up production permissions
4. Explore advanced features

---

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Create demo databases
createdb ecommerce_demo
createdb saas_demo
createdb financial_demo
```

### Permission Errors

```bash
# Grant permissions (PostgreSQL)
psql -U postgres -d ecommerce_demo -f demos/ecommerce/setup.sql
```

### API Key Issues

For natural language queries, set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-key-here"
```

Or use air-gapped mode with local models (see [AIR_GAPPED_MODE.md](../AIR_GAPPED_MODE.md)).

---

**Ready to get started?** Pick a demo above and follow the walkthrough! 🎉

