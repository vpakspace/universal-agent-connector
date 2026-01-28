"""
OntoGuard MCP Tools - Semantic validation tools for AI agents.

This module provides MCP-compatible tool definitions for OntoGuard
semantic validation, enabling AI agents to validate their actions
against OWL ontology rules.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def _get_adapter():
    """Get the OntoGuard adapter (lazy import to avoid circular dependencies)."""
    try:
        from ...security import get_ontoguard_adapter
        return get_ontoguard_adapter()
    except ImportError:
        logger.warning("OntoGuard security module not available")
        return None


def validate_action_tool(
    action: str,
    entity_type: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    MCP Tool: Validate an action against ontology rules.

    This tool allows AI agents to check whether a proposed action
    is permitted according to the semantic rules defined in the
    OWL ontology.

    Args:
        action: The action to validate. Common actions include:
            - 'create': Creating a new entity
            - 'read': Reading/querying entity data
            - 'update': Modifying an existing entity
            - 'delete': Removing an entity
            - 'query': Executing a database query
        entity_type: The type of entity being acted upon (e.g., 'User',
            'Order', 'Product', 'Database', 'Customer')
        context: Additional context for validation. Typically includes:
            - 'role': User's role (e.g., 'Admin', 'Customer', 'Manager')
            - 'user_id': Unique identifier for the user
            - 'approved_by': Approver role for actions requiring approval
            - 'timestamp': When the action is being performed

    Returns:
        Dictionary containing:
            - 'allowed': Boolean indicating if action is permitted
            - 'reason': Human-readable explanation of the result
            - 'constraints': List of constraints that were checked
            - 'suggestions': List of alternative allowed actions (if denied)
            - 'metadata': Additional information about the validation

    Example:
        >>> result = validate_action_tool(
        ...     action='delete',
        ...     entity_type='User',
        ...     context={'role': 'Customer', 'user_id': '123'}
        ... )
        >>> result['allowed']
        False
        >>> result['reason']
        "Action 'delete' requires role 'Admin', but user has role 'Customer'"
    """
    adapter = _get_adapter()

    if adapter is None:
        return {
            'allowed': True,
            'reason': 'OntoGuard not available (pass-through mode)',
            'constraints': [],
            'suggestions': [],
            'metadata': {'mode': 'pass_through'}
        }

    context = context or {}
    result = adapter.validate_action(action, entity_type, context)

    return {
        'allowed': result.allowed,
        'reason': result.reason,
        'constraints': result.constraints,
        'suggestions': result.suggestions,
        'metadata': result.metadata
    }


def check_permissions_tool(
    role: str,
    action: str,
    entity_type: str
) -> Dict[str, Any]:
    """
    MCP Tool: Check if a role has permission for an action.

    This tool provides a simple boolean check for whether a given
    role has permission to perform a specific action on an entity type.

    Args:
        role: User role to check. Common roles include:
            - 'Admin': Full system access
            - 'Manager': Limited administrative access
            - 'Customer': Standard user access
            - 'Guest': Minimal read-only access
        action: The action to check permission for
        entity_type: The entity type to check against

    Returns:
        Dictionary containing:
            - 'role': The role that was checked
            - 'action': The action that was checked
            - 'entity_type': The entity type that was checked
            - 'allowed': Boolean indicating if permission is granted

    Example:
        >>> result = check_permissions_tool('Admin', 'delete', 'User')
        >>> result['allowed']
        True
        >>> result = check_permissions_tool('Customer', 'delete', 'User')
        >>> result['allowed']
        False
    """
    adapter = _get_adapter()

    if adapter is None:
        return {
            'role': role,
            'action': action,
            'entity_type': entity_type,
            'allowed': True,
            'reason': 'OntoGuard not available (all permissions granted)'
        }

    allowed = adapter.check_permissions(role, action, entity_type)

    return {
        'role': role,
        'action': action,
        'entity_type': entity_type,
        'allowed': allowed
    }


def get_allowed_actions_tool(
    role: str,
    entity_type: str
) -> Dict[str, Any]:
    """
    MCP Tool: Get list of allowed actions for a role.

    This tool retrieves all actions that a specific role is permitted
    to perform on a given entity type according to the ontology rules.

    Args:
        role: User role to query actions for
        entity_type: The entity type to query

    Returns:
        Dictionary containing:
            - 'role': The role that was queried
            - 'entity_type': The entity type that was queried
            - 'allowed_actions': List of action names that are permitted

    Example:
        >>> result = get_allowed_actions_tool('Customer', 'Order')
        >>> result['allowed_actions']
        ['create', 'read', 'update', 'cancel']
    """
    adapter = _get_adapter()

    if adapter is None:
        return {
            'role': role,
            'entity_type': entity_type,
            'allowed_actions': ['*'],
            'reason': 'OntoGuard not available (all actions allowed)'
        }

    actions = adapter.get_allowed_actions(role, entity_type)

    return {
        'role': role,
        'entity_type': entity_type,
        'allowed_actions': actions
    }


