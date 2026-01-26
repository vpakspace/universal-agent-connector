# Dev Container / GitHub Codespaces Setup

This directory contains configuration for running AI Agent Connector in browser-based development environments.

## 🚀 One-Click Setup

### GitHub Codespaces

1. **Open in Codespaces**:
   - Click the green "Code" button on GitHub
   - Select "Codespaces" tab
   - Click "Create codespace on main"

2. **Wait for Setup**:
   - Container will build automatically
   - Dependencies will install
   - Demo databases will load
   - Server will start

3. **Access the Application**:
   - Port 5000 will be forwarded automatically
   - Open the forwarded port in browser
   - Follow the [Playground Tutorial](../PLAYGROUND_TUTORIAL.md)

### VS Code Dev Containers

1. **Open in Container**:
   - Install "Dev Containers" extension
   - Open command palette (F1)
   - Select "Dev Containers: Reopen in Container"

2. **Setup Runs Automatically**:
   - All dependencies install
   - Demo databases created
   - Server starts

3. **Access the Application**:
   - Port 5000 forwarded automatically
   - Open http://localhost:5000

## 📁 Files

- `devcontainer.json` - Dev container configuration
- `setup.sh` - Initial setup script (runs once)
- `start.sh` - Start script (runs on container start)
- `README.md` - This file

## 🔧 Configuration

The dev container includes:
- Python 3.11
- PostgreSQL 14
- All Python dependencies
- Pre-loaded demo databases
- Auto-starting server

## 🎯 What's Pre-Loaded

- ✅ Python virtual environment
- ✅ All dependencies installed
- ✅ 3 demo databases with sample data:
  - `ecommerce_demo`
  - `saas_demo`
  - `financial_demo`
- ✅ Server auto-starts on port 5000

## 📚 Next Steps

1. Follow the [Playground Tutorial](../PLAYGROUND_TUTORIAL.md)
2. Explore the [demo projects](../demos/README.md)
3. Read the [main README](../README.md)

---

**Note**: First-time setup may take 2-3 minutes. Subsequent starts are faster!

