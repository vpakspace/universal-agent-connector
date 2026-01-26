# Code Style Guide

Comprehensive code style guide for AI Agent Connector.

## Python Code Style

### General Principles

- **Readability**: Code should be easy to read and understand
- **Consistency**: Follow project conventions
- **Simplicity**: Prefer simple solutions
- **Documentation**: Document complex logic

### Formatting

#### Line Length

- **Maximum**: 100 characters
- **Soft limit**: 88 characters (black default)
- Break long lines appropriately

```python
# Good
def process_data(
    data: List[Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    pass

# Avoid
def process_data(data: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    pass
```

#### Indentation

- Use 4 spaces (no tabs)
- Align continuation lines properly

```python
# Good
if condition:
    do_something(
        arg1,
        arg2,
        arg3
    )

# Avoid
if condition:
  do_something(arg1, arg2, arg3)
```

#### Blank Lines

- 2 blank lines between top-level definitions
- 1 blank line between methods
- Use blank lines to separate logical sections

```python
import os
import sys

from typing import Dict, List


class MyClass:
    """Class docstring."""
    
    def method1(self):
        pass
    
    def method2(self):
        pass


def function():
    pass
```

### Naming Conventions

#### Variables and Functions

- Use `snake_case`
- Be descriptive
- Avoid abbreviations

```python
# Good
user_count = 10
def get_user_by_id(user_id: str):
    pass

# Avoid
uc = 10
def getUsr(id):
    pass
```

#### Classes

- Use `PascalCase`
- Be descriptive

```python
# Good
class DatabaseConnector:
    pass

class AgentRegistry:
    pass

# Avoid
class db_conn:
    pass
```

#### Constants

- Use `UPPER_SNAKE_CASE`

```python
# Good
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Avoid
maxRetries = 3
default_timeout = 30
```

#### Private Methods/Attributes

- Prefix with single underscore `_`
- Double underscore `__` for name mangling (rarely needed)

```python
class MyClass:
    def __init__(self):
        self._internal_state = {}
    
    def _helper_method(self):
        pass
```

### Imports

#### Import Order

1. Standard library imports
2. Related third-party imports
3. Local application imports

```python
# Standard library
import os
import sys
from typing import Dict, List, Optional

# Third-party
from flask import Flask, request, jsonify
import requests

# Local
from ai_agent_connector.app.api import api_bp
from ai_agent_connector.app.agents import AgentRegistry
```

#### Import Style

- Use absolute imports
- Group imports with blank line
- Sort imports alphabetically

```python
# Good
from ai_agent_connector.app.api.routes import register_agent
from ai_agent_connector.app.agents.registry import AgentRegistry

# Avoid
from ..api.routes import register_agent
from .registry import AgentRegistry
```

### Type Hints

#### Function Signatures

Always use type hints for function parameters and return types:

```python
from typing import Optional, Dict, List, Any

def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent by ID."""
    pass

def process_items(items: List[str]) -> Dict[str, int]:
    """Process list of items."""
    pass
```

#### Complex Types

Use `typing` module for complex types:

```python
from typing import Dict, List, Optional, Union, Tuple

def process_data(
    data: Dict[str, List[int]],
    options: Optional[Dict[str, Any]] = None
) -> Tuple[bool, Optional[str]]:
    pass
```

### Docstrings

#### Google Style

Use Google-style docstrings:

```python
def register_agent(
    agent_id: str,
    config: Dict[str, Any],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Register a new AI agent.
    
    This function registers an agent with the system and generates
    an API key for authentication.
    
    Args:
        agent_id: Unique identifier for the agent. Must be alphanumeric
            and between 3-50 characters.
        config: Agent configuration dictionary containing:
            - name: Agent display name
            - type: Agent type (analytics, etl, etc.)
            - database: Database connection configuration
        api_key: Optional pre-generated API key. If not provided,
            a new key will be generated.
    
    Returns:
        Dictionary containing:
            - agent_id: The registered agent ID
            - api_key: API key for authentication
            - created_at: Timestamp of registration
    
    Raises:
        ValueError: If agent_id is invalid or already exists
        ValidationError: If config is missing required fields
        DatabaseError: If database connection fails
    
    Example:
        >>> config = {
        ...     'name': 'My Agent',
        ...     'type': 'analytics',
        ...     'database': {'type': 'postgresql', ...}
        ... }
        >>> result = register_agent('my-agent', config)
        >>> print(result['api_key'])
        'abc123...'
    """
    pass
```

#### Class Docstrings

```python
class AgentRegistry:
    """
    Registry for managing AI agents.
    
    This class provides methods for registering, retrieving, and
    managing AI agents in the system.
    
    Attributes:
        _agents: Dictionary mapping agent IDs to agent configurations
        _api_keys: Dictionary mapping API keys to agent IDs
    
    Example:
        >>> registry = AgentRegistry()
        >>> registry.register('agent-1', {...})
        >>> agent = registry.get_agent('agent-1')
    """
    pass
```

