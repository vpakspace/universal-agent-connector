"""
WebSocket handlers for real-time OntoGuard validation.

This module provides WebSocket endpoints for:
- Real-time action validation
- Permission checks
- Allowed actions queries
- Rule explanations
- Validation streaming for batch operations

Events:
    Client -> Server:
        - validate_action: Validate a single action
        - check_permissions: Check if role has permission
        - get_allowed_actions: Get list of allowed actions
        - explain_rule: Get rule explanation
        - validate_batch: Validate multiple actions
        - subscribe_validation: Subscribe to validation events for an agent
        - unsubscribe_validation: Unsubscribe from validation events

    Server -> Client:
        - validation_result: Result of action validation
        - permission_result: Result of permission check
        - allowed_actions_result: List of allowed actions
        - rule_explanation: Rule explanation text
        - batch_result: Results of batch validation
        - validation_event: Real-time validation event (for subscribed agents)
        - schema_drift_detected: Schema drift alert (CRITICAL/WARNING severity)
        - error: Error message
"""

import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime, timezone
from functools import wraps

from flask_socketio import SocketIO, emit, join_room, leave_room

# Domain configuration
from ..config.domains import (
    get_domain_config,
    get_entity_from_table,
    get_ontology_path,
    is_valid_role,
    detect_domain_from_ontology,
    DEFAULT_DOMAIN,
)

logger = logging.getLogger(__name__)

# Current domain for WebSocket session
_current_domain: str = DEFAULT_DOMAIN

# Global SocketIO instance
_socketio: Optional[SocketIO] = None

# Connected clients tracking
_connected_clients: Dict[str, Dict[str, Any]] = {}

# Agent validation subscriptions (agent_id -> set of session_ids)
_agent_subscriptions: Dict[str, Set[str]] = {}


def _resolve_entity_type(data: Dict[str, Any]) -> str:
    """
    Resolve entity type from data, supporting table-to-entity mapping.

    Args:
        data: Request data containing entity_type and/or table, domain

    Returns:
        Resolved OWL entity type
    """
    entity_type = data.get('entity_type')
    table = data.get('table')
    domain = data.get('context', {}).get('domain') or data.get('domain') or _current_domain

    # If table provided, try to map to entity
    if table and not entity_type:
        entity_type = get_entity_from_table(table, domain)
        if entity_type:
            logger.debug(f"Mapped table '{table}' to entity '{entity_type}' for domain '{domain}'")

    return entity_type or table or 'Unknown'


def _validate_role_for_domain(role: str, domain: str) -> Optional[str]:
    """
    Validate that role exists in domain, return error message if not.

    Args:
        role: Role to validate
        domain: Domain name

    Returns:
        Error message if invalid, None if valid
    """
    if not role:
        return None  # No role specified, skip validation

    if not is_valid_role(role, domain):
        config = get_domain_config(domain)
        valid_roles = config.roles if config else []
        return f"Role '{role}' is not valid for domain '{domain}'. Valid roles: {valid_roles}"

    return None


def _switch_ontology_if_needed(domain: str) -> bool:
    """
    Switch OntoGuard ontology if domain changed.

    Args:
        domain: Target domain

    Returns:
        True if switch was successful or not needed
    """
    global _current_domain

    if domain == _current_domain:
        return True

    ontology_path = get_ontology_path(domain)
    if not ontology_path:
        logger.warning(f"No ontology path found for domain '{domain}'")
        return False

    try:
        from ..security import get_ontoguard_adapter

        adapter = get_ontoguard_adapter()
        if adapter.initialize([ontology_path]):
            _current_domain = domain
            logger.info(f"Switched OntoGuard to domain '{domain}' with ontology: {ontology_path}")
            return True
        else:
            logger.error(f"Failed to switch to domain '{domain}'")
            return False

    except Exception as e:
        logger.error(f"Error switching ontology: {e}")
        return False


def get_current_domain() -> str:
    """Get current active domain."""
    return _current_domain


def get_socketio() -> Optional[SocketIO]:
    """Get the global SocketIO instance."""
    return _socketio


