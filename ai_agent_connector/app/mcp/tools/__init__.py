"""
MCP Tools module.

This module provides MCP tool definitions for various functionalities
including OntoGuard semantic validation.
"""

from .ontoguard_tools import (
    ONTOGUARD_TOOLS,
    validate_action_tool,
    check_permissions_tool,
    get_allowed_actions_tool,
    explain_rule_tool
)

__all__ = [
    'ONTOGUARD_TOOLS',
    'validate_action_tool',
    'check_permissions_tool',
    'get_allowed_actions_tool',
    'explain_rule_tool'
]
