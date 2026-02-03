"""
GraphQL Schema Definition
"""

import graphene
from graphene import ObjectType, String, Int, Float, Boolean, List, Field, ID, DateTime, JSONString
from typing import Optional, Dict, Any
from datetime import datetime

# Import existing managers
from ..agents.registry import AgentRegistry
from ..agents.ai_agent_manager import AIAgentManager
from ..utils.cost_tracker import CostTracker
from ..utils.audit_logger import AuditLogger
from ..utils.provider_failover import ProviderFailoverManager


# Initialize managers (will be injected from routes)
_agent_registry = None
_ai_agent_manager = None
_cost_tracker = None
_audit_logger = None
_failover_manager = None


def set_managers(agent_registry, ai_agent_manager, cost_tracker, audit_logger, failover_manager):
    """Set managers for GraphQL resolvers"""
    global _agent_registry, _ai_agent_manager, _cost_tracker, _audit_logger, _failover_manager
    _agent_registry = agent_registry
    _ai_agent_manager = ai_agent_manager
    _cost_tracker = cost_tracker
    _audit_logger = audit_logger
    _failover_manager = failover_manager


# ============================================================================
# GraphQL Types
# ============================================================================

class AgentType(ObjectType):
    """Agent GraphQL type"""
    agent_id = ID(required=True)
    status = String()
    api_key = String()
    created_at = DateTime()
    database_type = String()
    database_name = String()
    permissions_count = Int()
    last_query_at = DateTime()


class QueryResultType(ObjectType):
    """Query result GraphQL type"""
    data = List(JSONString)
    rows = Int()
    columns = List(String)
    execution_time_ms = Float()
    sql = String()
    confidence = Float()


class CostRecordType(ObjectType):
    """Cost record GraphQL type"""
    call_id = ID()
    timestamp = DateTime()
    provider = String()
    model = String()
    agent_id = String()
    prompt_tokens = Int()
    completion_tokens = Int()
    total_tokens = Int()
    cost_usd = Float()
    operation_type = String()


class CostDashboardType(ObjectType):
    """Cost dashboard GraphQL type"""
    total_cost = Float(required=True)
    total_calls = Int(required=True)
    cost_by_provider = JSONString()
    cost_by_operation = JSONString()
    cost_by_agent = JSONString()
    daily_costs = List(JSONString)
    period_days = Int()


class BudgetAlertType(ObjectType):
    """Budget alert GraphQL type"""
    alert_id = ID(required=True)
    name = String(required=True)
    threshold_usd = Float(required=True)
    period = String(required=True)
    triggered = Boolean()
    notification_emails = List(String)
    webhook_url = String()
    created_at = DateTime()


class FailoverStatsType(ObjectType):
    """Failover statistics GraphQL type"""
    agent_id = ID(required=True)
    active_provider = String()
    total_switches = Int()
    provider_health = JSONString()
    last_switch_at = DateTime()
    consecutive_failures = graphene.JSONString()


class AuditLogType(ObjectType):
    """Audit log GraphQL type"""
    log_id = ID(required=True)
    agent_id = String()
    action_type = String(required=True)
    timestamp = DateTime(required=True)
    details = JSONString()
    user_id = String()
    ip_address = String()


class NotificationType(ObjectType):
    """Notification GraphQL type"""
    notification_id = ID(required=True)
    type = String(required=True)
    message = String(required=True)
    read = Boolean(required=True)
    created_at = DateTime(required=True)
    severity = String()
    link = String()


class QueryTemplateType(ObjectType):
    """Query template GraphQL type"""
    template_id = ID(required=True)
    name = String(required=True)
    sql = String(required=True)
    tags = List(String)
    is_public = Boolean()
    created_at = DateTime()
    usage_count = Int()


class PermissionType(ObjectType):
    """Permission GraphQL type"""
    resource_type = String(required=True)
    resource_id = String(required=True)
    permissions = List(String, required=True)
    granted_at = DateTime()


class OntoGuardValidationResultType(ObjectType):
    """OntoGuard validation result GraphQL type"""
    allowed = Boolean(required=True)
    action = String(required=True)
    entity_type = String(required=True)
    role = String()
    reason = String()
    constraints = List(String)
    suggestions = List(String)