### Code Organization

#### Function Length

- Keep functions focused and short
- Aim for < 50 lines
- Extract complex logic into helper functions

#### Class Organization

```python
class MyClass:
    """Class docstring."""
    
    # Class variables
    DEFAULT_VALUE = 10
    
    def __init__(self):
        """Initialize instance."""
        # Instance variables
        self._state = {}
    
    # Public methods
    def public_method(self):
        """Public method docstring."""
        pass
    
    # Private methods
    def _private_method(self):
        """Private method docstring."""
        pass
    
    # Magic methods
    def __str__(self):
        return "MyClass"
```

### Error Handling

#### Exception Types

Use appropriate exception types:

```python
# Good
if not agent_id:
    raise ValueError("agent_id is required")

if agent_id in self._agents:
    raise ValueError(f"Agent {agent_id} already exists")

# Avoid
if not agent_id:
    raise Exception("agent_id is required")
```

#### Try-Except Blocks

```python
# Good
try:
    result = self._execute_query(query)
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise RuntimeError(f"Query execution failed: {e}") from e

# Avoid
try:
    result = self._execute_query(query)
except:
    pass  # Never use bare except
```

### Comments

#### When to Comment

- Explain "why", not "what"
- Document complex algorithms
- Note non-obvious behavior
- Mark TODOs and FIXMEs

```python
# Good
# Use exponential backoff to avoid overwhelming the API
# during rate limit errors
delay = min(2 ** retry_count, 60)

# Avoid
# Increment retry count
retry_count += 1
```

#### Comment Style

- Use `#` for inline comments
- Keep comments up to date
- Write in clear English

```python
# Good
# Calculate exponential backoff delay
delay = 2 ** retry_count

# Avoid
# calc delay
delay = 2 ** retry_count
```

## JavaScript/TypeScript (CLI)

### Formatting

- Use 2 spaces for indentation
- Use semicolons
- Use single quotes for strings
- Trailing commas in objects/arrays

```javascript
// Good
const config = {
  url: 'http://localhost:5000',
  apiKey: 'test-key',
};

function processData(data) {
  return data.map(item => item.value);
}

// Avoid
const config = {url:"http://localhost:5000",apiKey:"test-key"}
function processData(data){return data.map(item=>item.value)}
```

### Naming

- Variables/functions: `camelCase`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`

```javascript
// Good
const apiClient = new APIClient();
const MAX_RETRIES = 3;

function getUserById(userId) {
  return users.find(u => u.id === userId);
}

// Avoid
const api_client = new api_client();
const maxRetries = 3;
function get_user_by_id(user_id) {}
```

## Testing Style

### Test Naming

```python
# Good
def test_register_agent_success():
    pass

def test_register_agent_with_invalid_id():
    pass

def test_register_agent_duplicate_id_raises_error():
    pass

# Avoid
def test1():
    pass

def test_agent():
    pass
```

### Test Organization

```python
class TestAgentRegistration:
    """Tests for agent registration."""
    
    def test_successful_registration(self):
        """Test successful agent registration."""
        pass
    
    def test_duplicate_id_error(self):
        """Test error on duplicate agent ID."""
        pass
    
    def test_invalid_config_error(self):
        """Test error on invalid configuration."""
        pass
```

## Tools and Automation

### Black (Formatter)

```bash
# Format all files
black .

# Format specific file
black ai_agent_connector/app/api/routes.py

# Check without formatting
black --check .
```

**Configuration** (`pyproject.toml`):

```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
```

### Flake8 (Linter)

```bash
# Lint all files
flake8 .

# Lint with specific config
flake8 --config=.flake8 .
```

**Configuration** (`.flake8`):

```ini
[flake8]
max-line-length = 100
exclude = 
    .git,
    __pycache__,
    venv,
    .venv
ignore = 
    E203,  # whitespace before ':'
    W503,  # line break before binary operator
```

### MyPy (Type Checker)

```bash
# Type check
mypy ai_agent_connector/

# Type check specific file
mypy ai_agent_connector/app/api/routes.py
```

## Pre-commit Hooks

### Setup

```bash
pip install pre-commit
pre-commit install
```

### Configuration (`.pre-commit-config.yaml`)

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
```

## Code Review Guidelines

### What to Look For

- Code follows style guide
- Type hints are present
- Docstrings are complete
- Tests are included
- Error handling is proper
- No security issues
- Performance considerations

### Review Comments

- Be constructive
- Explain reasoning
- Suggest improvements
- Acknowledge good code

---

**Questions?** Check [CONTRIBUTING.md](../CONTRIBUTING.md) or ask in discussions!