def explain_rule_tool(
    action: str,
    entity_type: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    MCP Tool: Get detailed explanation of validation rules.

    This tool provides a human-readable explanation of the ontology
    rules that apply to a specific action and entity type combination,
    helpful for understanding why an action was denied or what
    conditions need to be met.

    Args:
        action: The action to explain rules for
        entity_type: The entity type to explain rules for
        context: Optional context for the explanation

    Returns:
        Dictionary containing:
            - 'action': The action that was explained
            - 'entity_type': The entity type that was explained
            - 'explanation': Human-readable explanation of applicable rules

    Example:
        >>> result = explain_rule_tool('delete', 'User', {'role': 'Customer'})
        >>> print(result['explanation'])
        ❌ Action 'delete' is not permitted for role 'Customer'.
           This action requires the 'Admin' role.

        💡 Suggested alternatives:
           - read
           - update (with approval)
    """
    adapter = _get_adapter()

    if adapter is None:
        return {
            'action': action,
            'entity_type': entity_type,
            'explanation': 'OntoGuard not active - all actions are allowed by default.'
        }

    context = context or {}
    explanation = adapter.explain_rule(action, entity_type, context)

    return {
        'action': action,
        'entity_type': entity_type,
        'explanation': explanation
    }


def get_ontoguard_status_tool() -> Dict[str, Any]:
    """
    MCP Tool: Get OntoGuard status and configuration.

    This tool returns the current status of the OntoGuard semantic
    firewall, including whether it's active and what ontologies
    are loaded.

    Returns:
        Dictionary containing:
            - 'enabled': Whether OntoGuard is initialized
            - 'active': Whether OntoGuard is actively validating
            - 'pass_through_mode': Whether in pass-through mode
            - 'ontology_paths': List of loaded ontology file paths

    Example:
        >>> result = get_ontoguard_status_tool()
        >>> result['active']
        True
        >>> result['ontology_paths']
        ['ontologies/ecommerce.owl']
    """
    adapter = _get_adapter()

    if adapter is None:
        return {
            'enabled': False,
            'active': False,
            'pass_through_mode': True,
            'ontology_paths': [],
            'reason': 'OntoGuard module not available'
        }

    return {
        'enabled': adapter._initialized,
        'active': adapter.is_active,
        'pass_through_mode': adapter._pass_through_mode,
        'ontology_paths': adapter.ontology_paths
    }


# Tool definitions for MCP registration
ONTOGUARD_TOOLS: List[Dict[str, Any]] = [
    {
        'name': 'ontoguard_validate_action',
        'description': (
            'Validate an action against semantic ontology rules. '
            'Use this tool to check if an AI agent action is permitted '
            'according to business rules defined in OWL ontologies.'
        ),
        'function': validate_action_tool,
        'parameters': {
            'type': 'object',
            'properties': {
                'action': {
                    'type': 'string',
                    'description': 'The action to validate (create, read, update, delete, query)',
                    'enum': ['create', 'read', 'update', 'delete', 'query', 'execute']
                },
                'entity_type': {
                    'type': 'string',
                    'description': 'The entity type being acted upon (e.g., User, Order, Product)'
                },
                'context': {
                    'type': 'object',
                    'description': 'Additional context including role, user_id, etc.',
                    'properties': {
                        'role': {'type': 'string'},
                        'user_id': {'type': 'string'},
                        'approved_by': {'type': 'string'}
                    }
                }
            },
            'required': ['action', 'entity_type']
        }
    },
    {
        'name': 'ontoguard_check_permissions',
        'description': (
            'Check if a role has permission for a specific action. '
            'Quick boolean check for role-based access control.'
        ),
        'function': check_permissions_tool,
        'parameters': {
            'type': 'object',
            'properties': {
                'role': {
                    'type': 'string',
                    'description': 'User role (e.g., Admin, Manager, Customer)'
                },
                'action': {
                    'type': 'string',
                    'description': 'The action to check'
                },
                'entity_type': {
                    'type': 'string',
                    'description': 'The entity type'
                }
            },
            'required': ['role', 'action', 'entity_type']
        }
    },
    {
        'name': 'ontoguard_get_allowed_actions',
        'description': (
            'Get list of allowed actions for a role on an entity type. '
            'Useful for discovering what operations are permitted.'
        ),
        'function': get_allowed_actions_tool,
        'parameters': {
            'type': 'object',
            'properties': {
                'role': {
                    'type': 'string',
                    'description': 'User role to query'
                },
                'entity_type': {
                    'type': 'string',
                    'description': 'Entity type to query'
                }
            },
            'required': ['role', 'entity_type']
        }
    },
    {
        'name': 'ontoguard_explain_rule',
        'description': (
            'Get detailed explanation of validation rules. '
            'Human-readable explanation of why an action is allowed or denied.'
        ),
        'function': explain_rule_tool,
        'parameters': {
            'type': 'object',
            'properties': {
                'action': {
                    'type': 'string',
                    'description': 'The action to explain'
                },
                'entity_type': {
                    'type': 'string',
                    'description': 'The entity type'
                },
                'context': {
                    'type': 'object',
                    'description': 'Optional context for explanation'
                }
            },
            'required': ['action', 'entity_type']
        }
    },
    {
        'name': 'ontoguard_status',
        'description': (
            'Get OntoGuard status and configuration. '
            'Check if semantic validation is active and what ontologies are loaded.'
        ),
        'function': get_ontoguard_status_tool,
        'parameters': {
            'type': 'object',
            'properties': {}
        }
    }
]