class OntoGuardStatusType(ObjectType):
    """OntoGuard status GraphQL type"""
    enabled = Boolean(required=True)
    active = Boolean(required=True)
    ontology_loaded = Boolean()
    ontology_path = String()
    triples_count = Int()
    action_rules_count = Int()


class AllowedActionType(ObjectType):
    """Allowed action GraphQL type"""
    action = String(required=True)
    entity_type = String(required=True)
    constraints = List(String)


class RuleExplanationType(ObjectType):
    """Rule explanation GraphQL type"""
    action = String(required=True)
    entity_type = String(required=True)
    allowed_roles = List(String)
    constraints = List(String)
    owl_class = String()
    description = String()


# ============================================================================
# Input Types
# ============================================================================

class RegisterAgentInput(graphene.InputObjectType):
    """Input for registering an agent"""
    agent_id = ID(required=True)
    agent_credentials = JSONString(required=True)
    database = JSONString(required=True)
    agent_info = JSONString()


class ExecuteQueryInput(graphene.InputObjectType):
    """Input for executing a query"""
    agent_id = ID(required=True)
    query = String(required=True)
    params = JSONString()
    fetch = Boolean(default_value=True)


class NaturalLanguageQueryInput(graphene.InputObjectType):
    """Input for natural language query"""
    agent_id = ID(required=True)
    query = String(required=True)
    preview_only = Boolean(default_value=False)
    use_cache = Boolean(default_value=True)
    use_template = String()
    template_params = JSONString()


class ConfigureFailoverInput(graphene.InputObjectType):
    """Input for configuring failover"""
    agent_id = ID(required=True)
    primary_provider_id = String(required=True)
    backup_provider_ids = List(String, required=True)
    health_check_enabled = Boolean(default_value=True)
    auto_failover_enabled = Boolean(default_value=True)
    health_check_interval = Int()
    consecutive_failures_threshold = Int()


class CreateBudgetAlertInput(graphene.InputObjectType):
    """Input for creating budget alert"""
    name = String(required=True)
    threshold_usd = Float(required=True)
    period = String(required=True)
    notification_emails = List(String)
    webhook_url = String()


class ValidateActionInput(graphene.InputObjectType):
    """Input for OntoGuard action validation"""
    action = String(required=True)
    entity_type = String(required=True)
    role = String(required=True)
    user_id = String()
    resource_id = String()


class CheckPermissionsInput(graphene.InputObjectType):
    """Input for OntoGuard permissions check"""
    role = String(required=True)
    action = String(required=True)
    entity_type = String(required=True)


class ExplainRuleInput(graphene.InputObjectType):
    """Input for OntoGuard rule explanation"""
    action = String(required=True)
    entity_type = String(required=True)


# ============================================================================
# Queries
# ============================================================================

