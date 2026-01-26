"""
API routes for AI Agent Connector
Main API endpoints for agent management, query execution, and system features
"""

from flask import request, jsonify
from typing import Dict, List, Optional, Any
import os

from . import api_bp

# Core components
from ..agents.registry import AgentRegistry
from ..agents.ai_agent_manager import AIAgentManager
from ..permissions.access_control import AccessControl, Permission
from ..db import DatabaseConnector
from ..utils.sql_parser import extract_tables_from_query, get_query_type, QueryType
from ..utils.audit_logger import AuditLogger, ActionType
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

# Initialize global instances
agent_registry = AgentRegistry()
access_control = AccessControl()
ai_agent_manager = AIAgentManager()
audit_logger = AuditLogger()
cost_tracker = CostTracker()
nl_converter = NLToSQLConverter()
agent_orchestrator = AgentOrchestrator(agent_registry)

# Set cost tracker for NL converter
set_nl_cost_tracker(cost_tracker)

# Set cost tracker for AI agent manager
ai_agent_manager.set_cost_tracker(cost_tracker)

# Initialize security monitor
security_monitor = SecurityMonitor()


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
    """Register a new AI agent"""
    data = request.get_json() or {}
    
    agent_id = data.get('agent_id')
    agent_info = data.get('agent_info', {})
    agent_credentials = data.get('agent_credentials', {})
    database = data.get('database')
    
    if not agent_id:
        return jsonify({'error': 'Missing required fields: agent_id'}), 400
    
    try:
        result = agent_registry.register_agent(
            agent_id=agent_id,
            agent_info=agent_info,
            credentials=agent_credentials,
            database_config=database
        )
        
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
            'credentials_removed': True
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
    """Execute a SQL query with permission enforcement"""
    agent_id_from_auth = authenticate_agent()
    if not agent_id_from_auth or agent_id_from_auth != agent_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not agent_registry.get_agent(agent_id):
        return jsonify({'error': f'Agent {agent_id} not found'}), 404
    
    data = request.get_json() or {}
    query = data.get('query')
    params = data.get('params')
    as_dict = data.get('as_dict', False)
    
    if not query:
        return jsonify({'error': 'query is required'}), 400
    
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
        query_type = get_query_type(query)
        result = connector.execute_query(query, params=params, as_dict=as_dict)
        row_count = len(result) if result else 0
        
        tables_accessed = list(extract_tables_from_query(query))
        
        audit_logger.log(ActionType.QUERY_EXECUTION, agent_id=agent_id, status='success',
                        details={
                            'query_type': query_type.value,
                            'tables_accessed': tables_accessed,
                            'row_count': row_count,
                            'query_preview': query[:100]
                        })
        
        return jsonify({
            'agent_id': agent_id,
            'query_type': query_type.value,
            'tables_accessed': tables_accessed,
            'success': True,
            'result': result,
            'row_count': row_count
        }), 200
    except Exception as e:
        audit_logger.log(ActionType.QUERY_EXECUTION, agent_id=agent_id, status='error',
                        error_message=str(e), details={'query_preview': query[:100]})
        return jsonify({
            'error': 'Query execution failed',
            'message': str(e)
        }), 500


@api_bp.route('/agents/<agent_id>/query/natural', methods=['POST'])
def natural_language_query(agent_id: str):
    """Execute a natural language query"""
    agent_id_from_auth = authenticate_agent()
    if not agent_id_from_auth or agent_id_from_auth != agent_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not agent_registry.get_agent(agent_id):
        return jsonify({'error': f'Agent {agent_id} not found'}), 404
    
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
# Audit Log Endpoints
# ============================================================================

@api_bp.route('/audit/logs', methods=['GET'])
def get_audit_logs():
    """Get audit logs with filtering"""
    agent_id = request.args.get('agent_id')
    action_type = request.args.get('action_type')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    logs = audit_logger.get_logs(
        agent_id=agent_id,
        action_type=action_type,
        status=status,
        limit=limit,
        offset=offset
    )
    
    total = len(audit_logger.logs)
    
    return jsonify({
        'logs': logs,
        'total': total,
        'limit': limit,
        'offset': offset,
        'has_more': offset + limit < total
    }), 200


@api_bp.route('/audit/logs/<int:log_id>', methods=['GET'])
def get_audit_log(log_id: int):
    """Get specific audit log by ID"""
    log = audit_logger.get_log(log_id)
    if not log:
        return jsonify({'error': 'Log not found'}), 404
    return jsonify(log), 200


@api_bp.route('/audit/statistics', methods=['GET'])
def get_audit_statistics():
    """Get audit log statistics"""
    agent_id = request.args.get('agent_id')
    stats = audit_logger.get_statistics(agent_id=agent_id)
    return jsonify(stats), 200


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

