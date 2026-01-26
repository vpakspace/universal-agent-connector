"""
Main client class for Universal Agent Connector SDK
"""

import requests
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin

from .exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ConnectionError
)


class UniversalAgentConnector:
    """
    Python SDK client for Universal Agent Connector API.
    
    Provides easy access to all API endpoints for managing AI agents,
    database connections, permissions, queries, and more.
    
    Example:
        >>> from universal_agent_connector import UniversalAgentConnector
        >>> client = UniversalAgentConnector(base_url="http://localhost:5000")
        >>> agent = client.agents.register(
        ...     agent_id="my-agent",
        ...     agent_credentials={"api_key": "key", "api_secret": "secret"},
        ...     database={"host": "localhost", "database": "mydb"}
        ... )
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:5000",
        api_key: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """
        Initialize the SDK client.
        
        Args:
            base_url: Base URL of the API server (default: http://localhost:5000)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds (default: 30)
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.base_url = base_url.rstrip('/')
        self.api_url = urljoin(self.base_url, '/api')
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path (e.g., '/agents/register')
            params: Query parameters
            json_data: JSON request body
            **kwargs: Additional arguments for requests
            
        Returns:
            Response JSON data
            
        Raises:
            APIError: If API returns an error
            ConnectionError: If connection fails
        """
        url = urljoin(self.api_url + '/', endpoint.lstrip('/'))
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout,
                verify=self.verify_ssl,
                **kwargs
            )
            
            # Handle errors
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Check your API key.",
                    status_code=401,
                    response=response.json() if response.content else {}
                )
            elif response.status_code == 404:
                raise NotFoundError(
                    response.json().get('message', 'Resource not found'),
                    status_code=404,
                    response=response.json() if response.content else {}
                )
            elif response.status_code == 400:
                raise ValidationError(
                    response.json().get('message', 'Validation error'),
                    status_code=400,
                    response=response.json() if response.content else {}
                )
            elif response.status_code == 429:
                raise RateLimitError(
                    "Rate limit exceeded",
                    status_code=429,
                    response=response.json() if response.content else {}
                )
            elif not response.ok:
                error_data = response.json() if response.content else {}
                raise APIError(
                    error_data.get('message', f'API error: {response.status_code}'),
                    status_code=response.status_code,
                    response=error_data
                )
            
            # Return JSON response
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Connection failed: {str(e)}") from e
    
    # ============================================================================
    # Health & Info
    # ============================================================================
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        return self._request('GET', '/health')
    
    def get_api_docs(self) -> Dict[str, Any]:
        """Get API documentation"""
        return self._request('GET', '/api-docs')
    
    # ============================================================================
    # Agents
    # ============================================================================
    
    def register_agent(
        self,
        agent_id: str,
        agent_credentials: Dict[str, str],
        database: Dict[str, Any],
        agent_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a new AI agent.
        
        Args:
            agent_id: Unique agent identifier
            agent_credentials: API credentials (api_key, api_secret)
            database: Database configuration
            agent_info: Optional agent metadata
            
        Returns:
            Registration response with API key
        """
        data = {
            'agent_id': agent_id,
            'agent_credentials': agent_credentials,
            'database': database
        }
        if agent_info:
            data['agent_info'] = agent_info
        
        return self._request('POST', '/agents/register', json_data=data)
    
    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get agent information"""
        return self._request('GET', f'/agents/{agent_id}')
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        response = self._request('GET', '/agents')
        return response.get('agents', [])
    
    def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """Delete/revoke an agent"""
        return self._request('DELETE', f'/agents/{agent_id}')
    
    def update_agent_database(
        self,
        agent_id: str,
        database: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update agent's database connection"""
        return self._request('PUT', f'/agents/{agent_id}/database', json_data=database)
    
    # ============================================================================
    # Permissions
    # ============================================================================
    
    def set_permissions(
        self,
        agent_id: str,
        permissions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Set permissions for an agent"""
        return self._request(
            'PUT',
            f'/agents/{agent_id}/permissions/resources',
            json_data={'permissions': permissions}
        )
    
    def get_permissions(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get permissions for an agent"""
        response = self._request('GET', f'/agents/{agent_id}/permissions/resources')
        return response.get('permissions', [])
    
    def revoke_permission(
        self,
        agent_id: str,
        resource_id: str
    ) -> Dict[str, Any]:
        """Revoke a specific permission"""
        return self._request(
            'DELETE',
            f'/agents/{agent_id}/permissions/resources/{resource_id}'
        )
    
    # ============================================================================
    # Database
    # ============================================================================
    
    def test_database_connection(self, database: Dict[str, Any]) -> Dict[str, Any]:
        """Test a database connection"""
        return self._request('POST', '/databases/test', json_data=database)
    
    def get_agent_tables(self, agent_id: str) -> List[str]:
        """Get list of tables accessible to an agent"""
        response = self._request('GET', f'/agents/{agent_id}/tables')
        return response.get('tables', [])
    
    def get_access_preview(self, agent_id: str) -> Dict[str, Any]:
        """Get access preview for an agent"""
        return self._request('GET', f'/agents/{agent_id}/access-preview')
    
    # ============================================================================
    # Queries
    # ============================================================================
    
    def execute_query(
        self,
        agent_id: str,
        query: str,
        params: Optional[Dict] = None,
        fetch: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a SQL query.
        
        Args:
            agent_id: Agent identifier
            query: SQL query string
            params: Optional query parameters
            fetch: Whether to fetch results (default: True)
            
        Returns:
            Query results
        """
        data = {'query': query, 'fetch': fetch}
        if params:
            data['params'] = params
        
        return self._request('POST', f'/agents/{agent_id}/query', json_data=data)
    
    def execute_natural_language_query(
        self,
        agent_id: str,
        query: str,
        preview_only: bool = False,
        use_cache: bool = True,
        use_template: Optional[str] = None,
        template_params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute a natural language query (converts to SQL).
        
        Args:
            agent_id: Agent identifier
            query: Natural language query
            preview_only: If True, only return SQL without executing
            use_cache: Whether to use query cache
            use_template: Optional template ID to use
            template_params: Optional template parameters
            
        Returns:
            Query results or SQL preview
        """
        data = {
            'query': query,
            'preview_only': preview_only,
            'use_cache': use_cache
        }
        if use_template:
            data['use_template'] = use_template
        if template_params:
            data['template_params'] = template_params
        
        return self._request(
            'POST',
            f'/agents/{agent_id}/query/natural',
            json_data=data
        )
    
    def get_query_suggestions(
        self,
        agent_id: str,
        query: str,
        num_suggestions: int = 3
    ) -> List[Dict[str, Any]]:
        """Get SQL query suggestions for ambiguous natural language input"""
        response = self._request(
            'POST',
            f'/agents/{agent_id}/query/suggestions',
            json_data={'query': query, 'num_suggestions': num_suggestions}
        )
        return response.get('suggestions', [])
    
    # ============================================================================
    # Query Templates
    # ============================================================================
    
    def create_query_template(
        self,
        agent_id: str,
        name: str,
        sql: str,
        tags: Optional[List[str]] = None,
        is_public: bool = False
    ) -> Dict[str, Any]:
        """Create a query template"""
        data = {'name': name, 'sql': sql, 'is_public': is_public}
        if tags:
            data['tags'] = tags
        
        return self._request(
            'POST',
            f'/agents/{agent_id}/query/templates',
            json_data=data
        )
    
    def list_query_templates(
        self,
        agent_id: str,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """List query templates"""
        params = {}
        if tags:
            params['tags'] = ','.join(tags)
        
        response = self._request('GET', f'/agents/{agent_id}/query/templates', params=params)
        return response.get('templates', [])
    
    def get_query_template(
        self,
        agent_id: str,
        template_id: str
    ) -> Dict[str, Any]:
        """Get a specific query template"""
        return self._request('GET', f'/agents/{agent_id}/query/templates/{template_id}')
    
    def update_query_template(
        self,
        agent_id: str,
        template_id: str,
        **updates
    ) -> Dict[str, Any]:
        """Update a query template"""
        return self._request(
            'PUT',
            f'/agents/{agent_id}/query/templates/{template_id}',
            json_data=updates
        )
    
    def delete_query_template(
        self,
        agent_id: str,
        template_id: str
    ) -> Dict[str, Any]:
        """Delete a query template"""
        return self._request(
            'DELETE',
            f'/agents/{agent_id}/query/templates/{template_id}'
        )
    
    # ============================================================================
    # AI Agents (Admin)
    # ============================================================================
    
    def register_ai_agent(
        self,
        agent_id: str,
        provider: str,
        model: str,
        api_key: Optional[str] = None,
        **config
    ) -> Dict[str, Any]:
        """
        Register an AI agent (OpenAI, Anthropic, or custom).
        
        Args:
            agent_id: Agent identifier
            provider: Provider type ('openai', 'anthropic', 'custom')
            model: Model name
            api_key: API key for the provider
            **config: Additional configuration options
            
        Returns:
            Registration response
        """
        data = {
            'agent_id': agent_id,
            'provider': provider,
            'model': model,
            **config
        }
        if api_key:
            data['api_key'] = api_key
        
        return self._request('POST', '/admin/ai-agents/register', json_data=data)
    
    def list_ai_agents(self) -> List[Dict[str, Any]]:
        """List all registered AI agents"""
        response = self._request('GET', '/admin/ai-agents')
        return response.get('agents', [])
    
    def get_ai_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get AI agent information"""
        return self._request('GET', f'/admin/ai-agents/{agent_id}')
    
    def execute_ai_query(
        self,
        agent_id: str,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute a query using an AI agent"""
        data = {'query': query}
        if context:
            data['context'] = context
        
        return self._request('POST', f'/admin/ai-agents/{agent_id}/query', json_data=data)
    
    def set_rate_limit(
        self,
        agent_id: str,
        queries_per_minute: Optional[int] = None,
        queries_per_hour: Optional[int] = None,
        queries_per_day: Optional[int] = None
    ) -> Dict[str, Any]:
        """Set rate limit for an AI agent"""
        data = {}
        if queries_per_minute is not None:
            data['queries_per_minute'] = queries_per_minute
        if queries_per_hour is not None:
            data['queries_per_hour'] = queries_per_hour
        if queries_per_day is not None:
            data['queries_per_day'] = queries_per_day
        
        return self._request(
            'POST',
            f'/admin/ai-agents/{agent_id}/rate-limit',
            json_data=data
        )
    
    def get_rate_limit(self, agent_id: str) -> Dict[str, Any]:
        """Get rate limit configuration for an AI agent"""
        return self._request('GET', f'/admin/ai-agents/{agent_id}/rate-limit')
    
    def set_retry_policy(
        self,
        agent_id: str,
        enabled: bool = True,
        max_retries: int = 3,
        strategy: str = 'exponential',
        **policy_config
    ) -> Dict[str, Any]:
        """Set retry policy for an AI agent"""
        data = {
            'enabled': enabled,
            'max_retries': max_retries,
            'strategy': strategy,
            **policy_config
        }
        
        return self._request(
            'POST',
            f'/admin/ai-agents/{agent_id}/retry-policy',
            json_data=data
        )
    
    def get_retry_policy(self, agent_id: str) -> Dict[str, Any]:
        """Get retry policy for an AI agent"""
        return self._request('GET', f'/admin/ai-agents/{agent_id}/retry-policy')
    
    def delete_ai_agent(self, agent_id: str) -> Dict[str, Any]:
        """Delete an AI agent"""
        return self._request('DELETE', f'/admin/ai-agents/{agent_id}')
    
    # ============================================================================
    # Provider Failover
    # ============================================================================
    
    def configure_failover(
        self,
        agent_id: str,
        primary_provider_id: str,
        backup_provider_ids: List[str],
        **config_options
    ) -> Dict[str, Any]:
        """Configure provider failover for an agent"""
        data = {
            'primary_provider_id': primary_provider_id,
            'backup_provider_ids': backup_provider_ids,
            **config_options
        }
        
        return self._request('POST', f'/agents/{agent_id}/failover', json_data=data)
    
    def get_failover_config(self, agent_id: str) -> Dict[str, Any]:
        """Get failover configuration for an agent"""
        return self._request('GET', f'/agents/{agent_id}/failover')
    
    def get_failover_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get failover statistics for an agent"""
        return self._request('GET', f'/agents/{agent_id}/failover/stats')
    
    def check_provider_health(self, agent_id: str) -> Dict[str, Any]:
        """Check provider health for an agent"""
        return self._request('GET', f'/agents/{agent_id}/failover/health')
    
    def get_all_provider_health(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        return self._request('GET', '/providers/health')
    
    def switch_provider(
        self,
        agent_id: str,
        provider_id: str
    ) -> Dict[str, Any]:
        """Manually switch to a different provider"""
        return self._request(
            'POST',
            f'/agents/{agent_id}/failover/switch',
            json_data={'provider_id': provider_id}
        )
    
    # ============================================================================
    # Cost Tracking
    # ============================================================================
    
    def get_cost_dashboard(
        self,
        agent_id: Optional[str] = None,
        provider: Optional[str] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get cost dashboard data"""
        params = {'period_days': period_days}
        if agent_id:
            params['agent_id'] = agent_id
        if provider:
            params['provider'] = provider
        
        return self._request('GET', '/cost/dashboard', params=params)
    
    def export_cost_report(
        self,
        format: str = 'json',
        agent_id: Optional[str] = None,
        provider: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Union[str, Dict]:
        """
        Export cost report.
        
        Args:
            format: Export format ('json' or 'csv')
            agent_id: Optional filter by agent
            provider: Optional filter by provider
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            CSV string or JSON dict depending on format
        """
        params = {'format': format}
        if agent_id:
            params['agent_id'] = agent_id
        if provider:
            params['provider'] = provider
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        url = urljoin(self.api_url + '/', '/cost/export'.lstrip('/'))
        response = self.session.get(
            url,
            params=params,
            timeout=self.timeout,
            verify=self.verify_ssl
        )
        
        if not response.ok:
            error_data = response.json() if response.content else {}
            raise APIError(
                error_data.get('message', f'API error: {response.status_code}'),
                status_code=response.status_code,
                response=error_data
            )
        
        if format == 'csv':
            return response.text
        return response.json()
    
    def get_cost_stats(
        self,
        agent_id: Optional[str] = None,
        provider: Optional[str] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get cost statistics"""
        params = {'period_days': period_days}
        if agent_id:
            params['agent_id'] = agent_id
        if provider:
            params['provider'] = provider
        
        return self._request('GET', '/cost/stats', params=params)
    
    def create_budget_alert(
        self,
        name: str,
        threshold_usd: float,
        period: str,
        notification_emails: Optional[List[str]] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a budget alert"""
        data = {
            'name': name,
            'threshold_usd': threshold_usd,
            'period': period
        }
        if notification_emails:
            data['notification_emails'] = notification_emails
        if webhook_url:
            data['webhook_url'] = webhook_url
        
        return self._request('POST', '/cost/budget-alerts', json_data=data)
    
    def list_budget_alerts(self) -> List[Dict[str, Any]]:
        """List all budget alerts"""
        response = self._request('GET', '/cost/budget-alerts')
        return response.get('alerts', [])
    
    def update_budget_alert(
        self,
        alert_id: str,
        **updates
    ) -> Dict[str, Any]:
        """Update a budget alert"""
        return self._request(
            'PUT',
            f'/cost/budget-alerts/{alert_id}',
            json_data=updates
        )
    
    def delete_budget_alert(self, alert_id: str) -> Dict[str, Any]:
        """Delete a budget alert"""
        return self._request('DELETE', f'/cost/budget-alerts/{alert_id}')
    
    def set_custom_pricing(
        self,
        provider: str,
        model: str,
        prompt_per_1m: float,
        completion_per_1m: float
    ) -> Dict[str, Any]:
        """Set custom pricing for a provider/model"""
        return self._request(
            'POST',
            '/cost/custom-pricing',
            json_data={
                'provider': provider,
                'model': model,
                'prompt_per_1m': prompt_per_1m,
                'completion_per_1m': completion_per_1m
            }
        )
    
    # ============================================================================
    # Audit & Notifications
    # ============================================================================
    
    def get_audit_logs(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit logs"""
        params = {'limit': limit}
        if agent_id:
            params['agent_id'] = agent_id
        if action_type:
            params['action_type'] = action_type
        
        response = self._request('GET', '/audit/logs', params=params)
        return response.get('logs', [])
    
    def get_audit_log(self, log_id: int) -> Dict[str, Any]:
        """Get a specific audit log"""
        return self._request('GET', f'/audit/logs/{log_id}')
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit statistics"""
        return self._request('GET', '/audit/statistics')
    
    def get_notifications(
        self,
        unread_only: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get notifications"""
        params = {'limit': limit}
        if unread_only:
            params['unread_only'] = 'true'
        
        response = self._request('GET', '/notifications', params=params)
        return response.get('notifications', [])
    
    def mark_notification_read(self, notification_id: int) -> Dict[str, Any]:
        """Mark a notification as read"""
        return self._request('PUT', f'/notifications/{notification_id}/read')
    
    def mark_all_notifications_read(self) -> Dict[str, Any]:
        """Mark all notifications as read"""
        return self._request('PUT', '/notifications/read-all')
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        return self._request('GET', '/notifications/stats')
    
    # ============================================================================
    # Admin: Database Management
    # ============================================================================
    
    def list_databases(self) -> List[Dict[str, Any]]:
        """List all databases (admin)"""
        response = self._request('GET', '/admin/databases')
        return response.get('databases', [])
    
    def test_admin_database_connection(self, database: Dict[str, Any]) -> Dict[str, Any]:
        """Test database connection (admin)"""
        return self._request('POST', '/admin/databases/test', json_data=database)
    
    def get_database_connections(self) -> List[Dict[str, Any]]:
        """Get all database connections (admin)"""
        response = self._request('GET', '/admin/databases/connections')
        return response.get('connections', [])
    
    def rotate_database_credentials(
        self,
        agent_id: str,
        new_credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rotate database credentials for an agent"""
        return self._request(
            'POST',
            f'/admin/agents/{agent_id}/database/rotate',
            json_data=new_credentials
        )
    
    def activate_database_credentials(self, agent_id: str) -> Dict[str, Any]:
        """Activate rotated database credentials"""
        return self._request('POST', f'/admin/agents/{agent_id}/database/activate')
    
    def rollback_database_credentials(self, agent_id: str) -> Dict[str, Any]:
        """Rollback database credentials to previous version"""
        return self._request('POST', f'/admin/agents/{agent_id}/database/rollback')
    
    def get_database_rotation_status(self, agent_id: str) -> Dict[str, Any]:
        """Get database credential rotation status"""
        return self._request('GET', f'/admin/agents/{agent_id}/database/rotation-status')
    
    # ============================================================================
    # Admin: AI Agent Version Control
    # ============================================================================
    
    def list_ai_agent_versions(self, agent_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List configuration versions for an AI agent"""
        params = {}
        if limit:
            params['limit'] = limit
        
        response = self._request('GET', f'/admin/ai-agents/{agent_id}/versions', params=params)
        return response.get('versions', [])
    
    def get_ai_agent_version(self, agent_id: str, version: int) -> Dict[str, Any]:
        """Get a specific version of AI agent configuration"""
        return self._request('GET', f'/admin/ai-agents/{agent_id}/versions/{version}')
    
    def rollback_ai_agent_config(self, agent_id: str, version: int, description: Optional[str] = None) -> Dict[str, Any]:
        """Rollback AI agent configuration to a previous version"""
        data = {'version': version}
        if description:
            data['description'] = description
        
        return self._request('POST', f'/admin/ai-agents/{agent_id}/rollback', json_data=data)
    
    # ============================================================================
    # Admin: Webhooks
    # ============================================================================
    
    def register_webhook(
        self,
        agent_id: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a webhook for an AI agent"""
        data = {'url': url, 'events': events}
        if secret:
            data['secret'] = secret
        
        return self._request('POST', f'/admin/ai-agents/{agent_id}/webhooks', json_data=data)
    
    def list_webhooks(self, agent_id: str) -> List[Dict[str, Any]]:
        """List webhooks for an AI agent"""
        response = self._request('GET', f'/admin/ai-agents/{agent_id}/webhooks')
        return response.get('webhooks', [])
    
    def delete_webhook(self, agent_id: str, webhook_url: str) -> Dict[str, Any]:
        """Delete a webhook"""
        return self._request('DELETE', f'/admin/ai-agents/{agent_id}/webhooks', params={'url': webhook_url})
    
    def get_webhook_history(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get webhook delivery history"""
        response = self._request('GET', f'/admin/ai-agents/{agent_id}/webhooks/history', params={'limit': limit})
        return response.get('history', [])
    
    # ============================================================================
    # Admin: Row-Level Security (RLS)
    # ============================================================================
    
    def create_rls_rule(
        self,
        agent_id: str,
        table_name: str,
        rule_type: str,
        condition: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a row-level security rule"""
        data = {
            'agent_id': agent_id,
            'table_name': table_name,
            'rule_type': rule_type,
            'condition': condition
        }
        if description:
            data['description'] = description
        
        return self._request('POST', '/admin/rls/rules', json_data=data)
    
    def list_rls_rules(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List RLS rules"""
        params = {}
        if agent_id:
            params['agent_id'] = agent_id
        
        response = self._request('GET', '/admin/rls/rules', params=params)
        return response.get('rules', [])
    
    def delete_rls_rule(self, rule_id: str) -> Dict[str, Any]:
        """Delete an RLS rule"""
        return self._request('DELETE', f'/admin/rls/rules/{rule_id}')
    
    # ============================================================================
    # Admin: Column Masking
    # ============================================================================
    
    def create_masking_rule(
        self,
        agent_id: str,
        table_name: str,
        column_name: str,
        masking_type: str,
        **config
    ) -> Dict[str, Any]:
        """Create a column masking rule"""
        data = {
            'agent_id': agent_id,
            'table_name': table_name,
            'column_name': column_name,
            'masking_type': masking_type,
            **config
        }
        
        return self._request('POST', '/admin/masking/rules', json_data=data)
    
    def list_masking_rules(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List masking rules"""
        params = {}
        if agent_id:
            params['agent_id'] = agent_id
        
        response = self._request('GET', '/admin/masking/rules', params=params)
        return response.get('rules', [])
    
    def delete_masking_rule(self, rule_id: str) -> Dict[str, Any]:
        """Delete a masking rule"""
        return self._request('DELETE', '/admin/masking/rules', params={'rule_id': rule_id})
    
    # ============================================================================
    # Admin: Query Management
    # ============================================================================
    
    def set_query_limits(
        self,
        agent_id: str,
        max_rows: Optional[int] = None,
        max_execution_time: Optional[int] = None,
        max_query_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Set query execution limits for an agent"""
        data = {}
        if max_rows is not None:
            data['max_rows'] = max_rows
        if max_execution_time is not None:
            data['max_execution_time'] = max_execution_time
        if max_query_size is not None:
            data['max_query_size'] = max_query_size
        
        return self._request('POST', f'/admin/agents/{agent_id}/query-limits', json_data=data)
    
    def get_query_limits(self, agent_id: str) -> Dict[str, Any]:
        """Get query execution limits for an agent"""
        return self._request('GET', f'/admin/agents/{agent_id}/query-limits')
    
    def validate_query(
        self,
        agent_id: str,
        query: str
    ) -> Dict[str, Any]:
        """Validate a query before execution"""
        return self._request(
            'POST',
            f'/admin/agents/{agent_id}/validate-query',
            json_data={'query': query}
        )
    
    def list_query_approvals(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List pending query approvals"""
        params = {'limit': limit}
        if status:
            params['status'] = status
        
        response = self._request('GET', '/admin/query-approvals', params=params)
        return response.get('approvals', [])
    
    def approve_query(self, approval_id: str) -> Dict[str, Any]:
        """Approve a pending query"""
        return self._request('POST', f'/admin/query-approvals/{approval_id}/approve')
    
    def reject_query(self, approval_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Reject a pending query"""
        data = {}
        if reason:
            data['reason'] = reason
        
        return self._request('POST', f'/admin/query-approvals/{approval_id}/reject', json_data=data)
    
    def get_query_approval(self, approval_id: str) -> Dict[str, Any]:
        """Get a specific query approval"""
        return self._request('GET', f'/admin/query-approvals/{approval_id}')
    
    # ============================================================================
    # Admin: Approved Patterns
    # ============================================================================
    
    def create_approved_pattern(
        self,
        name: str,
        sql_template: str,
        natural_language_keywords: List[str],
        description: Optional[str] = None,
        **config
    ) -> Dict[str, Any]:
        """Create an approved query pattern"""
        data = {
            'name': name,
            'sql_template': sql_template,
            'natural_language_keywords': natural_language_keywords,
            **config
        }
        if description:
            data['description'] = description
        
        return self._request('POST', '/admin/query-patterns', json_data=data)
    
    def list_approved_patterns(self) -> List[Dict[str, Any]]:
        """List all approved query patterns"""
        response = self._request('GET', '/admin/query-patterns')
        return response.get('patterns', [])
    
    def get_approved_pattern(self, pattern_id: str) -> Dict[str, Any]:
        """Get a specific approved pattern"""
        return self._request('GET', f'/admin/query-patterns/{pattern_id}')
    
    def update_approved_pattern(
        self,
        pattern_id: str,
        **updates
    ) -> Dict[str, Any]:
        """Update an approved pattern"""
        return self._request('PUT', f'/admin/query-patterns/{pattern_id}', json_data=updates)
    
    def delete_approved_pattern(self, pattern_id: str) -> Dict[str, Any]:
        """Delete an approved pattern"""
        return self._request('DELETE', f'/admin/query-patterns/{pattern_id}')
    
    # ============================================================================
    # Admin: Query Cache
    # ============================================================================
    
    def set_cache_ttl(
        self,
        agent_id: str,
        ttl_seconds: int
    ) -> Dict[str, Any]:
        """Set cache TTL for an agent"""
        return self._request(
            'POST',
            f'/admin/agents/{agent_id}/cache/ttl',
            json_data={'ttl_seconds': ttl_seconds}
        )
    
    def get_cache_ttl(self, agent_id: str) -> Dict[str, Any]:
        """Get cache TTL for an agent"""
        return self._request('GET', f'/admin/agents/{agent_id}/cache/ttl')
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self._request('GET', '/admin/cache/stats')
    
    def invalidate_cache(
        self,
        agent_id: Optional[str] = None,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """Invalidate cache entries"""
        data = {}
        if agent_id:
            data['agent_id'] = agent_id
        if pattern:
            data['pattern'] = pattern
        
        return self._request('POST', '/admin/cache/invalidate', json_data=data)
    
    def clear_expired_cache(self) -> Dict[str, Any]:
        """Clear expired cache entries"""
        return self._request('POST', '/admin/cache/clear-expired')
    
    def list_cache_entries(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List cache entries"""
        params = {'limit': limit}
        if agent_id:
            params['agent_id'] = agent_id
        
        response = self._request('GET', '/admin/cache/entries', params=params)
        return response.get('entries', [])
    
    # ============================================================================
    # Admin: Audit Export
    # ============================================================================
    
    def export_audit_logs(
        self,
        format: str = 'json',
        agent_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Union[str, Dict]:
        """Export audit logs"""
        params = {'format': format}
        if agent_id:
            params['agent_id'] = agent_id
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        url = urljoin(self.api_url + '/', '/admin/audit/export'.lstrip('/'))
        response = self.session.get(
            url,
            params=params,
            timeout=self.timeout,
            verify=self.verify_ssl
        )
        
        if not response.ok:
            error_data = response.json() if response.content else {}
            raise APIError(
                error_data.get('message', f'API error: {response.status_code}'),
                status_code=response.status_code,
                response=error_data
            )
        
        if format == 'csv':
            return response.text
        return response.json()
    
    def get_audit_export_summary(
        self,
        agent_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get audit export summary"""
        params = {}
        if agent_id:
            params['agent_id'] = agent_id
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        return self._request('GET', '/admin/audit/export/summary', params=params)
    
    # ============================================================================
    # Admin: Alerts
    # ============================================================================
    
    def create_alert_rule(
        self,
        name: str,
        condition: str,
        severity: str,
        **config
    ) -> Dict[str, Any]:
        """Create an alert rule"""
        data = {
            'name': name,
            'condition': condition,
            'severity': severity,
            **config
        }
        
        return self._request('POST', '/admin/alerts/rules', json_data=data)
    
    def list_alert_rules(self) -> List[Dict[str, Any]]:
        """List alert rules"""
        response = self._request('GET', '/admin/alerts/rules')
        return response.get('rules', [])
    
    def get_alert_rule(self, rule_id: str) -> Dict[str, Any]:
        """Get a specific alert rule"""
        return self._request('GET', f'/admin/alerts/rules/{rule_id}')
    
    def update_alert_rule(
        self,
        rule_id: str,
        **updates
    ) -> Dict[str, Any]:
        """Update an alert rule"""
        return self._request('PUT', f'/admin/alerts/rules/{rule_id}', json_data=updates)
    
    def delete_alert_rule(self, rule_id: str) -> Dict[str, Any]:
        """Delete an alert rule"""
        return self._request('DELETE', f'/admin/alerts/rules/{rule_id}')
    
    def list_alerts(
        self,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List alerts"""
        params = {'limit': limit}
        if severity:
            params['severity'] = severity
        if acknowledged is not None:
            params['acknowledged'] = 'true' if acknowledged else 'false'
        
        response = self._request('GET', '/admin/alerts', params=params)
        return response.get('alerts', [])
    
    def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        """Acknowledge an alert"""
        return self._request('POST', f'/admin/alerts/{alert_id}/acknowledge')
    
    # ============================================================================
    # Admin: Query Tracing
    # ============================================================================
    
    def list_query_traces(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List query traces"""
        params = {'limit': limit}
        if agent_id:
            params['agent_id'] = agent_id
        
        response = self._request('GET', '/admin/traces', params=params)
        return response.get('traces', [])
    
    def get_query_trace(self, trace_id: str) -> Dict[str, Any]:
        """Get a specific query trace"""
        return self._request('GET', f'/admin/traces/{trace_id}')
    
    def get_observability_config(self) -> Dict[str, Any]:
        """Get observability configuration"""
        return self._request('GET', '/admin/observability/config')
    
    # ============================================================================
    # Admin: Teams
    # ============================================================================
    
    def create_team(
        self,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a team"""
        data = {'name': name}
        if description:
            data['description'] = description
        
        return self._request('POST', '/admin/teams', json_data=data)
    
    def list_teams(self) -> List[Dict[str, Any]]:
        """List all teams"""
        response = self._request('GET', '/admin/teams')
        return response.get('teams', [])
    
    def get_team(self, team_id: str) -> Dict[str, Any]:
        """Get team information"""
        return self._request('GET', f'/admin/teams/{team_id}')
    
    def update_team(
        self,
        team_id: str,
        **updates
    ) -> Dict[str, Any]:
        """Update a team"""
        return self._request('PUT', f'/admin/teams/{team_id}', json_data=updates)
    
    def delete_team(self, team_id: str) -> Dict[str, Any]:
        """Delete a team"""
        return self._request('DELETE', f'/admin/teams/{team_id}')
    
    def add_team_member(
        self,
        team_id: str,
        user_id: str,
        role: str
    ) -> Dict[str, Any]:
        """Add a member to a team"""
        return self._request(
            'POST',
            f'/admin/teams/{team_id}/members',
            json_data={'user_id': user_id, 'role': role}
        )
    
    def remove_team_member(
        self,
        team_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Remove a member from a team"""
        return self._request('DELETE', f'/admin/teams/{team_id}/members/{user_id}')
    
    def update_team_member_role(
        self,
        team_id: str,
        user_id: str,
        role: str
    ) -> Dict[str, Any]:
        """Update a team member's role"""
        return self._request(
            'PUT',
            f'/admin/teams/{team_id}/members/{user_id}/role',
            json_data={'role': role}
        )
    
    def assign_agent_to_team(
        self,
        team_id: str,
        agent_id: str
    ) -> Dict[str, Any]:
        """Assign an agent to a team"""
        return self._request('POST', f'/admin/teams/{team_id}/agents/{agent_id}')
    
    # ============================================================================
    # Query Sharing
    # ============================================================================
    
    def share_query(
        self,
        agent_id: str,
        query: str,
        expires_at: Optional[str] = None,
        access_level: str = 'read'
    ) -> Dict[str, Any]:
        """Share a query with a shareable link"""
        data = {'query': query, 'access_level': access_level}
        if expires_at:
            data['expires_at'] = expires_at
        
        return self._request('POST', f'/agents/{agent_id}/queries/share', json_data=data)
    
    def get_shared_query(self, share_id: str) -> Dict[str, Any]:
        """Get a shared query by share ID"""
        return self._request('GET', f'/shared/{share_id}')
    
    def list_shared_queries(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List shared queries for an agent"""
        response = self._request('GET', f'/agents/{agent_id}/queries/shares', params={'limit': limit})
        return response.get('shares', [])
    
    # ============================================================================
    # Admin: Dashboard
    # ============================================================================
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get dashboard metrics (admin)"""
        return self._request('GET', '/admin/dashboard/metrics')