class Query(ObjectType):
    """GraphQL Query root"""
    
    # Agents
    agent = Field(AgentType, agent_id=ID(required=True))
    agents = List(AgentType, limit=Int(), offset=Int())
    
    # Queries
    execute_query = Field(
        QueryResultType,
        input=ExecuteQueryInput(required=True)
    )
    
    execute_natural_language_query = Field(
        QueryResultType,
        input=NaturalLanguageQueryInput(required=True)
    )
    
    # Cost Tracking
    cost_dashboard = Field(
        CostDashboardType,
        agent_id=ID(),
        provider=String(),
        period_days=Int(default_value=30)
    )
    
    cost_records = List(
        CostRecordType,
        agent_id=ID(),
        provider=String(),
        limit=Int(default_value=100),
        offset=Int()
    )
    
    budget_alerts = List(BudgetAlertType)
    budget_alert = Field(BudgetAlertType, alert_id=ID(required=True))
    
    # Provider Failover
    failover_stats = Field(
        FailoverStatsType,
        agent_id=ID(required=True)
    )
    
    provider_health = Field(
        JSONString,
        agent_id=ID(required=True)
    )
    
    # Audit & Notifications
    audit_logs = List(
        AuditLogType,
        agent_id=ID(),
        action_type=String(),
        limit=Int(default_value=100),
        offset=Int()
    )
    
    audit_log = Field(AuditLogType, log_id=ID(required=True))
    
    notifications = List(
        NotificationType,
        unread_only=Boolean(),
        limit=Int(default_value=100)
    )
    
    notification = Field(NotificationType, notification_id=ID(required=True))
    
    # Query Templates
    query_templates = List(
        QueryTemplateType,
        agent_id=ID(required=True),
        tags=List(String)
    )
    
    query_template = Field(
        QueryTemplateType,
        agent_id=ID(required=True),
        template_id=ID(required=True)
    )
    
    # Permissions
    permissions = List(
        PermissionType,
        agent_id=ID(required=True)
    )
    
    # Health
    health = Field(JSONString)

    # OntoGuard
    ontoguard_status = Field(OntoGuardStatusType)

    ontoguard_validate = Field(
        OntoGuardValidationResultType,
        input=ValidateActionInput(required=True)
    )

    ontoguard_allowed_actions = List(
        AllowedActionType,
        role=String(required=True),
        entity_type=String()
    )

    ontoguard_explain_rule = Field(
        RuleExplanationType,
        input=ExplainRuleInput(required=True)
    )

    # Resolvers
    def resolve_agent(self, info, agent_id):
        """Resolve single agent"""
        if not _agent_registry:
            return None
        try:
            agent = _agent_registry.get_agent(agent_id)
            if agent:
                return {
                    'agent_id': agent_id,
                    'status': 'active',
                    'api_key': None,  # Don't expose API keys
                    'created_at': None,
                    'database_type': None,
                    'database_name': None,
                    'permissions_count': 0,
                    'last_query_at': None
                }
        except Exception:
            pass
        return None
    
    def resolve_agents(self, info, limit=None, offset=None):
        """Resolve list of agents"""
        if not _agent_registry:
            return []
        try:
            agents = _agent_registry.list_agents()
            if offset:
                agents = agents[offset:]
            if limit:
                agents = agents[:limit]
            return [
                {
                    'agent_id': agent_id,
                    'status': 'active',
                    'api_key': None,
                    'created_at': None,
                    'database_type': None,
                    'database_name': None,
                    'permissions_count': 0,
                    'last_query_at': None
                }
                for agent_id in agents
            ]
        except Exception:
            return []
    
    def resolve_execute_query(self, info, input):
        """Resolve query execution"""
        if not _agent_registry or not _ai_agent_manager:
            return None
        try:
            # Call the actual query execution via AIAgentManager
            # This integrates with the existing REST API logic
            from ..permissions import AccessControl
            from ..utils.sql_parser import extract_tables_from_query, get_query_type, QueryType
            from ..permissions import Permission
            
            access_control = AccessControl()
            agent_id = input['agent_id']
            query = input['query']
            params = input.get('params')
            fetch = input.get('fetch', True)
            
            # Verify agent exists
            agent = _agent_registry.get_agent(agent_id)
            if not agent:
                return None
            
            # Get database connector
            connector = _agent_registry.get_database_connector(agent_id)
            if not connector:
                return None
            
            # Extract tables and check permissions
            tables = extract_tables_from_query(query)
            query_type = get_query_type(query)
            required_permission = Permission.READ if query_type == QueryType.SELECT else Permission.WRITE
            
            for table in tables:
                if not access_control.has_resource_permission(agent_id, table, required_permission):
                    return None
            
            # Execute query
            connector.connect()
            try:
                if fetch:
                    result = connector.execute_query(query, params)
                    return {
                        'data': result.get('data', []),
                        'rows': result.get('rows', 0),
                        'columns': result.get('columns', []),
                        'execution_time_ms': result.get('execution_time_ms', 0.0),
                        'sql': query,
                        'confidence': None
                    }
                else:
                    connector.execute_query(query, params)
                    return {
                        'data': [],
                        'rows': 0,
                        'columns': [],
                        'execution_time_ms': 0.0,
                        'sql': query,
                        'confidence': None
                    }
            finally:
                connector.close()
        except Exception:
            return None
    
    def resolve_execute_natural_language_query(self, info, input):
        """Resolve natural language query"""
        if not _ai_agent_manager:
            return None
        try:
            # Call the actual NL query logic via AIAgentManager
            agent_id = input['agent_id']
            query = input['query']
            preview_only = input.get('preview_only', False)
            use_cache = input.get('use_cache', True)
            use_template = input.get('use_template')
            template_params = input.get('template_params')
            
            # Execute via AIAgentManager
            result = _ai_agent_manager.execute_query(
                agent_id=agent_id,
                query=query,
                context={
                    'preview_only': preview_only,
                    'use_cache': use_cache,
                    'use_template': use_template,
                    'template_params': template_params
                }
            )
            
            if result:
                return {
                    'data': result.get('data', []),
                    'rows': result.get('rows', 0),
                    'columns': result.get('columns', []),
                    'execution_time_ms': result.get('execution_time_ms', 0.0),
                    'sql': result.get('sql'),
                    'confidence': result.get('confidence', 0.0)
                }
        except Exception:
            pass
        return None
    
    def resolve_cost_dashboard(self, info, agent_id=None, provider=None, period_days=30):
        """Resolve cost dashboard"""
        if not _cost_tracker:
            return None
        try:
            dashboard_data = _cost_tracker.get_dashboard_data(
                agent_id=agent_id,
                provider=provider,
                period_days=period_days
            )
            return {
                'total_cost': dashboard_data.get('total_cost', 0.0),
                'total_calls': dashboard_data.get('total_calls', 0),
                'cost_by_provider': dashboard_data.get('cost_by_provider', {}),
                'cost_by_operation': dashboard_data.get('cost_by_operation', {}),
                'cost_by_agent': dashboard_data.get('cost_by_agent', {}),
                'daily_costs': dashboard_data.get('daily_costs', []),
                'period_days': period_days
            }
        except Exception:
            return None
    
    def resolve_cost_records(self, info, agent_id=None, provider=None, limit=100, offset=None):
        """Resolve cost records"""
        if not _cost_tracker:
            return []
        try:
            # Get records from cost tracker
            records = []
            if hasattr(_cost_tracker, '_cost_records'):
                all_records = list(_cost_tracker._cost_records.values())
                if agent_id:
                    all_records = [r for r in all_records if r.agent_id == agent_id]
                if provider:
                    all_records = [r for r in all_records if r.provider == provider]
                if offset:
                    all_records = all_records[offset:]
                if limit:
                    all_records = all_records[:limit]
                records = [
                    {
                        'call_id': r.call_id,
                        'timestamp': r.timestamp,
                        'provider': r.provider,
                        'model': r.model,
                        'agent_id': r.agent_id,
                        'prompt_tokens': r.prompt_tokens,
                        'completion_tokens': r.completion_tokens,
                        'total_tokens': r.total_tokens,
                        'cost_usd': r.cost_usd,
                        'operation_type': r.operation_type
                    }
                    for r in all_records
                ]
            return records
        except Exception:
            return []
    
    def resolve_budget_alerts(self, info):
        """Resolve budget alerts"""
        if not _cost_tracker:
            return []
        try:
            alerts = []
            if hasattr(_cost_tracker, '_budget_alerts'):
                alerts = [
                    {
                        'alert_id': alert.alert_id,
                        'name': alert.name,
                        'threshold_usd': alert.threshold_usd,
                        'period': alert.period,
                        'triggered': alert.triggered,
                        'notification_emails': alert.notification_emails,
                        'webhook_url': alert.webhook_url,
                        'created_at': None
                    }
                    for alert in _cost_tracker._budget_alerts.values()
                ]
            return alerts
        except Exception:
            return []
    
    def resolve_budget_alert(self, info, alert_id):
        """Resolve single budget alert"""
        if not _cost_tracker:
            return None
        try:
            if hasattr(_cost_tracker, '_budget_alerts'):
                alert = _cost_tracker._budget_alerts.get(alert_id)
                if alert:
                    return {
                        'alert_id': alert.alert_id,
                        'name': alert.name,
                        'threshold_usd': alert.threshold_usd,
                        'period': alert.period,
                        'triggered': alert.triggered,
                        'notification_emails': alert.notification_emails,
                        'webhook_url': alert.webhook_url,
                        'created_at': None
                    }
        except Exception:
            pass
        return None
    
    def resolve_failover_stats(self, info, agent_id):
        """Resolve failover statistics"""
        if not _failover_manager:
            return None
        try:
            stats = _failover_manager.get_failover_stats(agent_id)
            if stats:
                return {
                    'agent_id': agent_id,
                    'active_provider': stats.get('active_provider'),
                    'total_switches': stats.get('total_switches', 0),
                    'provider_health': stats.get('provider_health', {}),
                    'last_switch_at': None,
                    'consecutive_failures': stats.get('consecutive_failures', {})
                }
        except Exception:
            pass
        return None
    
    def resolve_provider_health(self, info, agent_id):
        """Resolve provider health"""
        if not _failover_manager:
            return None
        try:
            health = _failover_manager.get_provider_health(agent_id)
            return health
        except Exception:
            return None
    
    def resolve_audit_logs(self, info, agent_id=None, action_type=None, limit=100, offset=None):
        """Resolve audit logs"""
        if not _audit_logger:
            return []
        try:
            logs = _audit_logger.get_logs(
                agent_id=agent_id,
                action_type=action_type,
                limit=limit,
                offset=offset
            )
            return [
                {
                    'log_id': log.get('id', 0),
                    'agent_id': log.get('agent_id'),
                    'action_type': log.get('action_type', ''),
                    'timestamp': log.get('timestamp'),
                    'details': log.get('details'),
                    'user_id': log.get('user_id'),
                    'ip_address': log.get('ip_address')
                }
                for log in logs
            ]
        except Exception:
            return []
    
    def resolve_audit_log(self, info, log_id):
        """Resolve single audit log"""
        if not _audit_logger:
            return None
        try:
            log = _audit_logger.get_log(log_id)
            if log:
                return {
                    'log_id': log_id,
                    'agent_id': log.get('agent_id'),
                    'action_type': log.get('action_type', ''),
                    'timestamp': log.get('timestamp'),
                    'details': log.get('details'),
                    'user_id': log.get('user_id'),
                    'ip_address': log.get('ip_address')
                }
        except Exception:
            pass
        return None
    
    def resolve_notifications(self, info, unread_only=None, limit=100):
        """Resolve notifications"""
        # Placeholder - would integrate with notification system
        return []
    
    def resolve_notification(self, info, notification_id):
        """Resolve single notification"""
        return None
    
    def resolve_query_templates(self, info, agent_id, tags=None):
        """Resolve query templates"""
        # Placeholder - would integrate with template manager
        return []
    
    def resolve_query_template(self, info, agent_id, template_id):
        """Resolve single query template"""
        return None
    
    def resolve_permissions(self, info, agent_id):
        """Resolve permissions"""
        # Placeholder - would integrate with access control
        return []

    def resolve_ontoguard_status(self, info):
        """Resolve OntoGuard status"""
        try:
            from ..security.ontoguard_adapter import OntoGuardAdapter
            adapter = OntoGuardAdapter()
            return {
                'enabled': adapter.enabled,
                'active': adapter.enabled and adapter.validator is not None,
                'ontology_loaded': adapter.validator is not None,
                'ontology_path': getattr(adapter.validator, 'ontology_path', None) if adapter.validator else None,
                'triples_count': len(adapter.validator.graph) if adapter.validator and hasattr(adapter.validator, 'graph') else 0,
                'action_rules_count': len(adapter.validator.action_rules) if adapter.validator and hasattr(adapter.validator, 'action_rules') else 0,
            }
        except Exception:
            return {
                'enabled': False,
                'active': False,
                'ontology_loaded': False,
                'ontology_path': None,
                'triples_count': 0,
                'action_rules_count': 0,
            }

    def resolve_ontoguard_validate(self, info, input):
        """Resolve OntoGuard validation"""
        try:
            from ..security.ontoguard_adapter import OntoGuardAdapter
            adapter = OntoGuardAdapter()
            context = {'role': input.get('role')}
            if input.get('user_id'):
                context['user_id'] = input['user_id']
            if input.get('resource_id'):
                context['resource_id'] = input['resource_id']

            result = adapter.validate_action(
                action=input['action'],
                entity_type=input['entity_type'],
                context=context
            )
            return {
                'allowed': result.get('allowed', False),
                'action': input['action'],
                'entity_type': input['entity_type'],
                'role': input.get('role'),
                'reason': result.get('reason'),
                'constraints': result.get('constraints', []),
                'suggestions': result.get('suggestions', []),
            }
        except Exception as e:
            return {
                'allowed': False,
                'action': input['action'],
                'entity_type': input['entity_type'],
                'role': input.get('role'),
                'reason': str(e),
                'constraints': [],
                'suggestions': [],
            }

    def resolve_ontoguard_allowed_actions(self, info, role, entity_type=None):
        """Resolve OntoGuard allowed actions"""
        try:
            from ..security.ontoguard_adapter import OntoGuardAdapter
            adapter = OntoGuardAdapter()
            actions = adapter.get_allowed_actions(role=role, entity_type=entity_type)
            return [
                {
                    'action': a.get('action'),
                    'entity_type': a.get('entity_type'),
                    'constraints': a.get('constraints', []),
                }
                for a in actions
            ]
        except Exception:
            return []

    def resolve_ontoguard_explain_rule(self, info, input):
        """Resolve OntoGuard rule explanation"""
        try:
            from ..security.ontoguard_adapter import OntoGuardAdapter
            adapter = OntoGuardAdapter()
            explanation = adapter.explain_rule(
                action=input['action'],
                entity_type=input['entity_type']
            )
            return {
                'action': input['action'],
                'entity_type': input['entity_type'],
                'allowed_roles': explanation.get('allowed_roles', []),
                'constraints': explanation.get('constraints', []),
                'owl_class': explanation.get('owl_class'),
                'description': explanation.get('description'),
            }
        except Exception:
            return {
                'action': input['action'],
                'entity_type': input['entity_type'],
                'allowed_roles': [],
                'constraints': [],
                'owl_class': None,
                'description': None,
            }

    def resolve_health(self, info):
        """Resolve health check"""
        return {
            'status': 'healthy',
            'service': 'AI Agent Connector',
            'timestamp': datetime.now().isoformat()
        }


