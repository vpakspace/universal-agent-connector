"""
API routes for AI Agent Connector
Main API endpoints for agent management, query execution, and system features
"""

from flask import request, jsonify
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from functools import wraps
import os

from . import api_bp

# OntoGuard integration
from ..security import (
    get_ontoguard_adapter,
    ValidationResult,
    ValidationDeniedError,
    SchemaDriftDetector,
    SchemaBinding,
)

# Core components
from ..agents.registry import AgentRegistry
from ..agents.ai_agent_manager import AIAgentManager, set_cost_tracker as set_ai_cost_tracker
from ..permissions.access_control import AccessControl, Permission
from ..db import DatabaseConnector
from ..utils.sql_parser import extract_tables_from_query, get_query_type, QueryType
from ..utils.audit_logger import AuditLogger, ActionType, get_audit_logger, init_audit_logger
from ..utils.cost_tracker import CostTracker
from ..utils.nl_to_sql import NLToSQLConverter, set_cost_tracker as set_nl_cost_tracker
from ..utils.agent_orchestrator import AgentOrchestrator

# Enterprise features
from ..auth.sso import sso_manager, SSOConfig, SSOProviderType, UserProfile
from ..utils.legal_documents import legal_generator, LegalTemplate, DocumentGenerationRequest, DocumentType, Jurisdiction
from ..utils.chargeback import chargeback_manager, CostAllocationRule, AllocationRuleType, InvoiceStatus, UsageRecord, Invoice
from ..utils.adoption_analytics import adoption_analytics, FeatureType, QueryPatternType
from ..utils.training_data_export import training_data_exporter, QuerySQLPair, ExportFormat
from ..utils.security_monitor import SecurityMonitor
from ..utils.rate_limiter import RateLimiter, RateLimitConfig

# JWT Authentication
from ..security.jwt_auth import (
    get_jwt_manager,
    init_jwt_manager,
    jwt_required,
    jwt_or_api_key_required,
    get_current_agent_id,
    get_current_role,
    JWTConfig,
)

# Table name → OWL entity type mappings per domain
TABLE_ENTITY_MAPS = {
    'hospital': {
        'patients': 'PatientRecord',
        'medical_records': 'MedicalRecord',
        'lab_results': 'LabResult',
        'prescriptions': 'Prescription',
        'medications': 'Medication',
        'billing': 'Billing',
        'appointments': 'Appointment',
        'staff': 'Staff',
        'departments': 'Department',
        'rooms': 'Room',
        'insurance': 'Insurance',
        'surgeries': 'Surgery',
        'emergency_cases': 'EmergencyCase',
        'equipment': 'Equipment',
        'audit_log': 'AuditLog',
    },
    'finance': {
        'accounts': 'Account',
        'transactions': 'Transaction',
        'loans': 'Loan',
        'cards': 'Card',
        'customer_profiles': 'CustomerProfile',
        'reports': 'Report',
        'audit_log': 'AuditLog',
    },
}

def get_table_entity_map() -> dict:
    """Get active table_entity_map based on loaded ontology."""
    adapter = get_ontoguard_adapter()
    if adapter and adapter.ontology_paths:
        path = adapter.ontology_paths[0].lower()
        for domain, mapping in TABLE_ENTITY_MAPS.items():
            if domain in path:
                return mapping
    # Merge all maps as fallback
    merged = {}
    for m in TABLE_ENTITY_MAPS.values():
        merged.update(m)
    return merged

# Initialize global instances
agent_registry = AgentRegistry()
access_control = AccessControl()
ai_agent_manager = AIAgentManager()
audit_logger = get_audit_logger()
cost_tracker = CostTracker()
nl_converter = NLToSQLConverter()
agent_orchestrator = AgentOrchestrator(agent_registry)

# Set cost tracker for NL converter
set_nl_cost_tracker(cost_tracker)

# Set cost tracker for AI agent manager
set_ai_cost_tracker(cost_tracker)

# Initialize security monitor
security_monitor = SecurityMonitor()

# Initialize rate limiter
rate_limiter = RateLimiter()

# Default rate limit for new agents (can be overridden per agent)
DEFAULT_RATE_LIMIT = RateLimitConfig(
    queries_per_minute=60,
    queries_per_hour=1000,
    queries_per_day=10000
)


# ============================================================================
# Helper Functions
# ============================================================================

def authenticate_agent() -> Optional[str]:
    """Authenticate agent from API key header"""
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return None
    return agent_registry.authenticate_agent(api_key)


def require_auth() -> str:
    """Require authentication, return agent_id or raise error"""
    agent_id = authenticate_agent()
    if not agent_id:
        return None
    return agent_id


def check_rate_limit(agent_id: str) -> Tuple[bool, Optional[str]]:
    """
    Check if agent is within rate limits.

    Returns:
        (allowed, error_message)
    """
    return rate_limiter.check_rate_limit(agent_id)


def rate_limit_required(f):
    """
    Decorator to enforce rate limiting on endpoints.
    Must be used after authentication.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get agent_id from kwargs or authenticate
        agent_id = kwargs.get('agent_id') or authenticate_agent()
        if not agent_id:
            return jsonify({'error': 'Authentication required'}), 401

        # Check rate limit
        allowed, error_msg = check_rate_limit(agent_id)
        if not allowed:
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': error_msg,
                'retry_after': 60  # seconds
            }), 429

        return f(*args, **kwargs)
    return decorated_function


def check_permissions(agent_id: str, query: str) -> tuple[bool, List[Dict[str, Any]]]:
    """
    Check if agent has required permissions for query
    
    Returns:
        (has_permission, denied_resources)
    """
    tables = extract_tables_from_query(query)
    query_type = get_query_type(query)
    
    required_permission = Permission.READ if query_type == QueryType.SELECT else Permission.WRITE
    
    denied_resources = []
    for table in tables:
        # Check resource-level permissions first
        has_perm = access_control.has_resource_permission(agent_id, table, required_permission)
        if not has_perm:
            # Check general permissions
            has_perm = access_control.has_permission(agent_id, required_permission)
        
        if not has_perm:
            denied_resources.append({
                'resource': table,
                'required_permission': required_permission.value,
                'message': f'Agent does not have {required_permission.value} permission on {table}'
            })
    
    return len(denied_resources) == 0, denied_resources


# ============================================================================
# OntoGuard Validation Decorator
# ============================================================================

def validate_with_ontoguard(action: str, entity_type: str):
    """
    Decorator for OntoGuard semantic validation.

    This decorator validates incoming requests against OWL ontology rules
    before allowing the endpoint to execute.

    Args:
        action: The action being performed (e.g., 'query', 'create', 'delete')
        entity_type: The entity type being acted upon (e.g., 'Database', 'User')

    Returns:
        Decorated function that performs OntoGuard validation

    Example:
        @api_bp.route('/agents/<agent_id>/query', methods=['POST'])
        @validate_with_ontoguard(action='query', entity_type='Database')
        def execute_query(agent_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            adapter = get_ontoguard_adapter()

            # Skip validation if OntoGuard is not active
            if not adapter.is_active:
                return f(*args, **kwargs)

            # Extract context from request
            context = {
                'role': request.headers.get('X-User-Role', 'anonymous'),
                'user_id': request.headers.get('X-User-ID'),
                'ip': request.remote_addr,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Add any additional context from request body
            if request.is_json:
                data = request.get_json(silent=True) or {}
                if 'context' in data:
                    context.update(data['context'])

            # Validate action with OntoGuard
            result = adapter.validate_action(action, entity_type, context)

            if not result.allowed:
                return jsonify({
                    'error': 'Action denied by OntoGuard',
                    'reason': result.reason,
                    'constraints': result.constraints,
                    'suggestions': result.suggestions,
                    'metadata': result.metadata
                }), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator


def get_ontoguard_context() -> Dict[str, Any]:
    """
    Extract OntoGuard context from the current request.

    Returns:
        Dictionary containing context information for OntoGuard validation
    """
    context = {
        'role': request.headers.get('X-User-Role', 'anonymous'),
        'user_id': request.headers.get('X-User-ID'),
        'ip': request.remote_addr,
        'timestamp': datetime.utcnow().isoformat(),
        'method': request.method,
        'path': request.path
    }

    # Add query parameters
    if request.args:
        context['query_params'] = dict(request.args)

    return context


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI Agent Connector'
    }), 200


@api_bp.route('/api-docs', methods=['GET'])
def api_docs():
    """OpenAPI 3.0 documentation"""
    # Basic OpenAPI structure - can be expanded
    return jsonify({
        'openapi': '3.0.0',
        'info': {
            'title': 'AI Agent Connector API',
            'version': '0.1.0'
        },
        'paths': {
            '/agents/register': {},
            '/databases/test': {},
            '/agents/{agent_id}/query': {}
        }
    }), 200


# ============================================================================
# OntoGuard Endpoints
# ============================================================================

@api_bp.route('/ontoguard/status', methods=['GET'])
def ontoguard_status():
    """
    Get OntoGuard status and configuration.

    Returns:
        JSON object with OntoGuard status information
    """
    adapter = get_ontoguard_adapter()

    return jsonify({
        'enabled': adapter._initialized,
        'active': adapter.is_active,
        'pass_through_mode': adapter._pass_through_mode,
        'ontology_paths': adapter.ontology_paths,
        'config_path': adapter.config_path
    }), 200


