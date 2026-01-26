# Quick Start Guide

Get up and running with AI Agent Connector in minutes!

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- PostgreSQL database (optional, for testing database connections)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/universal-agent-connector.git
cd universal-agent-connector
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables (Optional)

Create a `.env` file (or set environment variables):

```bash
# Flask Configuration
FLASK_ENV=development
PORT=5000
HOST=127.0.0.1
SECRET_KEY=your-secret-key-here

# OpenAI (for natural language queries)
OPENAI_API_KEY=your-openai-api-key-here

# Database (if using environment variables)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your-password
DB_NAME=your-database
```

### 5. Run the Application

```bash
python main.py
```

The application will start at: `http://127.0.0.1:5000`

## First Steps

### 1. Access the Dashboard

Open your browser and go to: `http://127.0.0.1:5000/dashboard`

### 2. Connect Your First Agent

1. Click "Connect New Agent" or go to `/wizard`
2. Follow the 4-step wizard:
   - **Step 1**: Enter agent information (ID, name, type)
   - **Step 2**: Configure database connection (test connection first!)
   - **Step 3**: Provide agent API credentials
   - **Step 4**: Review and connect

### 3. Set Permissions

After registering an agent:
1. Go to `/agents/<agent_id>`
2. View available tables
3. Set read/write permissions on specific tables

### 4. Test Natural Language Queries

1. Use the API endpoint: `POST /api/agents/<agent_id>/query/natural`
2. Or use the dashboard to submit queries

## API Quick Test

### Register an Agent

```bash
curl -X POST http://127.0.0.1:5000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent",
    "agent_info": {
      "name": "Test Agent",
      "type": "assistant"
    },
    "agent_credentials": {
      "api_key": "test-key",
      "api_secret": "test-secret"
    },
    "database": {
      "host": "localhost",
      "port": 5432,
      "user": "postgres",
      "password": "password",
      "database": "testdb"
    }
  }'
```

### Execute a Query

```bash
curl -X POST http://127.0.0.1:5000/api/agents/test-agent/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "query": "SELECT * FROM users LIMIT 10"
  }'
```

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

## Documentation

- **Full README**: See [README.md](README.md)
- **API Documentation**: Visit `http://127.0.0.1:5000/api/api-docs`
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## Need Help?

- Check the [README.md](README.md) for detailed documentation
- Review [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md) for feature verification
- Open an issue on GitHub for bugs or questions

## Common Issues

### Port Already in Use
```bash
# Use a different port
PORT=5001 python main.py
```

### Database Connection Fails
- Verify PostgreSQL is running
- Check connection credentials
- Test connection using `/api/databases/test` endpoint

### Missing Dependencies
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

Enjoy using AI Agent Connector! 🎉