# ============================================================================
# Mutations
# ============================================================================

class RegisterAgent(graphene.Mutation):
    """Register a new agent"""
    
    class Arguments:
        input = RegisterAgentInput(required=True)
    
    agent = Field(AgentType)
    success = Boolean()
    message = String()
    
    def mutate(self, info, input):
        """Execute agent registration"""
        if not _agent_registry:
            return RegisterAgent(success=False, message="Agent registry not available")
        
        try:
            # Register agent using existing logic
            result = _agent_registry.register_agent(
                agent_id=input['agent_id'],
                agent_credentials=input['agent_credentials'],
                database=input['database'],
                agent_info=input.get('agent_info')
            )
            
            return RegisterAgent(
                success=True,
                message="Agent registered successfully",
                agent={
                    'agent_id': input['agent_id'],
                    'status': 'active',
                    'api_key': result.get('api_key'),
                    'created_at': None,
                    'database_type': None,
                    'database_name': None,
                    'permissions_count': 0,
                    'last_query_at': None
                }
            )
        except Exception as e:
            return RegisterAgent(success=False, message=str(e))


class ExecuteQuery(graphene.Mutation):
    """Execute a SQL query"""
    
    class Arguments:
        input = ExecuteQueryInput(required=True)
    
    result = Field(QueryResultType)
    success = Boolean()
    message = String()
    
    def mutate(self, info, input):
        """Execute query"""
        # Placeholder - would call actual query execution
        return ExecuteQuery(
            success=True,
            message="Query executed",
            result={
                'data': [],
                'rows': 0,
                'columns': [],
                'execution_time_ms': 0.0,
                'sql': input['query'],
                'confidence': None
            }
        )