@api_bp.route('/ontoguard/reload', methods=['POST'])
def reload_ontology():
    """
    Reload OntoGuard with a different ontology file.

    Request body:
        ontology_path: Path to OWL ontology file
    """
    data = request.get_json()
    ontology_path = data.get('ontology_path')
    if not ontology_path:
        return jsonify({'error': 'ontology_path required'}), 400

    if not os.path.exists(ontology_path):
        return jsonify({'error': f'File not found: {ontology_path}'}), 404

    try:
        from ..security import initialize_ontoguard
        config = {'ontology_paths': [ontology_path]}
        if initialize_ontoguard(config):
            return jsonify({'status': 'ok', 'ontology': ontology_path}), 200
        else:
            return jsonify({'error': 'Failed to reload ontology'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/ontoguard/validate', methods=['POST'])
def validate_action_endpoint():
    """
    Validate an action against OntoGuard ontology rules.

    Request body:
        {
            "action": "create|read|update|delete|query",
            "entity_type": "User|Order|Product|...",
            "context": {
                "role": "Admin|Customer|...",
                "user_id": "...",
                ...
            }
        }

    Returns:
        Validation result with allowed status and explanation
    """
    data = request.get_json() or {}

    action = data.get('action')
    entity_type = data.get('entity_type')
    context = data.get('context', {})

    if not action or not entity_type:
        return jsonify({
            'error': 'action and entity_type are required'
        }), 400

    adapter = get_ontoguard_adapter()
    result = adapter.validate_action(action, entity_type, context)

    return jsonify(result.to_dict()), 200 if result.allowed else 403


@api_bp.route('/ontoguard/permissions', methods=['POST'])
def check_permissions_endpoint():
    """
    Check if a role has permission for an action on entity type.

    Request body:
        {
            "role": "Admin|Customer|...",
            "action": "create|read|update|delete",
            "entity_type": "User|Order|..."
        }

    Returns:
        Permission check result
    """
    data = request.get_json() or {}

    role = data.get('role')
    action = data.get('action')
    entity_type = data.get('entity_type')

    if not all([role, action, entity_type]):
        return jsonify({
            'error': 'role, action, and entity_type are required'
        }), 400

    adapter = get_ontoguard_adapter()
    allowed = adapter.check_permissions(role, action, entity_type)

    return jsonify({
        'role': role,
        'action': action,
        'entity_type': entity_type,
        'allowed': allowed
    }), 200


@api_bp.route('/ontoguard/allowed-actions', methods=['GET'])
def get_allowed_actions_endpoint():
    """
    Get list of allowed actions for a role on entity type.

    Query parameters:
        - role: User role
        - entity_type: Entity type to query

    Returns:
        List of allowed actions
    """
    role = request.args.get('role', 'anonymous')
    entity_type = request.args.get('entity_type')

    if not entity_type:
        return jsonify({
            'error': 'entity_type query parameter is required'
        }), 400

    adapter = get_ontoguard_adapter()
    actions = adapter.get_allowed_actions(role, entity_type)

    return jsonify({
        'role': role,
        'entity_type': entity_type,
        'allowed_actions': actions
    }), 200


@api_bp.route('/ontoguard/explain', methods=['POST'])
def explain_rule_endpoint():
    """
    Get detailed explanation of validation rules for an action.

    Request body:
        {
            "action": "create|read|update|delete",
            "entity_type": "User|Order|...",
            "context": {...}
        }

    Returns:
        Human-readable explanation of the rules
    """
    data = request.get_json() or {}

    action = data.get('action')
    entity_type = data.get('entity_type')
    context = data.get('context', {})

    if not action or not entity_type:
        return jsonify({
            'error': 'action and entity_type are required'
        }), 400

    adapter = get_ontoguard_adapter()
    explanation = adapter.explain_rule(action, entity_type, context)

    return jsonify({
        'action': action,
        'entity_type': entity_type,
        'explanation': explanation
    }), 200


# ============================================================================
# Database Connection Endpoints
# ============================================================================

@api_bp.route('/databases/test', methods=['POST'])
def test_database_connection():
    """Test database connection before registration"""
    data = request.get_json() or {}
    
    connection_string = data.get('connection_string')
    if not connection_string:
        # Try individual parameters
        host = data.get('host')
        port = data.get('port', 5432)
        user = data.get('user')
        password = data.get('password')
        database = data.get('database')
        
        if not all([host, user, password, database]):
            return jsonify({
                'status': 'error',
                'error': 'Missing database configuration. Provide connection_string or (host, user, password, database)'
            }), 400
        
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    try:
        connector = DatabaseConnector(connection_string=connection_string)
        if connector.connect():
            # Test with a simple query
            connector.execute_query("SELECT 1")
            connector.disconnect()
            
            audit_logger.log(ActionType.QUERY_EXECUTION, details={'action': 'database_test', 'status': 'success'})
            
            return jsonify({
                'status': 'success',
                'message': 'Database connection test successful',
                'database_info': {
                    'connection_string': '***',
                    'connection_name': data.get('connection_name', 'default'),
                    'type': data.get('type', 'postgresql')
                }
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed',
                'error': 'Connection failed'
            }), 400
    except Exception as e:
        audit_logger.log(ActionType.QUERY_EXECUTION, details={'action': 'database_test', 'status': 'error'}, 
                        status='error', error_message=str(e))
        return jsonify({
            'status': 'error',
            'message': f'Database connection failed: {str(e)}',
            'error': str(e)
        }), 400


# ============================================================================
# Agent Registration & Management Endpoints
# ============================================================================

@api_bp.route('/agents/register', methods=['POST'])
def register_agent():
    """Register a new AI agent with optional rate limits"""
    data = request.get_json() or {}

    agent_id = data.get('agent_id')
    agent_info = data.get('agent_info', {})
    agent_credentials = data.get('agent_credentials', {})
    database = data.get('database')
    rate_limits_config = data.get('rate_limits')

    if not agent_id:
        return jsonify({'error': 'Missing required fields: agent_id'}), 400

    try:
        result = agent_registry.register_agent(
            agent_id=agent_id,
            agent_info=agent_info,
            credentials=agent_credentials,
            database_config=database
        )

        # Set rate limits (custom or default)
        if rate_limits_config:
            custom_config = RateLimitConfig(
                queries_per_minute=rate_limits_config.get('queries_per_minute'),
                queries_per_hour=rate_limits_config.get('queries_per_hour'),
                queries_per_day=rate_limits_config.get('queries_per_day')
            )
            rate_limiter.set_rate_limit(agent_id, custom_config)
            result['rate_limits'] = custom_config.to_dict()
        else:
            # Apply default rate limits
            rate_limiter.set_rate_limit(agent_id, DEFAULT_RATE_LIMIT)
            result['rate_limits'] = DEFAULT_RATE_LIMIT.to_dict()

        audit_logger.log(ActionType.AGENT_REGISTERED, agent_id=agent_id, details={'agent_info': agent_info})

        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        audit_logger.log(ActionType.AGENT_REGISTERED, agent_id=agent_id, status='error', error_message=str(e))
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500


@api_bp.route('/agents', methods=['GET'])
def list_agents():
    """List all registered agents"""
    agents = agent_registry.list_agents()
    audit_logger.log(ActionType.AGENTS_LISTED)
    return jsonify({'agents': agents, 'count': len(agents)}), 200


@api_bp.route('/agents/<agent_id>', methods=['GET'])
def get_agent(agent_id: str):
    """Get agent information"""
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        return jsonify({'error': f'Agent {agent_id} not found'}), 404
    
    audit_logger.log(ActionType.AGENT_VIEWED, agent_id=agent_id)
    return jsonify(agent), 200


@api_bp.route('/agents/<agent_id>', methods=['DELETE'])
def revoke_agent(agent_id: str):
    """Revoke an agent (complete cleanup)"""
    if not agent_registry.get_agent(agent_id):
        return jsonify({'error': f'Agent {agent_id} not found'}), 404

    # Revoke all permissions
    access_control.permissions.pop(agent_id, None)
    access_control.resource_permissions.pop(agent_id, None)

    # Remove rate limits
    rate_limiter.remove_agent(agent_id)

    # Remove from registry
    agent_registry.revoke_agent(agent_id)

    audit_logger.log(ActionType.AGENT_REVOKED, agent_id=agent_id)

    return jsonify({
        'message': f'Agent {agent_id} revoked successfully',
        'details': {
            'agent_id': agent_id,
            'permissions_revoked': True,
            'api_keys_invalidated': True,
            'database_access_removed': True,
            'credentials_removed': True,
            'rate_limits_removed': True
        }
    }), 200


@api_bp.route('/agents/<agent_id>/database', methods=['PUT'])
def update_agent_database(agent_id: str):
    """Update agent database connection"""
    if not agent_registry.get_agent(agent_id):
        return jsonify({'error': f'Agent {agent_id} not found'}), 404
    
    data = request.get_json() or {}
    connection_string = data.get('connection_string')
    
    if not connection_string:
        return jsonify({'error': 'connection_string is required'}), 400
    
    try:
        result = agent_registry.update_database_connection(agent_id, {'connection_string': connection_string})
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update database connection: {str(e)}'}), 400


# ============================================================================
# Table & Permission Endpoints
# ============================================================================

@api_bp.route('/agents/<agent_id>/tables', methods=['GET'])
def list_tables(agent_id: str):
    """List available tables from agent's database"""
    if not agent_registry.get_agent(agent_id):
        return jsonify({'error': f'Agent {agent_id} not found'}), 404
    
    connector = agent_registry.get_database_connector(agent_id)
    if not connector:
        return jsonify({'error': 'Agent does not have a database connection'}), 400
    
    try:
        # Get tables (database-specific query)
        tables_query = """
            SELECT table_schema, table_name, table_name as resource_id
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """
        tables_data = connector.execute_query(tables_query, as_dict=True)
        
        # Get resource permissions
        resource_perms = access_control.get_resource_permissions(agent_id)
        
        tables = []
        for row in tables_data or []:
            schema = row.get('table_schema', 'public')
            table_name = row.get('table_name')
            resource_id = f"{schema}.{table_name}" if schema != 'public' else table_name
            
            # Get permissions for this resource
            resource_info = resource_perms.get(resource_id, {})
            perms = resource_info.get('permissions', [])
            perm_values = [p.value for p in perms]
            
            tables.append({
                'schema': schema,
                'table_name': table_name,
                'resource_id': resource_id,
                'type': 'table',
                'permissions': perm_values,
                'has_read': Permission.READ in perms,
                'has_write': Permission.WRITE in perms
            })
        
        audit_logger.log(ActionType.TABLES_LISTED, agent_id=agent_id)
        
        return jsonify({
            'agent_id': agent_id,
            'database': agent_registry.get_agent(agent_id).get('database', {}).get('connection_name', 'default'),
            'tables': tables,
            'count': len(tables)
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to list tables: {str(e)}'}), 500


@api_bp.route('/agents/<agent_id>/access-preview', methods=['GET'])
def access_preview(agent_id: str):
    """Preview agent access to tables and fields"""
    if not agent_registry.get_agent(agent_id):
        return jsonify({'error': f'Agent {agent_id} not found'}), 404
    
    connector = agent_registry.get_database_connector(agent_id)
    if not connector:
        return jsonify({'error': 'Agent does not have a database connection'}), 400
    
    try:
        # Get all tables
        tables_query = """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """
        tables_data = connector.execute_query(tables_query, as_dict=True)
        
        # Get columns for all tables
        columns_query = """
            SELECT table_schema, table_name, column_name, data_type, is_nullable, column_default, ordinal_position
            FROM information_schema.columns
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name, ordinal_position
        """
        columns_data = connector.execute_query(columns_query, as_dict=True)
        
        # Organize columns by table
        columns_by_table = {}
        for col in columns_data or []:
            schema = col.get('table_schema', 'public')
            table_name = col.get('table_name')
            key = f"{schema}.{table_name}" if schema != 'public' else table_name
            if key not in columns_by_table:
                columns_by_table[key] = []
            columns_by_table[key].append({
                'name': col.get('column_name'),
                'type': col.get('data_type'),
                'nullable': col.get('is_nullable') == 'YES',
                'default': col.get('column_default'),
                'position': col.get('ordinal_position')
            })
        
        # Get resource permissions
        resource_perms = access_control.get_resource_permissions(agent_id)
        
        accessible_tables = []
        inaccessible_tables = []
        
        for row in tables_data or []:
            schema = row.get('table_schema', 'public')
            table_name = row.get('table_name')
            resource_id = f"{schema}.{table_name}" if schema != 'public' else table_name
            
            resource_info = resource_perms.get(resource_id, {})
            perms = resource_info.get('permissions', [])
            perm_values = [p.value for p in perms]
            
            columns = columns_by_table.get(resource_id, [])
            
            table_info = {
                'schema': schema,
                'table_name': table_name,
                'resource_id': resource_id,
                'access_status': 'accessible' if perms else 'no_permission',
                'permissions': perm_values,
                'has_read': Permission.READ in perms,
                'has_write': Permission.WRITE in perms,
                'column_count': len(columns),
                'columns': columns
            }
            
            if perms:
                accessible_tables.append(table_info)
            else:
                inaccessible_tables.append(table_info)
        
        # Calculate summary
        read_only = sum(1 for t in accessible_tables if t['has_read'] and not t['has_write'])
        read_write = sum(1 for t in accessible_tables if t['has_read'] and t['has_write'])
        write_only = sum(1 for t in accessible_tables if not t['has_read'] and t['has_write'])
        
        return jsonify({
            'agent_id': agent_id,
            'database': agent_registry.get_agent(agent_id).get('database', {}).get('connection_name', 'default'),
            'summary': {
                'total_tables': len(tables_data or []),
                'accessible_tables': len(accessible_tables),
                'inaccessible_tables': len(inaccessible_tables),
                'read_only_tables': read_only,
                'read_write_tables': read_write,
                'write_only_tables': write_only
            },
            'accessible_tables': accessible_tables,
            'inaccessible_tables': inaccessible_tables
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get access preview: {str(e)}'}), 500


@api_bp.route('/agents/<agent_id>/permissions/resources', methods=['PUT'])
def set_resource_permissions(agent_id: str):
    """Set resource-level permissions"""
    if not agent_registry.get_agent(agent_id):
        return jsonify({'error': f'Agent {agent_id} not found'}), 404
    
    data = request.get_json() or {}
    resource_id = data.get('resource_id')
    resource_type = data.get('resource_type', 'table')
    permissions = data.get('permissions', [])
    
    if not resource_id:
        return jsonify({'error': 'resource_id is required'}), 400
    
    # Convert permission strings to Permission enums
    perm_list = []
    for perm_str in permissions:
        try:
            perm_list.append(Permission(perm_str))
        except ValueError:
            return jsonify({'error': f'Invalid permission: {perm_str}'}), 400
    
    access_control.set_resource_permissions(agent_id, resource_id, perm_list, resource_type)
    
    audit_logger.log(ActionType.PERMISSION_SET, agent_id=agent_id, 
                    details={'resource_id': resource_id, 'permissions': permissions})
    
    return jsonify({
        'agent_id': agent_id,
        'resource_id': resource_id,
        'permissions': permissions
    }), 200


@api_bp.route('/agents/<agent_id>/permissions/resources', methods=['GET'])
def list_resource_permissions(agent_id: str):
    """List resource-level permissions"""
    if not agent_registry.get_agent(agent_id):
        return jsonify({'error': f'Agent {agent_id} not found'}), 404
    
    resource_perms = access_control.get_resource_permissions(agent_id)
    
    # Convert to response format
    resources = {}
    for resource_id, resource_info in resource_perms.items():
        resources[resource_id] = {
            'type': resource_info.get('type', 'table'),
            'permissions': [p.value for p in resource_info.get('permissions', [])]
        }
    
    audit_logger.log(ActionType.PERMISSION_LISTED, agent_id=agent_id)
    
    return jsonify({
        'agent_id': agent_id,
        'resources': resources
    }), 200


@api_bp.route('/agents/<agent_id>/permissions/resources/<resource_id>', methods=['DELETE'])
def revoke_resource_permissions(agent_id: str, resource_id: str):
    """Revoke all permissions for a resource"""
    if not agent_registry.get_agent(agent_id):
        return jsonify({'error': f'Agent {agent_id} not found'}), 404
    
    if not access_control.revoke_resource(agent_id, resource_id):
        return jsonify({'error': f'Resource {resource_id} not found for agent {agent_id}'}), 404
    
    audit_logger.log(ActionType.PERMISSION_REVOKED, agent_id=agent_id, 
                    details={'resource_id': resource_id})
    
    return jsonify({
        'message': f'Permissions revoked for resource {resource_id}',
        'agent_id': agent_id,
        'resource_id': resource_id
    }), 200


# ============================================================================
# Query Execution Endpoints
# ============================================================================

@api_bp.route('/agents/<agent_id>/query', methods=['POST'])
def execute_query(agent_id: str):
    """Execute a SQL query with permission enforcement, rate limiting, and OntoGuard validation"""
    agent_id_from_auth = authenticate_agent()
    if not agent_id_from_auth or agent_id_from_auth != agent_id:
        return jsonify({'error': 'Unauthorized'}), 401

    if not agent_registry.get_agent(agent_id):
        return jsonify({'error': f'Agent {agent_id} not found'}), 404

    # Rate limit check
    allowed, error_msg = check_rate_limit(agent_id)
    if not allowed:
        audit_logger.log(ActionType.QUERY_EXECUTION, agent_id=agent_id, status='rate_limited',
                        details={'error': error_msg})
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': error_msg,
            'retry_after': 60
        }), 429

    data = request.get_json() or {}
    query = data.get('query')
    params = data.get('params')
    as_dict = data.get('as_dict', False)

    if not query:
        return jsonify({'error': 'query is required'}), 400

    # OntoGuard semantic validation
    adapter = get_ontoguard_adapter()
    if adapter.is_active:
        # Map SQL operation to semantic action
        query_type = get_query_type(query)
        action_map = {
            QueryType.SELECT: 'read',
            QueryType.INSERT: 'create',
            QueryType.UPDATE: 'update',
            QueryType.DELETE: 'delete'
        }
        action = action_map.get(query_type, 'query')

        table_entity_map = get_table_entity_map()

        # Get tables from query and validate each
        tables = extract_tables_from_query(query)
        context = get_ontoguard_context()

        for table in tables:
            # Use mapping if available, otherwise convert automatically
            table_lower = table.lower()
            entity_type = table_entity_map.get(table_lower,
                ''.join(word.capitalize() for word in table.replace('_', ' ').split()))

            result = adapter.validate_action(action, entity_type, context)
            if not result.allowed:
                audit_logger.log(ActionType.QUERY_EXECUTION, agent_id=agent_id, status='denied',
                                details={'query_preview': query[:100], 'ontoguard_denial': result.reason})
                return jsonify({
                    'error': 'Action denied by OntoGuard',
                    'reason': result.reason,
                    'table': table,
                    'entity_type': entity_type,
                    'action': action,
                    'constraints': result.constraints,
                    'suggestions': result.suggestions
                }), 403

    # Check permissions
    has_permission, denied_resources = check_permissions(agent_id, query)
    if not has_permission:
        audit_logger.log(ActionType.QUERY_EXECUTION, agent_id=agent_id, status='denied',
                        details={'query_preview': query[:100], 'denied_resources': denied_resources})
        return jsonify({
            'error': 'Permission denied',
            'denied_resources': denied_resources,
            'message': 'Agent lacks required permissions on one or more resources'
        }), 403
    
    # Execute query
    connector = agent_registry.get_database_connector(agent_id)
    if not connector:
        return jsonify({'error': 'Agent does not have a database connection'}), 400

    try:
        # Connect to database
        connector.connect()

        query_type = get_query_type(query)

        # For non-SELECT queries (INSERT, UPDATE, DELETE), don't try to fetch results
        fetch_results = query_type == QueryType.SELECT
        result = connector.execute_query(query, params=params, as_dict=as_dict, fetch=fetch_results)
        row_count = len(result) if result else 0
        
        tables_accessed = list(extract_tables_from_query(query))
        
        audit_logger.log(ActionType.QUERY_EXECUTION, agent_id=agent_id, status='success',
                        details={
                            'query_type': query_type.value,
                            'tables_accessed': tables_accessed,
                            'row_count': row_count,
                            'query_preview': query[:100]
                        })
        
        response = jsonify({
            'agent_id': agent_id,
            'query_type': query_type.value,
            'tables_accessed': tables_accessed,
            'success': True,
            'result': result,
            'row_count': row_count
        })
        return response, 200
    except Exception as e:
        audit_logger.log(ActionType.QUERY_EXECUTION, agent_id=agent_id, status='error',
                        error_message=str(e), details={'query_preview': query[:100]})
        return jsonify({
            'error': 'Query execution failed',
            'message': str(e)
        }), 500
    finally:
        # Disconnect from database
        try:
            connector.disconnect()
        except Exception:
            pass


@api_bp.route('/agents/<agent_id>/query/natural', methods=['POST'])
def natural_language_query(agent_id: str):
    """Execute a natural language query with rate limiting and OntoGuard validation"""
    agent_id_from_auth = authenticate_agent()
    if not agent_id_from_auth or agent_id_from_auth != agent_id:
        return jsonify({'error': 'Unauthorized'}), 401

    if not agent_registry.get_agent(agent_id):
        return jsonify({'error': f'Agent {agent_id} not found'}), 404

    # Rate limit check
    allowed, error_msg = check_rate_limit(agent_id)
    if not allowed:
        audit_logger.log(ActionType.QUERY_EXECUTION, agent_id=agent_id, status='rate_limited',
                        details={'error': error_msg, 'query_type': 'natural_language'})
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': error_msg,
            'retry_after': 60
        }), 429

    data = request.get_json() or {}
    query = data.get('query') or data.get('question')
    as_dict = data.get('as_dict', False)
    
    if not query:
        return jsonify({'error': 'query or question is required'}), 400
    
    connector = agent_registry.get_database_connector(agent_id)
    if not connector:
        return jsonify({'error': 'Agent does not have a database connection'}), 400
    
    try:
        # Convert natural language to SQL
        conversion_result = nl_converter.convert_with_schema(query, connector)
        
        if conversion_result.get('error') or not conversion_result.get('sql'):
            return jsonify({
                'error': conversion_result.get('error', 'Failed to convert natural language to SQL'),
                'natural_language_query': query
            }), 400
        
        generated_sql = conversion_result['sql']

        # OntoGuard semantic validation on generated SQL
        adapter = get_ontoguard_adapter()
        if adapter.is_active:
            query_type = get_query_type(generated_sql)
            action_map = {
                QueryType.SELECT: 'read',
                QueryType.INSERT: 'create',
                QueryType.UPDATE: 'update',
                QueryType.DELETE: 'delete'
            }
            action = action_map.get(query_type, 'query')

            table_entity_map = get_table_entity_map()

            tables = extract_tables_from_query(generated_sql)
            context = get_ontoguard_context()

            for table in tables:
                table_lower = table.lower()
                entity_type = table_entity_map.get(table_lower,
                    ''.join(word.capitalize() for word in table.replace('_', ' ').split()))
                result = adapter.validate_action(action, entity_type, context)
                if not result.allowed:
                    audit_logger.log(ActionType.NATURAL_LANGUAGE_QUERY, agent_id=agent_id, status='denied',
                                    details={'query': query, 'generated_sql': generated_sql, 'ontoguard_denial': result.reason})
                    return jsonify({
                        'error': 'Action denied by OntoGuard',
                        'reason': result.reason,
                        'table': table,
                        'entity_type': entity_type,
                        'action': action,
                        'natural_language_query': query,
                        'generated_sql': generated_sql,
                        'constraints': result.constraints,
                        'suggestions': result.suggestions
                    }), 403

        # Check permissions on generated SQL
        has_permission, denied_resources = check_permissions(agent_id, generated_sql)
        if not has_permission:
            audit_logger.log(ActionType.NATURAL_LANGUAGE_QUERY, agent_id=agent_id, status='denied',
                            details={'query': query, 'generated_sql': generated_sql, 'denied_resources': denied_resources})
            return jsonify({
                'error': 'Permission denied',
                'denied_resources': denied_resources,
                'generated_sql': generated_sql,
                'natural_language_query': query
            }), 403
        
        # Execute query
        connector.connect()
        query_type = get_query_type(generated_sql)
        result = connector.execute_query(generated_sql, as_dict=as_dict)
        row_count = len(result) if result else 0
        
        tables_accessed = list(extract_tables_from_query(generated_sql))
        
        audit_logger.log(ActionType.NATURAL_LANGUAGE_QUERY, agent_id=agent_id, status='success',
                        details={
                            'query': query,
                            'generated_sql': generated_sql,
                            'query_type': query_type.value,
                            'tables_accessed': tables_accessed,
                            'row_count': row_count
                        })
        
        # Optionally record training data
        try:
            training_data_exporter.add_query_sql_pair(
                natural_language_query=query,
                sql_query=generated_sql,
                database_type=connector._connector.database_type if hasattr(connector._connector, 'database_type') else None,
                success=True
            )
        except:
            pass  # Don't fail if training data export fails
        
        return jsonify({
            'agent_id': agent_id,
            'natural_language_query': query,
            'generated_sql': generated_sql,
            'query_type': query_type.value,
            'tables_accessed': tables_accessed,
            'success': True,
            'result': result,
            'row_count': row_count
        }), 200
    except Exception as e:
        audit_logger.log(ActionType.NATURAL_LANGUAGE_QUERY, agent_id=agent_id, status='error',
                        error_message=str(e), details={'query': query})
        return jsonify({
            'error': 'Natural language query failed',
            'message': str(e),
            'natural_language_query': query
        }), 500


# ============================================================================
# Audit Log Endpoints (Persistent Audit Trail)
# ============================================================================

@api_bp.route('/audit/logs', methods=['GET'])
def get_audit_logs():
    """
    Get audit logs with filtering.

    Query params:
    - agent_id: Filter by agent ID
    - action_type: Filter by action type
    - status: Filter by status (success, error, denied)
    - start_date: Filter by start date (ISO format)
    - end_date: Filter by end date (ISO format)
    - limit: Max logs to return (default: 100)
    - offset: Pagination offset (default: 0)
    """
    agent_id = request.args.get('agent_id')
    action_type = request.args.get('action_type')
    status = request.args.get('status')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    # Parse dates
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid start_date format (use ISO format)'}), 400
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid end_date format (use ISO format)'}), 400

    result = audit_logger.get_logs(
        agent_id=agent_id,
        action_type=action_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

    return jsonify({
        'status': 'ok',
        'logs': result['logs'],
        'total': result['total'],
        'limit': result['limit'],
        'offset': result['offset'],
        'has_more': result['has_more'],
        'backend': audit_logger.backend_type
    }), 200


@api_bp.route('/audit/logs/<int:log_id>', methods=['GET'])
def get_audit_log(log_id: int):
    """Get specific audit log by ID"""
    log = audit_logger.get_log_by_id(log_id)
    if not log:
        return jsonify({'error': 'Log not found'}), 404
    return jsonify({'status': 'ok', 'log': log}), 200


@api_bp.route('/audit/statistics', methods=['GET'])
def get_audit_statistics():
    """
    Get audit log statistics.

    Query params:
    - agent_id: Filter by agent ID
    - days: Number of days to include (default: 7)
    """
    agent_id = request.args.get('agent_id')
    days = int(request.args.get('days', 7))

    stats = audit_logger.get_statistics(agent_id=agent_id, days=days)
    stats['backend'] = audit_logger.backend_type

    return jsonify({'status': 'ok', **stats}), 200


@api_bp.route('/audit/export', methods=['POST'])
def export_audit_logs():
    """
    Export audit logs to file.

    Request body:
    - output_path: Path to save file (default: logs/audit_export.jsonl)
    - agent_id: Filter by agent ID
    - start_date: Start date (ISO format)
    - end_date: End date (ISO format)
    - format: Output format ('jsonl' or 'json', default: 'jsonl')
    """
    data = request.get_json() or {}

    output_path = data.get('output_path', 'logs/audit_export.jsonl')
    agent_id = data.get('agent_id')
    format_type = data.get('format', 'jsonl')

    start_date = None
    end_date = None
    if data.get('start_date'):
        try:
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid start_date format'}), 400
    if data.get('end_date'):
        try:
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid end_date format'}), 400

    try:
        count = audit_logger.export_logs(
            output_path=output_path,
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
            format=format_type
        )

        return jsonify({
            'status': 'ok',
            'message': f'Exported {count} logs to {output_path}',
            'count': count,
            'output_path': output_path,
            'format': format_type
        }), 200
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500


@api_bp.route('/audit/config', methods=['GET'])
def get_audit_config():
    """Get audit logger configuration"""
    return jsonify({
        'status': 'ok',
        'backend': audit_logger.backend_type,
        'max_logs': audit_logger.max_logs,
        'action_types': [at.value for at in ActionType]
    }), 200


@api_bp.route('/audit/config', methods=['POST'])
def update_audit_config():
    """
    Reinitialize audit logger with new configuration.

    Request body:
    - backend: Backend type ('memory', 'file', 'sqlite')
    - log_dir: Directory for file backend
    - db_path: Database path for sqlite backend
    - max_logs: Max logs for memory backend
    - max_file_size_mb: Max file size for rotation
    - max_files: Max number of log files
    """
    global audit_logger

    data = request.get_json() or {}

    backend = data.get('backend', 'file')

    audit_logger = init_audit_logger(
        backend=backend,
        log_dir=data.get('log_dir', 'logs/audit'),
        db_path=data.get('db_path', 'logs/audit.db'),
        max_logs=data.get('max_logs', 10000),
        max_file_size_mb=data.get('max_file_size_mb', 100),
        max_files=data.get('max_files', 10)
    )

    return jsonify({
        'status': 'ok',
        'message': f'Audit logger reinitialized with {backend} backend',
        'backend': audit_logger.backend_type
    }), 200


# ============================================================================
# Security Notifications Endpoints
# ============================================================================

@api_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Get security notifications"""
    severity = request.args.get('severity')
    agent_id = request.args.get('agent_id')
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 100))
    
    notifications = security_monitor.get_notifications(
        severity=severity,
        agent_id=agent_id,
        unread_only=unread_only,
        limit=limit
    )
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'total': len(security_monitor.notifications),
        'unread_count': sum(1 for n in security_monitor.notifications if not n.read),
        'count': len(notifications)
    }), 200


@api_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id: int):
    """Mark notification as read"""
    if security_monitor.mark_read(notification_id):
        return jsonify({'message': 'Notification marked as read'}), 200
    return jsonify({'error': 'Notification not found'}), 404


@api_bp.route('/notifications/read-all', methods=['PUT'])
def mark_all_notifications_read():
    """Mark all notifications as read"""
    count = security_monitor.mark_all_read()
    return jsonify({
        'message': f'All notifications marked as read',
        'count': count
    }), 200


@api_bp.route('/notifications/stats', methods=['GET'])
def get_notification_stats():
    """Get notification statistics"""
    stats = security_monitor.get_statistics()
    return jsonify(stats), 200


# ============================================================================
# Cost Tracking Endpoints
# ============================================================================

@api_bp.route('/cost/dashboard', methods=['GET'])
def cost_dashboard():
    """Get cost dashboard data"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    agent_id = request.args.get('agent_id')
    
    dashboard_data = cost_tracker.get_dashboard_data(
        start_date=start_date,
        end_date=end_date,
        agent_id=agent_id
    )
    
    return jsonify(dashboard_data), 200


@api_bp.route('/cost/export', methods=['GET'])
def export_costs():
    """Export cost data"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    format_type = request.args.get('format', 'json')
    
    export_data = cost_tracker.export_costs(
        start_date=start_date,
        end_date=end_date,
        format=format_type
    )
    
    return jsonify(export_data), 200


@api_bp.route('/cost/stats', methods=['GET'])
def cost_stats():
    """Get cost statistics"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    stats = cost_tracker.get_statistics(start_date=start_date, end_date=end_date)
    return jsonify(stats), 200


@api_bp.route('/cost/budget-alerts', methods=['GET'])
def budget_alerts():
    """Get budget alerts"""
    alerts = cost_tracker.get_budget_alerts()
    return jsonify({'alerts': alerts}), 200


# ============================================================================
# Multi-Agent Collaboration Endpoints
# ============================================================================

@api_bp.route('/agents/collaborate', methods=['POST'])
def create_collaboration_session():
    """Create a multi-agent collaboration session"""
    agent_id = authenticate_agent()
    if not agent_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json() or {}
    query = data.get('query')
    agents = data.get('agents', [])
    
    if not query:
        return jsonify({'error': 'query is required'}), 400
    
    if not agents:
        return jsonify({'error': 'agents list is required'}), 400
    
    try:
        # Build roles dict
        roles = {agent['agent_id']: agent['role'] for agent in agents}
        agent_ids = [agent['agent_id'] for agent in agents]
        
        session = agent_orchestrator.create_session(query, agent_ids, roles)
        
        return jsonify(session.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/agents/collaborate/<session_id>', methods=['GET'])
def get_collaboration_session(session_id: str):
    """Get collaboration session details"""
    agent_id = authenticate_agent()
    if not agent_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    session = agent_orchestrator.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify(session.to_dict()), 200


@api_bp.route('/agents/collaborate/<session_id>/execute', methods=['POST'])
def execute_collaboration_session(session_id: str):
    """Execute a collaboration session"""
    agent_id = authenticate_agent()
    if not agent_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    session = agent_orchestrator.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        result = agent_orchestrator.execute_session(session_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/agents/collaborate/<session_id>/trace', methods=['GET'])
def get_collaboration_trace(session_id: str):
    """Get collaboration trace for visualization"""
    agent_id = authenticate_agent()
    if not agent_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    session = agent_orchestrator.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'session_id': session_id,
        'traces': [t.to_dict() for t in session.traces],
        'messages': [m.to_dict() for m in session.messages]
    }), 200


@api_bp.route('/agents/collaborate', methods=['GET'])
def list_collaboration_sessions():
    """List collaboration sessions"""
    agent_id = authenticate_agent()
    if not agent_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    limit = int(request.args.get('limit', 50))
    sessions = agent_orchestrator.list_sessions(limit=limit)
    
    return jsonify({
        'sessions': [s.to_dict() for s in sessions],
        'count': len(sessions)
    }), 200


# ============================================================================
# SSO Integration Endpoints (from SSO_ENDPOINTS_TO_ADD.md)
# ============================================================================

@api_bp.route('/sso/configs', methods=['GET'])
def list_sso_configs():
    """List all SSO configurations"""
    configs = sso_manager.list_configs()
    return jsonify({'configs': [c.to_dict() for c in configs]}), 200


@api_bp.route('/sso/configs', methods=['POST'])
def create_sso_config():
    """Create a new SSO configuration"""
    data = request.get_json() or {}
    config_id = data.get('config_id')
    
    if not config_id:
        return jsonify({'error': 'config_id is required'}), 400
    
    if sso_manager.get_config(config_id):
        return jsonify({'error': f'SSO config {config_id} already exists'}), 409
    
    try:
        config = SSOConfig.from_dict(data)
        sso_manager.add_config(config_id, config)
        return jsonify({
            'config_id': config_id,
            'message': 'SSO configuration created successfully',
            'config': config.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/sso/configs/<config_id>', methods=['GET'])
def get_sso_config(config_id: str):
    """Get SSO configuration"""
    config = sso_manager.get_config(config_id)
    if not config:
        return jsonify({'error': 'SSO config not found'}), 404
    return jsonify(config.to_dict()), 200


@api_bp.route('/sso/configs/<config_id>', methods=['PUT'])
def update_sso_config(config_id: str):
    """Update SSO configuration"""
    data = request.get_json() or {}
    try:
        config = SSOConfig.from_dict(data)
        sso_manager.update_config(config_id, config)
        return jsonify({
            'config_id': config_id,
            'message': 'SSO configuration updated successfully',
            'config': config.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/sso/configs/<config_id>', methods=['DELETE'])
def delete_sso_config(config_id: str):
    """Delete SSO configuration"""
    if sso_manager.delete_config(config_id):
        return jsonify({'message': f'SSO config {config_id} deleted successfully'}), 200
    return jsonify({'error': 'SSO config not found'}), 404


@api_bp.route('/sso/login/<provider>', methods=['POST'])
def sso_login(provider: str):
    """Initiate SSO login"""
    config_id = request.args.get('config_id')
    if not config_id:
        return jsonify({'error': 'config_id is required'}), 400
    
    try:
        result = sso_manager.initiate_login(provider, config_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/sso/callback/<provider>', methods=['POST'])
def sso_callback(provider: str):
    """Handle SSO callback"""
    data = request.get_json() or {}
    config_id = request.args.get('config_id')
    
    if not config_id:
        return jsonify({'error': 'config_id is required'}), 400
    
    try:
        result = sso_manager.handle_callback(provider, config_id, data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/sso/user-profile', methods=['GET'])
def get_user_profile():
    """Get user profile from SSO"""
    user_id = request.args.get('user_id')
    config_id = request.args.get('config_id')
    
    if not user_id or not config_id:
        return jsonify({'error': 'user_id and config_id are required'}), 400
    
    try:
        profile = sso_manager.get_user_profile(user_id, config_id)
        if profile:
            return jsonify(profile.to_dict()), 200
        return jsonify({'error': 'User profile not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/sso/attribute-mapping/<config_id>', methods=['GET'])
def get_attribute_mapping(config_id: str):
    """Get attribute mapping for SSO config"""
    config = sso_manager.get_config(config_id)
    if not config:
        return jsonify({'error': 'SSO config not found'}), 404
    return jsonify({'attribute_mapping': config.attribute_mapping}), 200


@api_bp.route('/sso/attribute-mapping/<config_id>', methods=['PUT'])
def update_attribute_mapping(config_id: str):
    """Update attribute mapping for SSO config"""
    data = request.get_json() or {}
    attribute_mapping = data.get('attribute_mapping')
    
    if not attribute_mapping:
        return jsonify({'error': 'attribute_mapping is required'}), 400
    
    config = sso_manager.get_config(config_id)
    if not config:
        return jsonify({'error': 'SSO config not found'}), 404
    
    config.attribute_mapping = attribute_mapping
    sso_manager.update_config(config_id, config)
    
    return jsonify({
        'config_id': config_id,
        'message': 'Attribute mapping updated successfully',
        'attribute_mapping': attribute_mapping
    }), 200


# ============================================================================
# Legal Documents Endpoints (from LEGAL_DOCUMENTS_ENDPOINTS.md)
# ============================================================================

@api_bp.route('/legal/templates', methods=['GET'])
def list_legal_templates():
    """List legal document templates"""
    document_type = request.args.get('document_type')
    jurisdiction = request.args.get('jurisdiction')
    
    templates = legal_generator.list_templates(document_type, jurisdiction)
    return jsonify({'templates': [t.to_dict() for t in templates]}), 200


@api_bp.route('/legal/templates', methods=['POST'])
def create_legal_template():
    """Create a legal document template"""
    data = request.get_json() or {}
    try:
        template = LegalTemplate.from_dict(data)
        legal_generator.add_template(template)
        return jsonify({
            'message': 'Template created successfully',
            'template': template.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/legal/templates/<template_id>', methods=['GET'])
def get_legal_template(template_id: str):
    """Get legal document template"""
    template = legal_generator.get_template(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    return jsonify(template.to_dict()), 200


@api_bp.route('/legal/documents/generate', methods=['POST'])
def generate_legal_document():
    """Generate a legal document"""
    data = request.get_json() or {}
    try:
        request_obj = DocumentGenerationRequest.from_dict(data)
        document = legal_generator.generate_document(request_obj)
        return jsonify(document.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/legal/documents/<document_id>', methods=['GET'])
def get_legal_document(document_id: str):
    """Get generated legal document"""
    document = legal_generator.get_document(document_id)
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    return jsonify(document.to_dict()), 200


@api_bp.route('/legal/jurisdictions', methods=['GET'])
def list_jurisdictions():
    """List supported jurisdictions"""
    jurisdictions = [j.value for j in Jurisdiction]
    return jsonify({'jurisdictions': jurisdictions}), 200


# ============================================================================
# Chargeback Endpoints (from CHARGEBACK_ENDPOINTS.md)
# ============================================================================

@api_bp.route('/chargeback/usage', methods=['POST'])
def record_usage():
    """Record resource usage for chargeback"""
    data = request.get_json() or {}
    
    usage_record = chargeback_manager.record_usage(
        team_id=data.get('team_id'),
        user_id=data.get('user_id'),
        agent_id=data.get('agent_id'),
        resource_type=data.get('resource_type', 'query'),
        quantity=data.get('quantity', 1.0),
        cost_usd=data.get('cost_usd', 0.0),
        metadata=data.get('metadata', {})
    )
    
    return jsonify(usage_record.to_dict()), 201


@api_bp.route('/chargeback/usage', methods=['GET'])
def list_usage_records():
    """List usage records"""
    team_id = request.args.get('team_id')
    user_id = request.args.get('user_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = int(request.args.get('limit', 100))
    
    records = chargeback_manager.list_usage_records(
        team_id=team_id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return jsonify({
        'records': [r.to_dict() for r in records],
        'count': len(records)
    }), 200


@api_bp.route('/chargeback/allocation-rules', methods=['POST'])
def create_allocation_rule():
    """Create cost allocation rule"""
    data = request.get_json() or {}
    try:
        rule = CostAllocationRule.from_dict(data)
        rule_id = chargeback_manager.add_allocation_rule(rule)
        return jsonify({
            'rule_id': rule_id,
            'message': 'Allocation rule created successfully',
            'rule': rule.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/chargeback/allocation-rules', methods=['GET'])
def list_allocation_rules():
    """List allocation rules"""
    rules = chargeback_manager.list_allocation_rules()
    return jsonify({
        'rules': [r.to_dict() for r in rules],
        'count': len(rules)
    }), 200


@api_bp.route('/chargeback/allocate', methods=['POST'])
def allocate_costs():
    """Allocate costs based on rules"""
    data = request.get_json() or {}
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    rule_id = data.get('rule_id')
    
    allocations = chargeback_manager.allocate_costs(
        start_date=start_date,
        end_date=end_date,
        rule_id=rule_id
    )
    
    return jsonify({
        'allocations': [a.to_dict() for a in allocations],
        'count': len(allocations)
    }), 200


@api_bp.route('/chargeback/invoices', methods=['POST'])
def generate_invoice():
    """Generate invoice"""
    data = request.get_json() or {}
    team_id = data.get('team_id')
    user_id = data.get('user_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    invoice = chargeback_manager.generate_invoice(
        team_id=team_id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify(invoice.to_dict()), 201


@api_bp.route('/chargeback/invoices', methods=['GET'])
def list_invoices():
    """List invoices"""
    team_id = request.args.get('team_id')
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 100))
    
    invoices = chargeback_manager.list_invoices(
        team_id=team_id,
        user_id=user_id,
        status=status,
        limit=limit
    )
    
    return jsonify({
        'invoices': [i.to_dict() for i in invoices],
        'count': len(invoices)
    }), 200


# ============================================================================
# Adoption Analytics Endpoints (from ANALYTICS_ENDPOINTS.md)
# ============================================================================

@api_bp.route('/analytics/telemetry/opt-in', methods=['POST'])
def opt_in_telemetry():
    """Opt-in a user to telemetry collection"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    adoption_analytics.opt_in_telemetry(user_id)
    return jsonify({
        'message': 'Telemetry opt-in successful',
        'user_id': user_id
    }), 200


@api_bp.route('/analytics/telemetry/opt-out', methods=['POST'])
def opt_out_telemetry():
    """Opt-out a user from telemetry collection"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    adoption_analytics.opt_out_telemetry(user_id)
    return jsonify({
        'message': 'Telemetry opt-out successful',
        'user_id': user_id
    }), 200


@api_bp.route('/analytics/telemetry/status/<user_id>', methods=['GET'])
def get_telemetry_status(user_id: str):
    """Get telemetry status for a user"""
    opted_in = adoption_analytics.is_opted_in(user_id)
    return jsonify({
        'user_id': user_id,
        'opted_in': opted_in,
        'telemetry_enabled': adoption_analytics.telemetry_enabled
    }), 200


@api_bp.route('/analytics/events', methods=['POST'])
def track_analytics_event():
    """Track an analytics event"""
    data = request.get_json() or {}
    
    feature_type_str = data.get('feature_type')
    if not feature_type_str:
        return jsonify({'error': 'feature_type is required'}), 400
    
    try:
        feature_type = FeatureType(feature_type_str)
    except ValueError:
        return jsonify({'error': f'Invalid feature_type: {feature_type_str}'}), 400
    
    event = adoption_analytics.track_event(
        feature_type=feature_type,
        user_id=data.get('user_id'),
        agent_id=data.get('agent_id'),
        metadata=data.get('metadata', {})
    )
    
    if event:
        return jsonify(event.to_dict()), 201
    return jsonify({'message': 'Event not tracked (telemetry disabled or user opted out)'}), 200


@api_bp.route('/analytics/dau', methods=['GET'])
def get_dau_timeseries():
    """Get Daily Active Users timeseries"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    dau_data = adoption_analytics.get_dau_timeseries(start_date=start_date, end_date=end_date)
    return jsonify(dau_data), 200


@api_bp.route('/analytics/query-patterns', methods=['GET'])
def get_query_patterns():
    """Get query pattern analysis"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    pattern_type = request.args.get('pattern_type')
    
    patterns = adoption_analytics.get_query_patterns(
        start_date=start_date,
        end_date=end_date,
        pattern_type=pattern_type
    )
    
    return jsonify({
        'patterns': [p.to_dict() for p in patterns],
        'count': len(patterns)
    }), 200


@api_bp.route('/analytics/feature-usage', methods=['GET'])
def get_feature_usage():
    """Get feature usage statistics"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    feature_type = request.args.get('feature_type')
    
    usage = adoption_analytics.get_feature_usage(
        start_date=start_date,
        end_date=end_date,
        feature_type=feature_type
    )
    
    return jsonify({
        'usage': [u.to_dict() for u in usage],
        'count': len(usage)
    }), 200


@api_bp.route('/analytics/export', methods=['GET'])
def export_analytics_data():
    """Export analytics data"""
    format_type = request.args.get('format', 'json')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    export_data = adoption_analytics.export_data(
        format=format_type,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify(export_data), 200


# ============================================================================
# Training Data Export Endpoints (from TRAINING_DATA_EXPORT_ENDPOINTS.md)
# ============================================================================

@api_bp.route('/training-data/pairs', methods=['POST'])
def add_training_pair():
    """Add a query-SQL pair to training data"""
    data = request.get_json() or {}
    
    natural_language_query = data.get('natural_language_query')
    sql_query = data.get('sql_query')
    
    if not natural_language_query or not sql_query:
        return jsonify({'error': 'natural_language_query and sql_query are required'}), 400
    
    pair = training_data_exporter.add_query_sql_pair(
        natural_language_query=natural_language_query,
        sql_query=sql_query,
        database_type=data.get('database_type'),
        database_name=data.get('database_name'),
        success=data.get('success', True),
        execution_time_ms=data.get('execution_time_ms'),
        metadata=data.get('metadata', {})
    )
    
    return jsonify({'pair': pair.to_dict()}), 201


@api_bp.route('/training-data/pairs', methods=['GET'])
def list_training_pairs():
    """List training pairs"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    successful_only = request.args.get('successful_only', 'false').lower() == 'true'
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    pairs = training_data_exporter.list_pairs(
        limit=limit,
        offset=offset,
        filter_successful_only=successful_only,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify({
        'pairs': [p.to_dict() for p in pairs],
        'count': len(pairs)
    }), 200


@api_bp.route('/training-data/pairs/<pair_id>', methods=['GET'])
def get_training_pair(pair_id: str):
    """Get a specific training pair"""
    pair = training_data_exporter.get_pair(pair_id)
    if not pair:
        return jsonify({'error': 'Pair not found'}), 404
    return jsonify({'pair': pair.to_dict()}), 200


@api_bp.route('/training-data/pairs/<pair_id>', methods=['DELETE'])
def delete_training_pair(pair_id: str):
    """Delete a training pair"""
    if training_data_exporter.delete_pair(pair_id):
        return jsonify({'message': 'Pair deleted successfully'}), 200
    return jsonify({'error': 'Pair not found'}), 404


@api_bp.route('/training-data/statistics', methods=['GET'])
def get_training_statistics():
    """Get training data statistics"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    stats = training_data_exporter.get_statistics(start_date=start_date, end_date=end_date)
    return jsonify({'statistics': stats.to_dict()}), 200


@api_bp.route('/training-data/export', methods=['GET'])
def export_training_data():
    """Export training data"""
    format_str = request.args.get('format', 'jsonl')
    successful_only = request.args.get('successful_only', 'false').lower() == 'true'
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        format_enum = ExportFormat(format_str)
    except ValueError:
        return jsonify({'error': f'Invalid format: {format_str}. Must be jsonl, json, or csv'}), 400
    
    # Create temporary file path (in production, use proper file handling)
    import tempfile
    import os
    from flask import send_file
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=f'.{format_str}') as f:
        temp_path = f.name
    
    try:
        count, stats = training_data_exporter.export(
            temp_path,
            format=format_enum,
            filter_successful_only=successful_only,
            start_date=start_date,
            end_date=end_date
        )
        
        if count == 0:
            os.unlink(temp_path)
            return jsonify({'error': 'No data to export'}), 404
        
        # Determine content type
        content_types = {
            'jsonl': 'application/x-ndjson',
            'json': 'application/json',
            'csv': 'text/csv'
        }
        
        return send_file(
            temp_path,
            mimetype=content_types.get(format_str, 'application/octet-stream'),
            as_attachment=True,
            download_name=f'training_data.{format_str}'
        )
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# AI Agent Management Endpoints (Admin)
# ============================================================================

@api_bp.route('/admin/ai-agents/register', methods=['POST'])
def register_ai_agent():
    """Register an AI agent provider (admin only)"""
    agent_id_from_auth = authenticate_agent()
    if not agent_id_from_auth:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not access_control.has_permission(agent_id_from_auth, Permission.ADMIN):
        return jsonify({'error': 'Admin permission required'}), 403
    
    data = request.get_json() or {}
    try:
        result = ai_agent_manager.register_agent(data)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/admin/ai-agents', methods=['GET'])
def list_ai_agents():
    """List all AI agent providers (admin only)"""
    agent_id_from_auth = authenticate_agent()
    if not agent_id_from_auth:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not access_control.has_permission(agent_id_from_auth, Permission.ADMIN):
        return jsonify({'error': 'Admin permission required'}), 403
    
    agents = ai_agent_manager.list_agents()
    return jsonify({'agents': agents, 'count': len(agents)}), 200


@api_bp.route('/admin/ai-agents/<agent_id>/query', methods=['POST'])
def execute_ai_agent_query(agent_id: str):
    """Execute a query using an AI agent (admin only)"""
    agent_id_from_auth = authenticate_agent()
    if not agent_id_from_auth:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not access_control.has_permission(agent_id_from_auth, Permission.ADMIN):
        return jsonify({'error': 'Admin permission required'}), 403
    
    data = request.get_json() or {}
    query = data.get('query')
    context = data.get('context', {})
    
    if not query:
        return jsonify({'error': 'query is required'}), 400
    
    try:
        result = ai_agent_manager.execute_query(agent_id, query, context=context)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# Schema Drift Detection Endpoints
# ============================================================

# Module-level detector instance
_schema_drift_detector: Optional[SchemaDriftDetector] = None


def get_schema_drift_detector() -> SchemaDriftDetector:
    """Get or create the schema drift detector singleton."""
    global _schema_drift_detector
    if _schema_drift_detector is None:
        _schema_drift_detector = SchemaDriftDetector()
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            'config', 'schema_bindings.yaml'
        )
        if os.path.exists(config_path):
            _schema_drift_detector.load_bindings(config_path)
    return _schema_drift_detector


@api_bp.route('/schema/drift-check', methods=['GET'])
def schema_drift_check():
    """
    Check schema drift for all bindings.

    Query params:
        entity: (optional) Check a specific entity only
        domain: (optional) Filter by domain

    Returns:
        JSON with drift reports for all (or filtered) bindings.
    """
    detector = get_schema_drift_detector()
    entity_filter = request.args.get('entity')
    domain_filter = request.args.get('domain')

    bindings = detector.bindings
    if not bindings:
        return jsonify({
            'status': 'no_bindings',
            'message': 'No schema bindings configured. POST to /api/schema/bindings to add.',
            'reports': []
        }), 200

    reports = []
    for entity_name, binding in bindings.items():
        if entity_filter and entity_name != entity_filter:
            continue
        if domain_filter and binding.domain != domain_filter:
            continue

        reports.append({
            'entity': entity_name,
            'table': binding.table,
            'domain': binding.domain,
            'expected_columns': binding.columns,
            'status': 'binding_loaded',
            'message': 'Use POST /api/schema/drift-check with current_schema to detect drift',
        })

    return jsonify({
        'status': 'ok',
        'total_bindings': len(bindings),
        'reports': reports,
    }), 200


@api_bp.route('/schema/drift-check', methods=['POST'])
def schema_drift_check_with_schema():
    """
    Check schema drift with actual current schemas.

    Body JSON:
        {
            "schemas": {
                "PatientRecord": {"id": "integer", "name": "text", ...},
                ...
            }
        }

    Returns:
        JSON with drift reports including missing/new columns, type changes, renames.
    """
    detector = get_schema_drift_detector()
    data = request.get_json() or {}
    schemas = data.get('schemas', {})

    if not schemas:
        return jsonify({'error': 'schemas field is required'}), 400

    reports = []
    for entity_name, current_schema in schemas.items():
        report = detector.detect_drift(entity_name, current_schema)
        fixes = detector.suggest_fixes(report) if report.has_drift else []
        reports.append({
            **report.to_dict(),
            'fixes': [f.to_dict() for f in fixes],
        })

    has_critical = any(r['severity'] == 'CRITICAL' for r in reports)

    return jsonify({
        'status': 'critical_drift' if has_critical else 'ok',
        'reports': reports,
    }), 200


@api_bp.route('/schema/drift-check/live', methods=['POST'])
def schema_drift_check_live():
    """
    Check schema drift against live database connection.

    Body JSON:
        {
            "agent_id": "doctor-1",
            "entities": ["PatientRecord", "Staff"]  // optional, all if omitted
        }

    Requires X-API-Key header for agent authentication.
    """
    agent_id_from_auth = authenticate_agent()
    if not agent_id_from_auth:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    agent_id = data.get('agent_id', agent_id_from_auth)
    entities = data.get('entities')

    if not agent_registry.get_agent(agent_id):
        return jsonify({'error': f'Agent {agent_id} not found'}), 404

    connector = agent_registry.get_database_connector(agent_id)
    if not connector:
        return jsonify({'error': 'Agent does not have a database connection'}), 400

    detector = get_schema_drift_detector()
    if not detector.bindings:
        return jsonify({
            'status': 'no_bindings',
            'message': 'No schema bindings configured.',
            'reports': []
        }), 200

    try:
        connector.connect()
        drift_reports = detector.check_live(connector, entities)

        reports = []
        for report in drift_reports:
            fixes = detector.suggest_fixes(report) if report.has_drift else []
            reports.append({
                **report.to_dict(),
                'fixes': [f.to_dict() for f in fixes],
            })

        has_critical = any(r['severity'] == 'CRITICAL' for r in reports)

        return jsonify({
            'status': 'critical_drift' if has_critical else 'ok',
            'agent_id': agent_id,
            'reports': reports,
        }), 200
    except Exception as e:
        return jsonify({'error': f'Live drift check failed: {str(e)}'}), 500
    finally:
        try:
            connector.disconnect()
        except Exception:
            pass


@api_bp.route('/schema/bindings', methods=['GET'])
def list_schema_bindings():
    """List all schema bindings."""
    detector = get_schema_drift_detector()
    bindings = []
    for name, b in detector.bindings.items():
        bindings.append({
            'entity': b.entity,
            'table': b.table,
            'domain': b.domain,
            'columns': b.columns,
        })
    return jsonify({'bindings': bindings, 'total': len(bindings)}), 200


@api_bp.route('/schema/bindings', methods=['POST'])
def create_schema_binding():
    """
    Create or update a schema binding.

    Body JSON:
        {
            "entity": "PatientRecord",
            "table": "patients",
            "domain": "hospital",
            "columns": {"id": "integer", "name": "text"}
        }
    """
    detector = get_schema_drift_detector()
    data = request.get_json() or {}

    entity = data.get('entity')
    table = data.get('table')
    columns = data.get('columns', {})

    if not entity or not table:
        return jsonify({'error': 'entity and table are required'}), 400

    binding = SchemaBinding(
        entity=entity,
        table=table,
        columns=columns,
        domain=data.get('domain', 'default'),
    )
    detector.add_binding(binding)

    return jsonify({
        'status': 'created',
        'binding': {
            'entity': binding.entity,
            'table': binding.table,
            'domain': binding.domain,
            'columns': binding.columns,
        }
    }), 201


# =============================================================================
# Cache Management Endpoints
# =============================================================================

@api_bp.route('/cache/stats', methods=['GET'])
def get_cache_stats():
    """
    Get validation cache statistics.

    Returns:
        JSON with cache statistics (hits, misses, hit_rate, size, etc.)
    """
    try:
        from ..cache import get_cache_stats as _get_cache_stats
        stats = _get_cache_stats()
        return jsonify({
            'status': 'ok',
            'cache': stats,
        })
    except ImportError:
        return jsonify({
            'status': 'unavailable',
            'message': 'Cache module not installed',
        }), 503


@api_bp.route('/cache/invalidate', methods=['POST'])
def invalidate_cache():
    """
    Invalidate cache entries.

    Body JSON (optional):
        {
            "action": "read",
            "entity_type": "PatientRecord",
            "role": "Doctor",
            "domain": "hospital"
        }

    If body is empty or all fields are null, clears entire cache.
    """
    try:
        from ..cache import invalidate_cache as _invalidate_cache

        data = request.get_json() or {}
        action = data.get('action')
        entity_type = data.get('entity_type')
        role = data.get('role')
        domain = data.get('domain')

        count = _invalidate_cache(action, entity_type, role, domain)

        return jsonify({
            'status': 'ok',
            'invalidated': count,
            'filter': {
                'action': action,
                'entity_type': entity_type,
                'role': role,
                'domain': domain,
            }
        })
    except ImportError:
        return jsonify({
            'status': 'unavailable',
            'message': 'Cache module not installed',
        }), 503


@api_bp.route('/cache/config', methods=['GET'])
def get_cache_config():
    """
    Get cache configuration.

    Returns:
        JSON with cache settings (max_size, default_ttl, enabled, redis_url)
    """
    try:
        from ..cache import get_validation_cache

        cache = get_validation_cache()
        return jsonify({
            'status': 'ok',
            'config': {
                'max_size': cache.max_size,
                'default_ttl': cache.default_ttl,
                'enabled': cache.enabled,
                'redis_connected': cache._redis is not None,
            }
        })
    except ImportError:
        return jsonify({
            'status': 'unavailable',
            'message': 'Cache module not installed',
        }), 503


@api_bp.route('/cache/cleanup', methods=['POST'])
def cleanup_cache():
    """
    Cleanup expired cache entries.

    Returns:
        JSON with number of cleaned up entries
    """
    try:
        from ..cache import get_validation_cache

        cache = get_validation_cache()
        count = cache.cleanup_expired()

        return jsonify({
            'status': 'ok',
            'cleaned_up': count,
        })
    except ImportError:
        return jsonify({
            'status': 'unavailable',
            'message': 'Cache module not installed',
        }), 503


# =============================================================================
# Rate Limiting Endpoints
# =============================================================================

@api_bp.route('/rate-limits', methods=['GET'])
def list_rate_limits():
    """
    List all configured rate limits.

    Returns:
        JSON with all agent rate limit configurations
    """
    limits = {}
    for agent_id, config in rate_limiter._configs.items():
        limits[agent_id] = {
            'config': config.to_dict(),
            'usage': rate_limiter.get_usage_stats(agent_id)
        }

    return jsonify({
        'status': 'ok',
        'default_limits': DEFAULT_RATE_LIMIT.to_dict(),
        'agent_limits': limits,
        'total_agents': len(limits)
    })


@api_bp.route('/rate-limits/<agent_id>', methods=['GET'])
def get_agent_rate_limit(agent_id: str):
    """
    Get rate limit configuration and usage for an agent.

    Args:
        agent_id: Agent identifier

    Returns:
        JSON with rate limit config and current usage
    """
    config = rate_limiter.get_rate_limit(agent_id)
    usage = rate_limiter.get_usage_stats(agent_id)

    return jsonify({
        'status': 'ok',
        'agent_id': agent_id,
        'configured': config is not None,
        'config': config.to_dict() if config else DEFAULT_RATE_LIMIT.to_dict(),
        'usage': usage
    })


@api_bp.route('/rate-limits/<agent_id>', methods=['PUT'])
def set_agent_rate_limit(agent_id: str):
    """
    Set rate limit configuration for an agent.

    Body JSON:
        {
            "queries_per_minute": 60,
            "queries_per_hour": 1000,
            "queries_per_day": 10000
        }
    """
    data = request.get_json() or {}

    config = RateLimitConfig(
        queries_per_minute=data.get('queries_per_minute'),
        queries_per_hour=data.get('queries_per_hour'),
        queries_per_day=data.get('queries_per_day')
    )

    rate_limiter.set_rate_limit(agent_id, config)

    return jsonify({
        'status': 'ok',
        'agent_id': agent_id,
        'config': config.to_dict()
    })


@api_bp.route('/rate-limits/<agent_id>', methods=['DELETE'])
def remove_agent_rate_limit(agent_id: str):
    """
    Remove rate limit configuration for an agent.

    This removes custom limits; agent will use default limits.
    """
    config = rate_limiter.get_rate_limit(agent_id)
    if config:
        rate_limiter.remove_agent(agent_id)

    return jsonify({
        'status': 'ok',
        'agent_id': agent_id,
        'removed': config is not None
    })


@api_bp.route('/rate-limits/<agent_id>/reset', methods=['POST'])
def reset_agent_rate_limit(agent_id: str):
    """
    Reset rate limit counters for an agent.

    This clears the usage history without changing the configuration.
    """
    rate_limiter.reset_agent_limits(agent_id)

    return jsonify({
        'status': 'ok',
        'agent_id': agent_id,
        'message': 'Rate limit counters reset'
    })


@api_bp.route('/rate-limits/default', methods=['GET'])
def get_default_rate_limits():
    """
    Get default rate limits applied to new agents.
    """
    return jsonify({
        'status': 'ok',
        'default_limits': DEFAULT_RATE_LIMIT.to_dict()
    })


# ============================================================================
# JWT Authentication Endpoints
# ============================================================================

@api_bp.route('/auth/token', methods=['POST'])
def get_jwt_token():
    """
    Generate JWT tokens for an agent.

    Requires valid API key for initial token generation.
    Returns access_token (short-lived) and refresh_token (long-lived).

    Request body:
        - role (optional): User role for RBAC

    Headers:
        - X-API-Key: Agent's API key

    Returns:
        - access_token: Short-lived access token (30 min default)
        - refresh_token: Long-lived refresh token (7 days default)
        - token_type: "Bearer"
        - expires_in: Access token lifetime in seconds
    """
    # Authenticate with API key first
    agent_id = authenticate_agent()
    if not agent_id:
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Valid X-API-Key required to obtain JWT tokens'
        }), 401

    data = request.get_json() or {}
    role = data.get('role') or request.headers.get('X-User-Role')

    jwt_mgr = get_jwt_manager()
    tokens = jwt_mgr.generate_token_pair(agent_id, role)

    audit_logger.log(
        action_type=ActionType.JWT_TOKEN_GENERATED,
        agent_id=agent_id,
        details={'role': role}
    )

    return jsonify({
        'status': 'ok',
        'agent_id': agent_id,
        **tokens
    })


@api_bp.route('/auth/refresh', methods=['POST'])
def refresh_jwt_token():
    """
    Refresh an access token using a refresh token.

    Request body:
        - refresh_token: Valid refresh token

    Returns:
        - access_token: New short-lived access token
        - token_type: "Bearer"
        - expires_in: Access token lifetime in seconds
    """
    data = request.get_json()
    if not data or 'refresh_token' not in data:
        return jsonify({
            'error': 'Bad Request',
            'message': 'refresh_token is required'
        }), 400

    jwt_mgr = get_jwt_manager()
    success, new_tokens, error = jwt_mgr.refresh_access_token(data['refresh_token'])

    if not success:
        return jsonify({
            'error': 'Unauthorized',
            'message': error or 'Invalid refresh token'
        }), 401

    return jsonify({
        'status': 'ok',
        **new_tokens
    })


@api_bp.route('/auth/verify', methods=['POST'])
def verify_jwt_token():
    """
    Verify a JWT token and return its payload.

    Request body:
        - token: JWT token to verify
        - type (optional): Token type to verify ("access" or "refresh", default: "access")

    Returns:
        - valid: True/False
        - payload: Token payload if valid
        - error: Error message if invalid
    """
    data = request.get_json()
    if not data or 'token' not in data:
        return jsonify({
            'error': 'Bad Request',
            'message': 'token is required'
        }), 400

    token_type = data.get('type', 'access')
    jwt_mgr = get_jwt_manager()
    is_valid, payload, error = jwt_mgr.verify_token(data['token'], expected_type=token_type)

    if not is_valid:
        return jsonify({
            'valid': False,
            'error': error
        })

    return jsonify({
        'valid': True,
        'payload': {
            'agent_id': payload.agent_id,
            'role': payload.role,
            'token_type': payload.token_type,
            'expires_at': payload.exp.isoformat() if payload.exp else None,
            'issued_at': payload.iat.isoformat() if payload.iat else None,
        }
    })


@api_bp.route('/auth/revoke', methods=['POST'])
def revoke_jwt_token():
    """
    Revoke a JWT token.

    Request body:
        - token: JWT token to revoke

    Headers:
        - X-API-Key or Authorization: Bearer <token> for authentication

    Returns:
        - status: "ok" if revoked
    """
    # Require authentication
    agent_id = authenticate_agent()
    if not agent_id:
        # Try JWT auth
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            jwt_mgr = get_jwt_manager()
            is_valid, payload, _ = jwt_mgr.verify_token(auth_header[7:])
            if is_valid and payload:
                agent_id = payload.agent_id

    if not agent_id:
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required to revoke tokens'
        }), 401

    data = request.get_json()
    if not data or 'token' not in data:
        return jsonify({
            'error': 'Bad Request',
            'message': 'token is required'
        }), 400

    jwt_mgr = get_jwt_manager()
    revoked = jwt_mgr.revoke_token(data['token'])

    if revoked:
        audit_logger.log(
            action_type=ActionType.JWT_TOKEN_REVOKED,
            agent_id=agent_id,
            details={}
        )

    return jsonify({
        'status': 'ok',
        'revoked': revoked
    })


@api_bp.route('/auth/config', methods=['GET'])
def get_jwt_config():
    """
    Get JWT configuration (excluding secrets).

    Returns:
        - algorithm: JWT algorithm
        - access_token_expire_minutes: Access token lifetime
        - refresh_token_expire_days: Refresh token lifetime
        - issuer: Token issuer
    """
    jwt_mgr = get_jwt_manager()
    return jsonify({
        'status': 'ok',
        'config': jwt_mgr.get_config()
    })

