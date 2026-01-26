"""
AI Agent Manager
Manages AI agent providers, rate limiting, retry policies, version control, and webhooks
"""

from typing import Dict, Optional, Any, List
from ..agents.providers import (
    AgentProvider,
    AgentConfiguration,
    create_agent_provider,
    BaseAgentProvider
)
from ..utils.rate_limiter import RateLimiter, RateLimitConfig
from ..utils.retry_policy import RetryPolicy, RetryExecutor
from ..utils.version_control import ConfigurationVersionControl, ConfigurationVersion
from ..utils.webhooks import WebhookNotifier, WebhookEvent, WebhookConfig
from ..utils.provider_failover import ProviderFailoverManager
from ..utils.helpers import get_timestamp
from ..utils.air_gapped import AirGappedModeError

# Global cost tracker instance (will be initialized in routes.py)
_cost_tracker = None

def set_cost_tracker(tracker):
    """Set the global cost tracker instance"""
    global _cost_tracker
    _cost_tracker = tracker


class AIAgentManager:
    """
    Comprehensive AI agent management system.
    Handles provider registration, rate limiting, retries, versioning, and webhooks.
    """
    
    def __init__(self):
        """Initialize AI agent manager"""
        # agent_id -> AgentConfiguration
        self._configurations: Dict[str, AgentConfiguration] = {}
        # agent_id -> BaseAgentProvider
        self._providers: Dict[str, BaseAgentProvider] = {}
        # Rate limiter
        self._rate_limiter = RateLimiter()
        # agent_id -> RetryPolicy
        self._retry_policies: Dict[str, RetryPolicy] = {}
        # Version control
        self._version_control = ConfigurationVersionControl()
        # Webhook notifier
        self._webhook_notifier = WebhookNotifier()
        # Provider failover manager
        self._failover_manager = ProviderFailoverManager()
    
    def register_ai_agent(
        self,
        agent_id: str,
        config: AgentConfiguration,
        rate_limit: Optional[RateLimitConfig] = None,
        retry_policy: Optional[RetryPolicy] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register a new AI agent with full configuration.
        
        Args:
            agent_id: Unique agent identifier
            config: Agent configuration
            rate_limit: Optional rate limit configuration
            retry_policy: Optional retry policy
            description: Optional description for version control
            created_by: Optional creator identifier
            
        Returns:
            Dict containing registration details
            
        Raises:
            ValueError: If agent already exists or configuration is invalid
            AirGappedModeError: If external provider is used in air-gapped mode
        """
        if agent_id in self._configurations:
            raise ValueError(f"AI agent {agent_id} already registered")
        
        # Validate configuration (this will also check air-gapped mode)
        provider = create_agent_provider(config)
        if not provider.validate_configuration():
            raise ValueError(f"Invalid configuration for agent {agent_id}")
        
        # Store configuration
        self._configurations[agent_id] = config
        self._providers[agent_id] = provider
        
        # Register provider with failover manager (using agent_id as provider_id)
        self._failover_manager.register_provider(agent_id, provider)
        
        # Set rate limits
        if rate_limit:
            self._rate_limiter.set_rate_limit(agent_id, rate_limit)
        
        # Set retry policy
        if retry_policy:
            self._retry_policies[agent_id] = retry_policy
        else:
            # Default retry policy
            self._retry_policies[agent_id] = RetryPolicy()
        
        # Create initial version
        version = self._version_control.create_version(
            agent_id=agent_id,
            config=config.to_dict(),
            description=description or "Initial configuration",
            created_by=created_by
        )
        
        # Notify webhook
        self._webhook_notifier.notify(
            event=WebhookEvent.AGENT_REGISTERED,
            agent_id=agent_id,
            data={
                'provider': config.provider.value,
                'model': config.model,
                'version': version.version
            }
        )
        
        return {
            'agent_id': agent_id,
            'provider': config.provider.value,
            'model': config.model,
            'version': version.version,
            'registered_at': get_timestamp()
        }
    
    def update_ai_agent_configuration(
        self,
        agent_id: str,
        config_updates: Dict[str, Any],
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> ConfigurationVersion:
        """
        Update AI agent configuration (creates new version).
        
        Args:
            agent_id: Agent identifier
            config_updates: Dictionary of configuration updates
            description: Description of changes
            created_by: Creator identifier
            
        Returns:
            ConfigurationVersion: New version created
            
        Raises:
            ValueError: If agent not found or configuration invalid
        """
        if agent_id not in self._configurations:
            raise ValueError(f"AI agent {agent_id} not found")
        
        # Get current config
        current_config = self._configurations[agent_id]
        current_dict = current_config.to_dict()
        
        # Update with new values
        updated_dict = {**current_dict, **config_updates}
        updated_dict.pop('api_key', None)  # Don't include masked API key
        
        # Create new configuration
        new_config = AgentConfiguration.from_dict(updated_dict)
        
        # Validate
        provider = create_agent_provider(new_config)
        if not provider.validate_configuration():
            raise ValueError(f"Invalid updated configuration for agent {agent_id}")
        
        # Update stored configuration
        self._configurations[agent_id] = new_config
        self._providers[agent_id] = provider
        
        # Create new version
        version = self._version_control.create_version(
            agent_id=agent_id,
            config=new_config.to_dict(),
            description=description or "Configuration updated",
            created_by=created_by
        )
        
        # Notify webhook
        self._webhook_notifier.notify(
            event=WebhookEvent.CONFIGURATION_CHANGED,
            agent_id=agent_id,
            data={
                'version': version.version,
                'changes': config_updates
            }
        )
        
        return version
    
    def execute_query(
        self,
        agent_id: str,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a query using an AI agent.
        Includes rate limiting, retry logic, and webhook notifications.
        
        Args:
            agent_id: Agent identifier
            query: Query or prompt
            context: Optional context
            
        Returns:
            Dict containing response and metadata
            
        Raises:
            ValueError: If agent not found
            RuntimeError: If rate limit exceeded or query fails after retries
        """
        if agent_id not in self._providers:
            raise ValueError(f"AI agent {agent_id} not found")
        
        # Check rate limit
        allowed, error_msg = self._rate_limiter.check_rate_limit(agent_id)
        if not allowed:
            self._webhook_notifier.notify(
                event=WebhookEvent.RATE_LIMIT_EXCEEDED,
                agent_id=agent_id,
                data={'error': error_msg}
            )
            raise RuntimeError(error_msg)
        
        # Check if failover is configured
        failover_config = self._failover_manager.get_failover_config(agent_id)
        
        try:
            if failover_config and failover_config.auto_failover_enabled:
                # Use failover manager for execution
                try:
                    result, provider_used = self._failover_manager.execute_with_failover(
                        agent_id=agent_id,
                        query=query,
                        context=context
                    )
                except Exception as e:
                    # If failover fails, try with retry policy on primary provider
                    provider = self._providers[agent_id]
                    retry_policy = self._retry_policies.get(agent_id, RetryPolicy())
                    retry_executor = RetryExecutor(retry_policy)
                    
                    def _execute():
                        return provider.execute_query(query, context)
                    
                    result = retry_executor.execute(_execute)
                    provider_used = agent_id
            else:
                # Use standard retry logic
                provider = self._providers[agent_id]
                retry_policy = self._retry_policies.get(agent_id, RetryPolicy())
                retry_executor = RetryExecutor(retry_policy)
                
                # Execute with retry
                def _execute():
                    return provider.execute_query(query, context)
                
                result = retry_executor.execute(_execute)
                provider_used = agent_id
                
                # Track cost (if not already tracked by provider)
                if _cost_tracker and result.get('usage'):
                    try:
                        _cost_tracker.track_call(
                            provider=result.get('provider', 'unknown'),
                            model=result.get('model', 'unknown'),
                            usage=result.get('usage', {}),
                            agent_id=agent_id,
                            operation_type='query',
                            metadata={'query_length': len(query)}
                        )
                    except Exception:
                        pass  # Don't fail if cost tracking fails
                
                # Notify success
                self._webhook_notifier.notify(
                    event=WebhookEvent.QUERY_SUCCESS,
                    agent_id=agent_id,
                    data={
                        'query_length': len(query),
                        'response_length': len(result.get('response', '')),
                        'usage': result.get('usage', {})
                    }
                )
                
                return result
        except Exception as e:
            # Notify failure
            self._webhook_notifier.notify(
                event=WebhookEvent.QUERY_FAILURE,
                agent_id=agent_id,
                data={
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            )
            raise
    
    def set_rate_limit(
        self,
        agent_id: str,
        rate_limit: RateLimitConfig
    ) -> None:
        """Set rate limit for an agent"""
        if agent_id not in self._configurations:
            raise ValueError(f"AI agent {agent_id} not found")
        self._rate_limiter.set_rate_limit(agent_id, rate_limit)
    
    def get_rate_limit(self, agent_id: str) -> Optional[RateLimitConfig]:
        """Get rate limit configuration for an agent"""
        return self._rate_limiter.get_rate_limit(agent_id)
    
    def get_rate_limit_usage(self, agent_id: str) -> Dict[str, Any]:
        """Get current rate limit usage statistics"""
        return self._rate_limiter.get_usage_stats(agent_id)
    
    def set_retry_policy(
        self,
        agent_id: str,
        retry_policy: RetryPolicy
    ) -> None:
        """Set retry policy for an agent"""
        if agent_id not in self._configurations:
            raise ValueError(f"AI agent {agent_id} not found")
        self._retry_policies[agent_id] = retry_policy
    
    def get_retry_policy(self, agent_id: str) -> Optional[RetryPolicy]:
        """Get retry policy for an agent"""
        return self._retry_policies.get(agent_id)
    
    def rollback_configuration(
        self,
        agent_id: str,
        version: int,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> ConfigurationVersion:
        """
        Rollback agent configuration to a previous version.
        
        Args:
            agent_id: Agent identifier
            version: Version to rollback to
            description: Description for rollback
            created_by: Creator identifier
            
        Returns:
            ConfigurationVersion: New version created from rollback
        """
        version_obj = self._version_control.rollback_to_version(
            agent_id=agent_id,
            version=version,
            description=description,
            created_by=created_by
        )
        
        # Update current configuration
        config = AgentConfiguration.from_dict(version_obj.config)
        self._configurations[agent_id] = config
        self._providers[agent_id] = create_agent_provider(config)
        
        # Notify webhook
        self._webhook_notifier.notify(
            event=WebhookEvent.CONFIGURATION_CHANGED,
            agent_id=agent_id,
            data={
                'version': version_obj.version,
                'rollback_to': version,
                'type': 'rollback'
            }
        )
        
        return version_obj
    
    def get_configuration_version(
        self,
        agent_id: str,
        version: Optional[int] = None
    ) -> Optional[ConfigurationVersion]:
        """Get a specific version of configuration"""
        return self._version_control.get_version(agent_id, version)
    
    def list_configuration_versions(
        self,
        agent_id: str,
        limit: Optional[int] = None
    ) -> List[ConfigurationVersion]:
        """List all configuration versions for an agent"""
        return self._version_control.list_versions(agent_id, limit)
    
    def register_webhook(
        self,
        agent_id: Optional[str],
        webhook_config: WebhookConfig
    ) -> str:
        """Register a webhook for an agent or globally"""
        return self._webhook_notifier.register_webhook(agent_id, webhook_config)
    
    def unregister_webhook(
        self,
        agent_id: Optional[str],
        webhook_url: str
    ) -> bool:
        """Unregister a webhook"""
        return self._webhook_notifier.unregister_webhook(agent_id, webhook_url)
    
    def get_webhooks(self, agent_id: Optional[str] = None) -> List[WebhookConfig]:
        """Get webhooks for an agent or globally"""
        return self._webhook_notifier.get_webhooks(agent_id)
    
    def get_webhook_delivery_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get webhook delivery history"""
        return self._webhook_notifier.get_delivery_history(agent_id, limit)
    
    def get_webhook_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get webhook delivery statistics"""
        return self._webhook_notifier.get_delivery_stats(agent_id)
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information"""
        if agent_id not in self._configurations:
            return None
        
        config = self._configurations[agent_id]
        rate_limit = self._rate_limiter.get_rate_limit(agent_id)
        retry_policy = self._retry_policies.get(agent_id)
        current_version = self._version_control.get_current_version(agent_id)
        
        return {
            'agent_id': agent_id,
            'configuration': config.to_dict(),
            'rate_limit': rate_limit.to_dict() if rate_limit else None,
            'retry_policy': retry_policy.to_dict() if retry_policy else None,
            'current_version': current_version,
            'webhooks_count': len(self._webhook_notifier.get_webhooks(agent_id))
        }
    
    def list_agents(self) -> List[str]:
        """List all registered AI agent IDs"""
        return list(self._configurations.keys())
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an AI agent"""
        if agent_id not in self._configurations:
            return False
        
        self._configurations.pop(agent_id, None)
        self._providers.pop(agent_id, None)
        self._rate_limiter.remove_agent(agent_id)
        self._retry_policies.pop(agent_id, None)
        self._version_control.delete_agent_versions(agent_id)
        self._failover_manager.remove_agent(agent_id)
        
        # Notify webhook
        self._webhook_notifier.notify(
            event=WebhookEvent.AGENT_REVOKED,
            agent_id=agent_id,
            data={}
        )
        
        return True
    
    def configure_failover(
        self,
        agent_id: str,
        primary_provider_id: str,
        backup_provider_ids: Optional[List[str]] = None,
        **config_options
    ) -> Dict[str, Any]:
        """
        Configure failover for an agent.
        
        Args:
            agent_id: Agent identifier (the agent that will use failover)
            primary_provider_id: Primary provider agent ID (must be registered)
            backup_provider_ids: List of backup provider agent IDs (must be registered)
            **config_options: Additional failover configuration options
            
        Returns:
            Dict containing failover configuration
        """
        if agent_id not in self._providers:
            raise ValueError(f"Agent {agent_id} not found")
        
        if primary_provider_id not in self._providers:
            raise ValueError(f"Primary provider {primary_provider_id} not found")
        
        # Ensure providers are registered with failover manager
        if primary_provider_id not in self._failover_manager._providers:
            primary_provider = self._providers[primary_provider_id]
            self._failover_manager.register_provider(primary_provider_id, primary_provider)
        
        # Register backup providers
        for backup_id in (backup_provider_ids or []):
            if backup_id not in self._providers:
                raise ValueError(f"Backup provider {backup_id} not found")
            if backup_id not in self._failover_manager._providers:
                backup_provider = self._providers[backup_id]
                self._failover_manager.register_provider(backup_id, backup_provider)
        
        # Configure failover
        config = self._failover_manager.configure_failover(
            agent_id=agent_id,
            primary_provider_id=primary_provider_id,
            backup_provider_ids=backup_provider_ids or [],
            **config_options
        )
        
        return config.to_dict()
    
    def get_failover_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get failover configuration for an agent"""
        config = self._failover_manager.get_failover_config(agent_id)
        return config.to_dict() if config else None
    
    def get_provider_health(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get provider health status"""
        if agent_id:
            health = self._failover_manager.get_provider_health(agent_id)
            return health.to_dict() if health else {}
        else:
            all_health = self._failover_manager.get_all_provider_health()
            return {pid: h.to_dict() for pid, h in all_health.items()}
    
    def get_failover_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get failover statistics for an agent"""
        return self._failover_manager.get_failover_stats(agent_id)