def emit_validation_event(agent_id: str, event_data: Dict[str, Any]) -> None:
    """
    Emit a validation event to all subscribers of an agent.

    Args:
        agent_id: The agent ID to emit the event for
        event_data: The event data to emit
    """
    if _socketio is None:
        return

    room = f"agent_{agent_id}"
    _socketio.emit('validation_event', {
        'agent_id': agent_id,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        **event_data
    }, room=room)


def emit_schema_drift_event(drift_report: Dict[str, Any], fixes: list = None) -> None:
    """
    Emit a schema drift event to all connected clients.

    This is the real-time notification for the $4.6M mistake prevention system.
    Called when schema drift is detected during query validation.

    Args:
        drift_report: DriftReport as dict with entity, table, missing_columns, etc.
        fixes: List of suggested fixes
    """
    if _socketio is None:
        return

    event_data = {
        'type': 'schema_drift_detected',
        'severity': drift_report.get('severity', 'INFO'),
        'entity': drift_report.get('entity'),
        'table': drift_report.get('table'),
        'message': drift_report.get('message'),
        'missing_columns': drift_report.get('missing_columns', []),
        'new_columns': drift_report.get('new_columns', []),
        'type_changes': drift_report.get('type_changes', {}),
        'renamed_columns': drift_report.get('renamed_columns', {}),
        'suggested_fixes': [f.get('description') if isinstance(f, dict) else str(f) for f in (fixes or [])],
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }

    # Broadcast to all connected clients
    _socketio.emit('schema_drift_detected', event_data)

    logger.info(
        "Schema drift event emitted: %s severity for entity '%s'",
        event_data['severity'],
        event_data['entity']
    )