class ExecuteNaturalLanguageQuery(graphene.Mutation):
    """Execute a natural language query"""
    
    class Arguments:
        input = NaturalLanguageQueryInput(required=True)
    
    result = Field(QueryResultType)
    success = Boolean()
    message = String()
    
    def mutate(self, info, input):
        """Execute natural language query"""
        # Placeholder - would call actual NL query logic
        return ExecuteNaturalLanguageQuery(
            success=True,
            message="Query executed",
            result={
                'data': [],
                'rows': 0,
                'columns': [],
                'execution_time_ms': 0.0,
                'sql': None,
                'confidence': 0.0
            }
        )


class ConfigureFailover(graphene.Mutation):
    """Configure provider failover"""
    
    class Arguments:
        input = ConfigureFailoverInput(required=True)
    
    config = Field(JSONString)
    success = Boolean()
    message = String()
    
    def mutate(self, info, input):
        """Configure failover"""
        if not _failover_manager:
            return ConfigureFailover(success=False, message="Failover manager not available")
        
        try:
            config = _failover_manager.configure_failover(
                agent_id=input['agent_id'],
                primary_provider_id=input['primary_provider_id'],
                backup_provider_ids=input['backup_provider_ids'],
                health_check_enabled=input.get('health_check_enabled', True),
                auto_failover_enabled=input.get('auto_failover_enabled', True),
                health_check_interval=input.get('health_check_interval'),
                consecutive_failures_threshold=input.get('consecutive_failures_threshold')
            )
            
            return ConfigureFailover(
                success=True,
                message="Failover configured successfully",
                config=config
            )
        except Exception as e:
            return ConfigureFailover(success=False, message=str(e))


