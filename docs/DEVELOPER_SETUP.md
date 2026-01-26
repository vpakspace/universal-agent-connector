# Developer Setup Guide

Complete guide for setting up a development environment for AI Agent Connector.

## Prerequisites

### Required Software

- **Python 3.11+**: [Download](https://www.python.org/downloads/)
- **Node.js 14+**: [Download](https://nodejs.org/) (for CLI tool)
- **PostgreSQL 14+**: [Download](https://www.postgresql.org/download/) or use Docker
- **Git**: [Download](https://git-scm.com/downloads)

### Optional Tools

- **Docker**: For containerized databases
- **VS Code**: Recommended IDE
- **Postman/Insomnia**: For API testing

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-username/ai-agent-connector.git
cd ai-agent-connector
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy
```

### 3. Set Up Database

#### Option A: Docker (Recommended)

```bash
docker run -d \
  --name postgres-dev \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ai_agent_connector \
  -p 5432:5432 \
  postgres:14
```

#### Option B: Local PostgreSQL

```bash
# Create database
createdb ai_agent_connector
createdb ai_agent_connector_test
```

### 4. Configure Environment

Create `.env` file:

```bash
# .env
FLASK_ENV=development
PORT=5000
HOST=127.0.0.1
SECRET_KEY=dev-secret-key-change-in-production
ENCRYPTION_KEY=your-encryption-key-here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_agent_connector

# Optional: AI Provider Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Optional: Air-gapped mode
AIR_GAPPED_MODE=false
LOCAL_AI_BASE_URL=http://localhost:11434
LOCAL_AI_MODEL=llama2
```

Generate encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 5. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ai_agent_connector --cov-report=html

# Run specific test
pytest tests/test_api_routes.py::test_register_agent
```

### 6. Start Development Server

```bash
python main.py
```

Server should start on `http://127.0.0.1:5000`

## Development Workflow

### Code Formatting

```bash
# Format all Python files
black .

# Check formatting
black --check .

# Format specific file
black ai_agent_connector/app/api/routes.py
```

### Linting

```bash
# Lint all files
flake8 .

# Lint specific file
flake8 ai_agent_connector/app/api/routes.py

# Ignore specific errors
flake8 --ignore=E501,W503 .
```

### Type Checking

```bash
# Type check all files
mypy ai_agent_connector/

# Type check specific file
mypy ai_agent_connector/app/api/routes.py
```

### Running Application

```bash
# Development mode (auto-reload)
python main.py

# With debugger
python -m pdb main.py
```

## IDE Setup

### VS Code

Recommended extensions:

- **Python**: Microsoft Python extension
- **Pylance**: Python language server
- **Black Formatter**: Code formatting
- **Flake8**: Linting
- **Python Test Explorer**: Test runner

**Settings** (`.vscode/settings.json`):

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### PyCharm

1. Open project
2. Configure Python interpreter (venv)
3. Enable pytest
4. Configure code style (PEP 8)
5. Enable inspections

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_api_routes.py

# Specific test
pytest tests/test_api_routes.py::test_register_agent

# With coverage
pytest --cov=ai_agent_connector --cov-report=html

# Verbose output
pytest -v

# Show print statements
pytest -s
```

### Writing Tests

1. Create test file: `tests/test_feature.py`
2. Import pytest and modules
3. Write test functions: `def test_something():`
4. Use fixtures for setup
5. Assert expected behavior

**Example:**

```python
import pytest
from ai_agent_connector.app.api.routes import register_agent

def test_register_agent_success():
    """Test successful agent registration."""
    result = register_agent('test-agent', {'name': 'Test'})
    assert result['agent_id'] == 'test-agent'
    assert 'api_key' in result
```

### Test Database

Tests use a separate test database:

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/ai_agent_connector_test"
pytest
```

## CLI Tool Development

### Setup

```bash
cd cli
npm install
npm link  # For local development
```

### Development

```bash
# Run tests
npm test

# Lint
npm run lint

# Format
npm run format  # If configured
```

### Testing CLI

```bash
# Test locally
aidb test

# Test with local server
aidb query "test query" --url http://localhost:5000
```

## Database Development

### Creating Migrations

If using a migration tool:

```bash
# Create migration
alembic revision -m "add new table"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Database Schema Changes

1. Update models in `ai_agent_connector/app/db/`
2. Create migration (if applicable)
3. Update tests
4. Update documentation

## Debugging

### Python Debugger

```bash
# Run with debugger
python -m pdb main.py

# Set breakpoint in code
import pdb; pdb.set_trace()
```

### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Flask",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal",
      "env": {
        "FLASK_ENV": "development"
      }
    }
  ]
}
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

## Common Tasks

### Adding a New Endpoint

1. Add route in `ai_agent_connector/app/api/routes.py`
2. Add tests in `tests/test_api_routes.py`
3. Update API documentation
4. Add to README if public

### Adding a New Feature

1. Create feature branch
2. Implement feature
3. Add tests
4. Update documentation
5. Submit PR

### Updating Dependencies

```bash
# Update requirements
pip freeze > requirements.txt

# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade package-name
```

## Troubleshooting

### Import Errors

```bash
# Ensure virtual environment is activated
which python  # Should point to venv

# Reinstall dependencies
pip install -r requirements.txt
```

### Database Connection Issues

```bash
# Test connection
psql -h localhost -U postgres -d ai_agent_connector

# Check PostgreSQL is running
pg_isready -h localhost
```

### Port Already in Use

```bash
# Change port
export PORT=5001
python main.py

# Or kill process using port
# Windows
netstat -ano | findstr :5000
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:5000 | xargs kill
```

## Resources

- [Python Style Guide (PEP 8)](https://www.python.org/dev/peps/pep-0008/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Git Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows)

---

**Questions?** Check [CONTRIBUTING.md](../CONTRIBUTING.md) or open an issue!