def require_initialized(f):
    """Decorator to ensure OntoGuard is initialized before handling events."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import request
        from ..security import get_ontoguard_adapter

        adapter = get_ontoguard_adapter()
        if not adapter._initialized:
            emit('error', {
                'code': 'NOT_INITIALIZED',
                'message': 'OntoGuard is not initialized',
                'event': f.__name__
            })
            return
        return f(*args, **kwargs)
    return wrapper


def register_websocket_handlers(socketio: SocketIO) -> None:
    """
    Register all WebSocket event handlers.

    Args:
        socketio: The Flask-SocketIO instance
    """
    global _socketio
    _socketio = socketio

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        from flask import request

        session_id = request.sid
        _connected_clients[session_id] = {
            'connected_at': datetime.now(timezone.utc).isoformat(),
            'subscriptions': set()
        }

        logger.info(f"WebSocket client connected: {session_id}")

        emit('connected', {
            'session_id': session_id,
            'message': 'Connected to OntoGuard WebSocket'
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        from flask import request

        session_id = request.sid

        # Clean up subscriptions
        if session_id in _connected_clients:
            for agent_id in _connected_clients[session_id].get('subscriptions', set()):
                if agent_id in _agent_subscriptions:
                    _agent_subscriptions[agent_id].discard(session_id)
                    if not _agent_subscriptions[agent_id]:
                        del _agent_subscriptions[agent_id]

            del _connected_clients[session_id]

        logger.info(f"WebSocket client disconnected: {session_id}")

    @socketio.on('validate_action')
    @require_initialized
    def handle_validate_action(data: Dict[str, Any]):
        """
        Handle action validation request.

        Expected data:
            action: str - The action to validate (e.g., "create", "read", "update", "delete")
            entity_type: str - The entity type (e.g., "User", "Order") OR
            table: str - SQL table name (auto-mapped to entity_type)
            context: dict - Additional context:
                - role: User role
                - domain: Domain name (hospital/finance) for ontology selection
                - user_id, agent_id, etc.
            request_id: str (optional) - Client request ID for correlation
        """
        from ..security import get_ontoguard_adapter

        try:
            action = data.get('action')
            context = data.get('context', {})
            request_id = data.get('request_id')

            # Get domain from context or use current
            domain = context.get('domain') or data.get('domain') or _current_domain

            # Switch ontology if domain changed
            if not _switch_ontology_if_needed(domain):
                emit('error', {
                    'code': 'DOMAIN_SWITCH_FAILED',
                    'message': f"Failed to switch to domain '{domain}'",
                    'request_id': request_id
                })
                return

            # Resolve entity type (supports table-to-entity mapping)
            entity_type = _resolve_entity_type(data)

            if not action or entity_type == 'Unknown':
                emit('error', {
                    'code': 'INVALID_REQUEST',
                    'message': 'action and (entity_type or table) are required',
                    'request_id': request_id
                })
                return

            # Validate role for domain
            role = context.get('role')
            role_error = _validate_role_for_domain(role, domain)
            if role_error:
                emit('error', {
                    'code': 'INVALID_ROLE',
                    'message': role_error,
                    'domain': domain,
                    'request_id': request_id
                })
                return

            adapter = get_ontoguard_adapter()
            result = adapter.validate_action(action, entity_type, context)

            response = {
                'allowed': result.allowed,
                'action': action,
                'entity_type': entity_type,
                'domain': domain,
                'role': role,
                'reason': result.reason,
                'constraints': result.constraints,
                'suggestions': result.suggestions,
                'metadata': result.metadata,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            if request_id:
                response['request_id'] = request_id

            emit('validation_result', response)

            # Emit to subscribers if agent_id in context
            agent_id = context.get('agent_id')
            if agent_id:
                emit_validation_event(agent_id, {
                    'type': 'validation',
                    'action': action,
                    'entity_type': entity_type,
                    'result': result.to_dict()
                })

            logger.debug(f"Validation: {action} on {entity_type} -> {result.allowed}")

        except Exception as e:
            logger.error(f"Validation error: {e}")
            emit('error', {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'request_id': data.get('request_id')
            })

    @socketio.on('check_permissions')
    @require_initialized
    def handle_check_permissions(data: Dict[str, Any]):
        """
        Handle permission check request.

        Expected data:
            role: str - The user role
            action: str - The action to check
            entity_type: str - The entity type OR
            table: str - SQL table name (auto-mapped)
            domain: str (optional) - Domain for ontology selection
            request_id: str (optional) - Client request ID
        """
        from ..security import get_ontoguard_adapter

        try:
            role = data.get('role')
            action = data.get('action')
            request_id = data.get('request_id')
            domain = data.get('domain') or _current_domain

            # Switch ontology if needed
            _switch_ontology_if_needed(domain)

            # Resolve entity type
            entity_type = _resolve_entity_type(data)

            if not all([role, action]) or entity_type == 'Unknown':
                emit('error', {
                    'code': 'INVALID_REQUEST',
                    'message': 'role, action, and (entity_type or table) are required',
                    'request_id': request_id
                })
                return

            # Validate role for domain
            role_error = _validate_role_for_domain(role, domain)
            if role_error:
                emit('error', {
                    'code': 'INVALID_ROLE',
                    'message': role_error,
                    'domain': domain,
                    'request_id': request_id
                })
                return

            adapter = get_ontoguard_adapter()
            allowed = adapter.check_permissions(role, action, entity_type)

            response = {
                'allowed': allowed,
                'role': role,
                'action': action,
                'entity_type': entity_type,
                'domain': domain,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            if request_id:
                response['request_id'] = request_id

            emit('permission_result', response)

        except Exception as e:
            logger.error(f"Permission check error: {e}")
            emit('error', {
                'code': 'PERMISSION_CHECK_ERROR',
                'message': str(e),
                'request_id': data.get('request_id')
            })

    @socketio.on('get_allowed_actions')
    @require_initialized
    def handle_get_allowed_actions(data: Dict[str, Any]):
        """
        Handle get allowed actions request.

        Expected data:
            role: str - The user role
            entity_type: str - The entity type OR
            table: str - SQL table name (auto-mapped)
            domain: str (optional) - Domain for ontology selection
            request_id: str (optional) - Client request ID
        """
        from ..security import get_ontoguard_adapter

        try:
            role = data.get('role')
            request_id = data.get('request_id')
            domain = data.get('domain') or _current_domain

            # Switch ontology if needed
            _switch_ontology_if_needed(domain)

            # Resolve entity type
            entity_type = _resolve_entity_type(data)

            if not role or entity_type == 'Unknown':
                emit('error', {
                    'code': 'INVALID_REQUEST',
                    'message': 'role and (entity_type or table) are required',
                    'request_id': request_id
                })
                return

            adapter = get_ontoguard_adapter()
            actions = adapter.get_allowed_actions(role, entity_type)

            response = {
                'role': role,
                'entity_type': entity_type,
                'domain': domain,
                'allowed_actions': actions,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            if request_id:
                response['request_id'] = request_id

            emit('allowed_actions_result', response)

        except Exception as e:
            logger.error(f"Get allowed actions error: {e}")
            emit('error', {
                'code': 'GET_ALLOWED_ACTIONS_ERROR',
                'message': str(e),
                'request_id': data.get('request_id')
            })

    @socketio.on('explain_rule')
    @require_initialized
    def handle_explain_rule(data: Dict[str, Any]):
        """
        Handle rule explanation request.

        Expected data:
            action: str - The action to explain
            entity_type: str - The entity type OR
            table: str - SQL table name (auto-mapped)
            context: dict - Additional context:
                - role: User role (for domain validation)
                - domain: Domain name (hospital/finance)
            domain: str (optional) - Domain for ontology selection (alternative to context.domain)
            request_id: str (optional) - Client request ID
        """
        from ..security import get_ontoguard_adapter

        try:
            action = data.get('action')
            context = data.get('context', {})
            request_id = data.get('request_id')
            domain = context.get('domain') or data.get('domain') or _current_domain

            # Switch ontology if needed
            if not _switch_ontology_if_needed(domain):
                emit('error', {
                    'code': 'DOMAIN_SWITCH_FAILED',
                    'message': f"Failed to switch to domain '{domain}'",
                    'request_id': request_id
                })
                return

            # Resolve entity type (supports table-to-entity mapping)
            entity_type = _resolve_entity_type(data)

            if not action or entity_type == 'Unknown':
                emit('error', {
                    'code': 'INVALID_REQUEST',
                    'message': 'action and (entity_type or table) are required',
                    'request_id': request_id
                })
                return

            # Validate role if provided
            role = context.get('role')
            role_error = _validate_role_for_domain(role, domain)
            if role_error:
                emit('error', {
                    'code': 'INVALID_ROLE',
                    'message': role_error,
                    'domain': domain,
                    'request_id': request_id
                })
                return

            adapter = get_ontoguard_adapter()
            explanation = adapter.explain_rule(action, entity_type, context)

            response = {
                'action': action,
                'entity_type': entity_type,
                'domain': domain,
                'role': role,
                'explanation': explanation,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            if request_id:
                response['request_id'] = request_id

            emit('rule_explanation', response)

        except Exception as e:
            logger.error(f"Explain rule error: {e}")
            emit('error', {
                'code': 'EXPLAIN_RULE_ERROR',
                'message': str(e),
                'request_id': data.get('request_id')
            })

    @socketio.on('validate_batch')
    @require_initialized
    def handle_validate_batch(data: Dict[str, Any]):
        """
        Handle batch validation request with domain support.

        Expected data:
            domain: str (optional) - Default domain for all validations
            validations: list - List of validation requests, each containing:
                - action: str
                - entity_type: str OR table: str (auto-mapped)
                - context: dict (optional) - may include domain override, role
            request_id: str (optional) - Client request ID
        """
        from ..security import get_ontoguard_adapter

        try:
            validations = data.get('validations', [])
            request_id = data.get('request_id')
            default_domain = data.get('domain') or _current_domain

            if not validations:
                emit('error', {
                    'code': 'INVALID_REQUEST',
                    'message': 'validations list is required',
                    'request_id': request_id
                })
                return

            adapter = get_ontoguard_adapter()
            results = []
            current_batch_domain = default_domain

            for i, validation in enumerate(validations):
                action = validation.get('action')
                context = validation.get('context', {})

                # Get domain for this validation (context overrides default)
                item_domain = context.get('domain') or validation.get('domain') or default_domain

                # Switch ontology if domain changed
                if item_domain != current_batch_domain:
                    if not _switch_ontology_if_needed(item_domain):
                        results.append({
                            'index': i,
                            'error': f"Failed to switch to domain '{item_domain}'"
                        })
                        continue
                    current_batch_domain = item_domain

                # Resolve entity type (supports table-to-entity mapping)
                entity_type = _resolve_entity_type(validation)

                if not action or entity_type == 'Unknown':
                    results.append({
                        'index': i,
                        'error': 'action and (entity_type or table) are required'
                    })
                    continue

                # Validate role for domain
                role = context.get('role')
                role_error = _validate_role_for_domain(role, item_domain)
                if role_error:
                    results.append({
                        'index': i,
                        'error': role_error,
                        'domain': item_domain
                    })
                    continue

                result = adapter.validate_action(action, entity_type, context)
                results.append({
                    'index': i,
                    'action': action,
                    'entity_type': entity_type,
                    'domain': item_domain,
                    'role': role,
                    'allowed': result.allowed,
                    'reason': result.reason,
                    'constraints': result.constraints,
                    'suggestions': result.suggestions
                })

            response = {
                'results': results,
                'default_domain': default_domain,
                'total': len(validations),
                'allowed_count': sum(1 for r in results if r.get('allowed', False)),
                'denied_count': sum(1 for r in results if not r.get('allowed', True) and 'error' not in r),
                'error_count': sum(1 for r in results if 'error' in r),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            if request_id:
                response['request_id'] = request_id

            emit('batch_result', response)

        except Exception as e:
            logger.error(f"Batch validation error: {e}")
            emit('error', {
                'code': 'BATCH_VALIDATION_ERROR',
                'message': str(e),
                'request_id': data.get('request_id')
            })

    @socketio.on('subscribe_validation')
    def handle_subscribe_validation(data: Dict[str, Any]):
        """
        Subscribe to validation events for a specific agent.

        Expected data:
            agent_id: str - The agent ID to subscribe to
        """
        from flask import request

        agent_id = data.get('agent_id')

        if not agent_id:
            emit('error', {
                'code': 'INVALID_REQUEST',
                'message': 'agent_id is required'
            })
            return

        session_id = request.sid
        room = f"agent_{agent_id}"

        # Join the room for this agent
        join_room(room)

        # Track subscription
        if agent_id not in _agent_subscriptions:
            _agent_subscriptions[agent_id] = set()
        _agent_subscriptions[agent_id].add(session_id)

        if session_id in _connected_clients:
            _connected_clients[session_id]['subscriptions'].add(agent_id)

        logger.info(f"Client {session_id} subscribed to agent {agent_id}")

        emit('subscribed', {
            'agent_id': agent_id,
            'message': f'Subscribed to validation events for agent {agent_id}'
        })

    @socketio.on('unsubscribe_validation')
    def handle_unsubscribe_validation(data: Dict[str, Any]):
        """
        Unsubscribe from validation events for a specific agent.

        Expected data:
            agent_id: str - The agent ID to unsubscribe from
        """
        from flask import request

        agent_id = data.get('agent_id')

        if not agent_id:
            emit('error', {
                'code': 'INVALID_REQUEST',
                'message': 'agent_id is required'
            })
            return

        session_id = request.sid
        room = f"agent_{agent_id}"

        # Leave the room
        leave_room(room)

        # Update tracking
        if agent_id in _agent_subscriptions:
            _agent_subscriptions[agent_id].discard(session_id)
            if not _agent_subscriptions[agent_id]:
                del _agent_subscriptions[agent_id]

        if session_id in _connected_clients:
            _connected_clients[session_id]['subscriptions'].discard(agent_id)

        logger.info(f"Client {session_id} unsubscribed from agent {agent_id}")

        emit('unsubscribed', {
            'agent_id': agent_id,
            'message': f'Unsubscribed from validation events for agent {agent_id}'
        })

    @socketio.on('get_status')
    def handle_get_status(data: Dict[str, Any] = None):
        """
        Get OntoGuard status.

        Expected data:
            request_id: str (optional) - Client request ID
        """
        from ..security import get_ontoguard_adapter

        data = data or {}
        request_id = data.get('request_id')

        adapter = get_ontoguard_adapter()

        response = {
            'initialized': adapter._initialized,
            'active': adapter.is_active,
            'pass_through_mode': adapter._pass_through_mode,
            'ontology_count': len(adapter.ontology_paths),
            'connected_clients': len(_connected_clients),
            'active_subscriptions': sum(len(subs) for subs in _agent_subscriptions.values()),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        if request_id:
            response['request_id'] = request_id

        emit('status', response)

    logger.info("OntoGuard WebSocket handlers registered")
