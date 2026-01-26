"""
Universal Agent Connector Python SDK

Official Python SDK for the Universal Agent Connector API.
Provides easy integration with AI agent management, database connections, and query execution.
"""

from .client import UniversalAgentConnector
from .exceptions import (
    UniversalAgentConnectorError,
    APIError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError
)

__version__ = "0.1.0"
__all__ = [
    'UniversalAgentConnector',
    'UniversalAgentConnectorError',
    'APIError',
    'AuthenticationError',
    'NotFoundError',
    'ValidationError',
    'RateLimitError'
]
