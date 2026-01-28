"""
GraphQL API for Universal Agent Connector
"""

from .schema import schema, set_managers
from .routes import graphql_bp

# Alias for backwards compatibility
init_graphql = set_managers

__all__ = ['schema', 'graphql_bp', 'init_graphql', 'set_managers']
