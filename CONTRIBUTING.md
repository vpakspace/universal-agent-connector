# Contributing to AI Agent Connector

Thank you for your interest in contributing to AI Agent Connector! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guide](#code-style-guide)
- [Making Changes](#making-changes)
- [Submitting Pull Requests](#submitting-pull-requests)
- [Testing](#testing)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)

## 🤝 Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please be respectful, inclusive, and constructive in all interactions.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 14+ (for CLI tool)
- PostgreSQL (for testing)
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/ai-agent-connector.git
   cd ai-agent-connector
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/original-repo/ai-agent-connector.git
   ```

## 💻 Development Setup

### Python Environment

1. Create virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate virtual environment:
   ```bash
   # Windows
   .\venv\Scripts\Activate.ps1
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If exists
   ```

4. Install development dependencies:
   ```bash
   pip install pytest pytest-cov black flake8 mypy
   ```

### Database Setup

1. Install PostgreSQL (or use Docker):
   ```bash
   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:14
   ```

2. Create test databases:
   ```bash
   createdb ai_agent_connector_test
   ```

3. Set environment variables:
   ```bash
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/ai_agent_connector_test"
   export ENCRYPTION_KEY="test-key-for-development"
   ```

### CLI Tool Setup (Optional)

If contributing to the CLI tool:

```bash
cd cli
npm install
npm link  # For local development
```

### Verify Setup

Run tests to verify everything works:

```bash
pytest tests/ -v
```

## 📝 Code Style Guide

### Python Code Style

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

#### Formatting

- **Line length**: 100 characters (not 79)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Use double quotes for strings
- **Imports**: Grouped and sorted (stdlib, third-party, local)

#### Code Formatting Tools

We use `black` for automatic formatting:

```bash
# Format all Python files
black .

# Format specific file
black ai_agent_connector/app/api/routes.py

# Check without formatting
black --check .
```

#### Linting

We use `flake8` for linting:

```bash
# Lint all files
flake8 .

# Lint specific file
flake8 ai_agent_connector/app/api/routes.py
```

#### Type Hints

We use type hints for better code clarity:

```python
from typing import Optional, Dict, List

def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent by ID."""
    return agent_registry.get(agent_id)
```

#### Docstrings

Use Google-style docstrings:

```python
def register_agent(agent_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Register a new AI agent.
    
    Args:
        agent_id: Unique identifier for the agent
        config: Agent configuration dictionary
        
    Returns:
        Dictionary containing agent information and API key
        
    Raises:
        ValueError: If agent_id already exists
        ValidationError: If config is invalid
    """
    pass
```

### JavaScript/TypeScript Code Style (CLI)

For CLI tool contributions:

- Use ESLint configuration
- Follow Airbnb JavaScript Style Guide
- Use Prettier for formatting

```bash
cd cli
npm run lint
npm run format  # If configured
```

### File Naming

- **Python files**: `snake_case.py`
- **Test files**: `test_*.py`
- **Configuration files**: `UPPER_CASE` or `kebab-case`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): Add widget export endpoint

Add new endpoint for exporting widget configurations
with validation and error handling.

Closes #123
```

```
fix(auth): Fix API key validation bug

API key validation was failing for keys with special
characters. Updated regex pattern to handle all valid
characters.

Fixes #456
```

## 🔨 Making Changes

### Branch Naming

Use descriptive branch names:

- `feat/add-widget-export`
- `fix/permission-validation`
- `docs/update-api-docs`
- `refactor/improve-error-handling`

### Workflow

1. **Create a branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes**:
   - Write code
   - Add tests
   - Update documentation

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat(api): Add new endpoint"
   ```

4. **Keep your branch updated**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

5. **Push to your fork**:
   ```bash
   git push origin feat/your-feature-name
   ```

### Code Review Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guide
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No linter errors
- [ ] Type hints added (Python)
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with main

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api_routes.py

# Run with coverage
pytest --cov=ai_agent_connector --cov-report=html

# Run specific test
pytest tests/test_api_routes.py::test_register_agent
```

### Writing Tests

- Use `pytest` framework
- Follow naming: `test_*.py`
- Use descriptive test names
- Include docstrings for complex tests

**Example:**
```python
def test_register_agent_success(client, mock_agent_registry):
    """Test successful agent registration."""
    response = client.post('/api/agents/register', json={
        'agent_id': 'test-agent',
        'agent_info': {'name': 'Test Agent'}
    })
    assert response.status_code == 201
    assert 'api_key' in response.json()
```

### Test Coverage

- Aim for 80%+ coverage
- Cover edge cases
- Test error paths
- Test validation

## 📚 Documentation

### Code Documentation

- Add docstrings to all public functions/classes
- Include type hints
- Document complex logic
- Add inline comments for non-obvious code

### User Documentation

- Update README.md if needed
- Add examples
- Update API documentation
- Add to relevant guides

### Documentation Files

- `README.md` - Main documentation
- `docs/` - Additional documentation
- Docstrings in code
- API documentation

## 🐛 Issue Reporting

### Before Reporting

1. Check existing issues
2. Verify it's a bug (not expected behavior)
3. Try to reproduce
4. Check documentation

### Bug Report Template

```markdown
**Description**
Clear description of the bug

**Steps to Reproduce**
1. Step one
2. Step two
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Windows 10]
- Python: [e.g., 3.11.0]
- Version: [e.g., 0.1.0]

**Additional Context**
Screenshots, logs, etc.
```

### Feature Request Template

```markdown
**Feature Description**
Clear description of the feature

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should it work?

**Alternatives Considered**
Other approaches you've thought about

**Additional Context**
Any other relevant information
```

## 🔄 Submitting Pull Requests

### PR Checklist

- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Documentation updated
- [ ] No linter errors
- [ ] Commit messages follow conventions
- [ ] PR description is clear
- [ ] Related issues referenced

### PR Description Template

Use the PR template (see `.github/pull_request_template.md`) or include:

1. **Description**: What changes were made
2. **Type**: Feature, bug fix, docs, etc.
3. **Testing**: How it was tested
4. **Screenshots**: If UI changes
5. **Related Issues**: Link to issues

### Review Process

1. **Automated Checks**: CI runs tests and linting
2. **Code Review**: Maintainers review code
3. **Feedback**: Address any feedback
4. **Approval**: Once approved, PR is merged

### After Merge

- Delete your branch
- Update your fork
- Celebrate! 🎉

## 📖 Key Documentation

- **[ARCHITECTURE](docs/ARCHITECTURE.md)** — System design, components, data flow, and extension points
- **[API Reference](docs/API.md)** — REST and GraphQL endpoint reference
- **[README](README.md)** — Overview, quick start, and usage

## 🏗️ Project Structure

Understanding the project structure helps with contributions:

```
ai_agent_connector/
├── app/                    # Core application
│   ├── api/                # API endpoints
│   ├── agents/            # Agent management
│   ├── db/                # Database connectors
│   ├── permissions/       # Access control
│   └── utils/             # Utilities
├── tests/                 # Test files
├── docs/                  # Documentation
├── cli/                   # CLI tool
├── templates/             # HTML templates
└── static/                # Static files
```

## 🎯 Areas for Contribution

### Good First Issues

Look for issues labeled:
- `good first issue`
- `help wanted`
- `documentation`

### Contribution Areas

- **Bug Fixes**: Fix reported bugs
- **Features**: Implement new features
- **Documentation**: Improve docs
- **Tests**: Add test coverage
- **Performance**: Optimize code
- **Security**: Security improvements
- **Examples**: Add examples/demos

## 📞 Getting Help

- **Documentation**: Check README and docs/
- **Issues**: Search existing issues
- **Discussions**: Use GitHub Discussions
- **Community**: Join our community channels

## 🙏 Thank You!

Thank you for contributing to AI Agent Connector! Your contributions make this project better for everyone.

---

**Questions?** Open an issue or start a discussion!