class CreateBudgetAlert(graphene.Mutation):
    """Create a budget alert"""
    
    class Arguments:
        input = CreateBudgetAlertInput(required=True)
    
    alert = Field(BudgetAlertType)
    success = Boolean()
    message = String()
    
    def mutate(self, info, input):
        """Create budget alert"""
        if not _cost_tracker:
            return CreateBudgetAlert(success=False, message="Cost tracker not available")
        
        try:
            alert = _cost_tracker.add_budget_alert(
                name=input['name'],
                threshold_usd=input['threshold_usd'],
                period=input['period'],
                notification_emails=input.get('notification_emails'),
                webhook_url=input.get('webhook_url')
            )
            
            return CreateBudgetAlert(
                success=True,
                message="Budget alert created successfully",
                alert={
                    'alert_id': alert.alert_id,
                    'name': alert.name,
                    'threshold_usd': alert.threshold_usd,
                    'period': alert.period,
                    'triggered': alert.triggered,
                    'notification_emails': alert.notification_emails,
                    'webhook_url': alert.webhook_url,
                    'created_at': None
                }
            )
        except Exception as e:
            return CreateBudgetAlert(success=False, message=str(e))


class ValidateOntoGuardAction(graphene.Mutation):
    """Validate an action against OntoGuard ontology rules"""

    class Arguments:
        input = ValidateActionInput(required=True)

    result = Field(OntoGuardValidationResultType)
    success = Boolean()
    message = String()

    def mutate(self, info, input):
        """Execute OntoGuard validation"""
        try:
            from ..security.ontoguard_adapter import OntoGuardAdapter
            adapter = OntoGuardAdapter()
            context = {'role': input.get('role')}
            if input.get('user_id'):
                context['user_id'] = input['user_id']
            if input.get('resource_id'):
                context['resource_id'] = input['resource_id']

            validation_result = adapter.validate_action(
                action=input['action'],
                entity_type=input['entity_type'],
                context=context
            )

            result_dict = validation_result if isinstance(validation_result, dict) else {
                'allowed': getattr(validation_result, 'allowed', False),
                'reason': getattr(validation_result, 'reason', None),
                'constraints': getattr(validation_result, 'constraints', []),
                'suggestions': getattr(validation_result, 'suggestions', []),
            }

            return ValidateOntoGuardAction(
                success=True,
                message="Validation completed",
                result={
                    'allowed': result_dict.get('allowed', False),
                    'action': input['action'],
                    'entity_type': input['entity_type'],
                    'role': input.get('role'),
                    'reason': result_dict.get('reason'),
                    'constraints': result_dict.get('constraints', []),
                    'suggestions': result_dict.get('suggestions', []),
                }
            )
        except Exception as e:
            return ValidateOntoGuardAction(
                success=False,
                message=str(e),
                result={
                    'allowed': False,
                    'action': input['action'],
                    'entity_type': input['entity_type'],
                    'role': input.get('role'),
                    'reason': str(e),
                    'constraints': [],
                    'suggestions': [],
                }
            )


