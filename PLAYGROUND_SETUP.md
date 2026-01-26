# Playground Setup Guide

Complete guide for setting up the "Try in Browser" playground.

## 📋 Overview

The playground provides a one-click browser-based environment with:
- Pre-configured development environment
- Pre-loaded demo databases
- Auto-starting server
- Guided tutorial

## 🎯 Supported Platforms

### 1. Gitpod

**Configuration**: `.gitpod.yml`

**Features:**
- PostgreSQL workspace image
- Automatic Python setup
- Demo database loading
- Auto-starting server
- Port forwarding

**Usage:**
1. Add Gitpod button to README
2. Click button to open workspace
3. Wait for setup (2-3 minutes)
4. Server starts automatically

### 2. GitHub Codespaces

**Configuration**: `.devcontainer/devcontainer.json`

**Features:**
- Python 3.11 dev container
- PostgreSQL feature
- Automatic setup scripts
- Port forwarding
- VS Code extensions

**Usage:**
1. Open repository on GitHub
2. Click "Code" → "Codespaces"
3. Create new codespace
4. Wait for setup
5. Server starts automatically

## 📁 Configuration Files

### Gitpod Configuration

**File**: `.gitpod.yml`

**Tasks:**
1. **Setup Python Environment** - Installs Python, dependencies
2. **Setup Demo Databases** - Creates and loads demo data
3. **Start AI Agent Connector** - Starts the server

**Ports:**
- Port 5000 - AI Agent Connector (auto-opens browser)

### Dev Container Configuration

**File**: `.devcontainer/devcontainer.json`

**Features:**
- Python 3.11 base image
- PostgreSQL feature
- VS Code extensions
- Post-create and post-start scripts

**Scripts:**
- `setup.sh` - Initial setup (runs once)
- `start.sh` - Start server (runs on start)

## 🔧 Setup Process

### Automatic Setup Flow

1. **Container Creation**
   - Base image loads
   - Features install (PostgreSQL, Python)
   - Extensions install

2. **Post-Create (setup.sh)**
   - Create virtual environment
   - Install Python dependencies
   - Wait for PostgreSQL
   - Create demo databases
   - Load sample data
   - Generate encryption key
   - Create .env file

3. **Post-Start (start.sh)**
   - Activate virtual environment
   - Load environment variables
   - Start AI Agent Connector server
   - Display welcome message

4. **Port Forwarding**
   - Port 5000 forwarded automatically
   - Browser opens to dashboard
   - Ready to use!

## 📊 Pre-Loaded Data

All three demo databases are automatically loaded:

### E-Commerce Demo
- Database: `ecommerce_demo`
- Tables: customers, products, categories, orders, order_items
- Records: 10 customers, 20 products, 20 orders

### SaaS Metrics Demo
- Database: `saas_demo`
- Tables: users, plans, subscriptions, events
- Records: 18 users, 4 plans, 18 subscriptions

### Financial Reporting Demo
- Database: `financial_demo`
- Tables: accounts, transactions, categories, budgets
- Records: 5 accounts, 25 transactions, 14 categories

## 🎓 Tutorial Integration

The playground includes:
- **PLAYGROUND_TUTORIAL.md** - Complete step-by-step guide
- **Welcome message** - Displayed on container start
- **Quick start links** - Direct links to dashboard, API docs
- **Sample queries** - Ready-to-use natural language queries

## 🔐 Security Notes

**Development Environment:**
- Uses default/development credentials
- Encryption key auto-generated
- Not suitable for production
- Data is ephemeral (resets on container restart)

**For Production:**
- Use proper secret management
- Set strong encryption keys
- Use secure database credentials
- Follow [SECURITY.md](SECURITY.md) guidelines

## 🛠️ Customization

### Adding More Demo Data

Edit the setup scripts to load additional data:

```bash
# In .devcontainer/setup.sh or .gitpod.yml
psql -d ecommerce_demo -f demos/ecommerce/additional_data.sql
```

### Changing Port

Edit configuration files:

```yaml
# .gitpod.yml
ports:
  - port: 8080  # Change port
```

```json
// .devcontainer/devcontainer.json
"forwardPorts": [8080, 5432]
```

### Adding Environment Variables

```yaml
# .gitpod.yml
env:
  - name: CUSTOM_VAR
    value: "value"
```

```json
// .devcontainer/devcontainer.json
"remoteEnv": {
  "CUSTOM_VAR": "value"
}
```

## 📝 Maintenance

### Updating Demo Data

1. Edit SQL files in `demos/*/setup.sql`
2. Update setup scripts if needed
3. Test in playground
4. Commit changes

### Updating Dependencies

1. Update `requirements.txt`
2. Test in playground
3. Verify all demos still work
4. Commit changes

### Updating Tutorial

1. Edit `PLAYGROUND_TUTORIAL.md`
2. Test walkthrough
3. Update screenshots if needed
4. Commit changes

## 🐛 Troubleshooting

### Container Won't Start

- Check configuration file syntax
- Verify base image exists
- Check feature compatibility

### Database Not Loading

- Check PostgreSQL is running
- Verify connection credentials
- Check SQL script syntax
- Review setup script logs

### Server Not Starting

- Check Python dependencies
- Verify environment variables
- Check port availability
- Review application logs

### Port Not Forwarding

- Check port configuration
- Verify port forwarding settings
- Try manual port forwarding
- Check firewall settings

## 📚 Related Documentation

- [PLAYGROUND_TUTORIAL.md](PLAYGROUND_TUTORIAL.md) - User tutorial
- [demos/README.md](demos/README.md) - Demo projects
- [README.md](README.md) - Main documentation

---

**Status**: ✅ Complete  
**Last Updated**: 2024-01-15