class CheckOntoGuardPermissions(graphene.Mutation):
    """Check if a role has permission for an action on entity type"""

    class Arguments:
        input = CheckPermissionsInput(required=True)

    allowed = Boolean()
    success = Boolean()
    message = String()
    reason = String()
    constraints = List(String)

    def mutate(self, info, input):
        """Execute OntoGuard permissions check"""
        try:
            from ..security.ontoguard_adapter import OntoGuardAdapter
            adapter = OntoGuardAdapter()
            result = adapter.check_permissions(
                role=input['role'],
                action=input['action'],
                entity_type=input['entity_type']
            )

            result_dict = result if isinstance(result, dict) else {
                'allowed': getattr(result, 'allowed', False),
                'reason': getattr(result, 'reason', None),
                'constraints': getattr(result, 'constraints', []),
            }

            return CheckOntoGuardPermissions(
                success=True,
                message="Permissions check completed",
                allowed=result_dict.get('allowed', False),
                reason=result_dict.get('reason'),
                constraints=result_dict.get('constraints', []),
            )
        except Exception as e:
            return CheckOntoGuardPermissions(
                success=False,
                message=str(e),
                allowed=False,
                reason=str(e),
                constraints=[],
            )


class ExplainOntoGuardRule(graphene.Mutation):
    """Get detailed explanation of validation rules for an action"""

    class Arguments:
        input = ExplainRuleInput(required=True)

    explanation = Field(RuleExplanationType)
    success = Boolean()
    message = String()

    def mutate(self, info, input):
        """Execute OntoGuard rule explanation"""
        try:
            from ..security.ontoguard_adapter import OntoGuardAdapter
            adapter = OntoGuardAdapter()
            result = adapter.explain_rule(
                action=input['action'],
                entity_type=input['entity_type']
            )

            result_dict = result if isinstance(result, dict) else {}

            return ExplainOntoGuardRule(
                success=True,
                message="Rule explanation retrieved",
                explanation={
                    'action': input['action'],
                    'entity_type': input['entity_type'],
                    'allowed_roles': result_dict.get('allowed_roles', []),
                    'constraints': result_dict.get('constraints', []),
                    'owl_class': result_dict.get('owl_class'),
                    'description': result_dict.get('description'),
                }
            )
        except Exception as e:
            return ExplainOntoGuardRule(
                success=False,
                message=str(e),
                explanation={
                    'action': input['action'],
                    'entity_type': input['entity_type'],
                    'allowed_roles': [],
                    'constraints': [],
                    'owl_class': None,
                    'description': None,
                }
            )


class Mutation(ObjectType):
    """GraphQL Mutation root"""
    register_agent = RegisterAgent.Field()
    execute_query = ExecuteQuery.Field()
    execute_natural_language_query = ExecuteNaturalLanguageQuery.Field()
    configure_failover = ConfigureFailover.Field()
    create_budget_alert = CreateBudgetAlert.Field()
    # OntoGuard mutations
    validate_ontoguard_action = ValidateOntoGuardAction.Field()
    check_ontoguard_permissions = CheckOntoGuardPermissions.Field()
    explain_ontoguard_rule = ExplainOntoGuardRule.Field()


# ============================================================================
# Subscriptions
# ============================================================================

class Subscription(ObjectType):
    """GraphQL Subscription root for real-time updates"""
    
    cost_updated = Field(
        CostRecordType,
        agent_id=ID()
    )
    
    agent_status_changed = Field(
        AgentType,
        agent_id=ID()
    )
    
    failover_switched = Field(
        FailoverStatsType,
        agent_id=ID()
    )
    
    audit_log_created = Field(
        AuditLogType,
        agent_id=ID()
    )
    
    notification_created = Field(NotificationType)
    
    budget_alert_triggered = Field(BudgetAlertType)


# Create schema
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)
