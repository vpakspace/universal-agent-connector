"""
AI Provider Failover System
Provides automatic failover between AI providers (e.g., OpenAI → Claude)
with health checks and retry logic
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import time
import threading

from ..agents.providers import (
    BaseAgentProvider, AgentConfiguration, AgentProvider,
    create_agent_provider
)
from ..utils.helpers import get_timestamp


class ProviderHealthStatus(Enum):
    """Provider health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    CHECKING = "checking"


@dataclass
class ProviderHealth:
    """Provider health information"""
    provider_id: str
    status: ProviderHealthStatus
    last_check: Optional[str] = None
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    consecutive_failures: int = 0
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'provider_id': self.provider_id,
            'status': self.status.value,
            'last_check': self.last_check,
            'last_success': self.last_success,
            'last_failure': self.last_failure,
            'consecutive_failures': self.consecutive_failures,
            'response_time_ms': self.response_time_ms,
            'error_message': self.error_message
        }


@dataclass
class FailoverConfig:
    """Failover configuration for an agent"""
    agent_id: str
    primary_provider_id: str
    backup_provider_ids: List[str] = field(default_factory=list)
    health_check_enabled: bool = True
    health_check_interval: int = 60  # seconds
    health_check_timeout: int = 5  # seconds
    max_consecutive_failures: int = 3  # Switch after N failures
    auto_failover_enabled: bool = True
    health_check_query: str = "Hello"  # Simple query for health checks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'agent_id': self.agent_id,
            'primary_provider_id': self.primary_provider_id,
            'backup_provider_ids': self.backup_provider_ids,
            'health_check_enabled': self.health_check_enabled,
            'health_check_interval': self.health_check_interval,
            'health_check_timeout': self.health_check_timeout,
            'max_consecutive_failures': self.max_consecutive_failures,
            'auto_failover_enabled': self.auto_failover_enabled,
            'health_check_query': self.health_check_query
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FailoverConfig':
        """Create from dictionary"""
        return cls(
            agent_id=data['agent_id'],
            primary_provider_id=data['primary_provider_id'],
            backup_provider_ids=data.get('backup_provider_ids', []),
            health_check_enabled=data.get('health_check_enabled', True),
            health_check_interval=data.get('health_check_interval', 60),
            health_check_timeout=data.get('health_check_timeout', 5),
            max_consecutive_failures=data.get('max_consecutive_failures', 3),
            auto_failover_enabled=data.get('auto_failover_enabled', True),
            health_check_query=data.get('health_check_query', 'Hello')
        )


class ProviderFailoverManager:
    """
    Manages automatic failover between AI providers.
    Provides health checks, automatic switching, and retry logic.
    """
    
    def __init__(self):
        """Initialize failover manager"""
        # agent_id -> FailoverConfig
        self._failover_configs: Dict[str, FailoverConfig] = {}
        # provider_id -> ProviderHealth
        self._provider_health: Dict[str, ProviderHealth] = {}
        # agent_id -> List[provider_id] (ordered list of providers to try)
        self._provider_chain: Dict[str, List[str]] = {}
        # agent_id -> provider_id (current active provider)
        self._active_providers: Dict[str, str] = {}
        # provider_id -> BaseAgentProvider
        self._providers: Dict[str, BaseAgentProvider] = {}
        # Lock for thread safety
        self._lock = threading.Lock()
        # Health check threads
        self._health_check_threads: Dict[str, threading.Thread] = {}
        self._stop_health_checks = False
    
    def register_provider(
        self,
        provider_id: str,
        provider: BaseAgentProvider
    ) -> None:
        """
        Register a provider instance.
        
        Args:
            provider_id: Unique identifier for the provider
            provider: Provider instance
        """
        with self._lock:
            self._providers[provider_id] = provider
            if provider_id not in self._provider_health:
                self._provider_health[provider_id] = ProviderHealth(
                    provider_id=provider_id,
                    status=ProviderHealthStatus.UNKNOWN
                )
    
    def configure_failover(
        self,
        agent_id: str,
        primary_provider_id: str,
        backup_provider_ids: Optional[List[str]] = None,
        **config_options
    ) -> FailoverConfig:
        """
        Configure failover for an agent.
        
        Args:
            agent_id: Agent identifier
            primary_provider_id: Primary provider ID
            backup_provider_ids: List of backup provider IDs (in order)
            **config_options: Additional configuration options
            
        Returns:
            FailoverConfig: Created configuration
        """
        with self._lock:
            config = FailoverConfig(
                agent_id=agent_id,
                primary_provider_id=primary_provider_id,
                backup_provider_ids=backup_provider_ids or [],
                **config_options
            )
            
            self._failover_configs[agent_id] = config
            self._active_providers[agent_id] = primary_provider_id
            
            # Build provider chain (primary + backups)
            provider_chain = [primary_provider_id] + (backup_provider_ids or [])
            self._provider_chain[agent_id] = provider_chain
            
            # Start health checks if enabled
            if config.health_check_enabled:
                self._start_health_checks(agent_id)
            
            return config
    
    def get_failover_config(self, agent_id: str) -> Optional[FailoverConfig]:
        """Get failover configuration for an agent"""
        return self._failover_configs.get(agent_id)
    
    def check_provider_health(
        self,
        provider_id: str,
        timeout: Optional[int] = None
    ) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Check health of a provider.
        
        Args:
            provider_id: Provider identifier
            timeout: Optional timeout in seconds
            
        Returns:
            Tuple of (is_healthy, error_message, response_time_ms)
        """
        if provider_id not in self._providers:
            return False, f"Provider {provider_id} not found", None
        
        provider = self._providers[provider_id]
        health = self._provider_health.get(provider_id)
        
        if not health:
            health = ProviderHealth(
                provider_id=provider_id,
                status=ProviderHealthStatus.UNKNOWN
            )
            self._provider_health[provider_id] = health
        
        # Update status to checking
        health.status = ProviderHealthStatus.CHECKING
        health.last_check = get_timestamp()
        
        try:
            # Simple health check query
            start_time = time.time()
            
            # Use a simple query for health check
            test_query = "Hello"
            test_context = {'system_prompt': 'You are a helpful assistant. Respond briefly.'}
            
            # Set timeout if provided
            original_timeout = None
            if timeout and hasattr(provider, 'config'):
                original_timeout = provider.config.timeout
                provider.config.timeout = timeout
            
            try:
                result = provider.execute_query(test_query, test_context)
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Restore original timeout
                if original_timeout is not None:
                    provider.config.timeout = original_timeout
                
                # Success
                health.status = ProviderHealthStatus.HEALTHY
                health.last_success = get_timestamp()
                health.consecutive_failures = 0
                health.response_time_ms = response_time
                health.error_message = None
                
                return True, None, response_time
                
            except Exception as e:
                # Restore original timeout
                if original_timeout is not None:
                    provider.config.timeout = original_timeout
                
                error_msg = str(e)
                health.status = ProviderHealthStatus.UNHEALTHY
                health.last_failure = get_timestamp()
                health.consecutive_failures += 1
                health.error_message = error_msg
                
                return False, error_msg, None
                
        except Exception as e:
            health.status = ProviderHealthStatus.UNHEALTHY
            health.last_failure = get_timestamp()
            health.consecutive_failures += 1
            health.error_message = str(e)
            return False, str(e), None
    
    def get_provider_health(self, provider_id: str) -> Optional[ProviderHealth]:
        """Get health status for a provider"""
        return self._provider_health.get(provider_id)
    
    def get_all_provider_health(self) -> Dict[str, ProviderHealth]:
        """Get health status for all providers"""
        return self._provider_health.copy()
    
    def execute_with_failover(
        self,
        agent_id: str,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Execute a query with automatic failover.
        
        Args:
            agent_id: Agent identifier
            query: Query to execute
            context: Optional context
            
        Returns:
            Tuple of (result, provider_id_used)
            
        Raises:
            ValueError: If agent not configured for failover
            RuntimeError: If all providers fail
        """
        if agent_id not in self._failover_configs:
            raise ValueError(f"Agent {agent_id} not configured for failover")
        
        config = self._failover_configs[agent_id]
        provider_chain = self._provider_chain.get(agent_id, [])
        
        if not provider_chain:
            raise ValueError(f"No providers configured for agent {agent_id}")
        
        last_error = None
        providers_tried = []
        
        # Try each provider in the chain
        for provider_id in provider_chain:
            if provider_id not in self._providers:
                continue
            
            providers_tried.append(provider_id)
            provider = self._providers[provider_id]
            
            try:
                # Execute query
                result = provider.execute_query(query, context)
                
                # Success - update active provider and health
                with self._lock:
                    self._active_providers[agent_id] = provider_id
                    health = self._provider_health.get(provider_id)
                    if health:
                        health.status = ProviderHealthStatus.HEALTHY
                        health.last_success = get_timestamp()
                        health.consecutive_failures = 0
                
                return result, provider_id
                
            except Exception as e:
                last_error = e
                
                # Update health status
                with self._lock:
                    health = self._provider_health.get(provider_id)
                    if health:
                        health.status = ProviderHealthStatus.UNHEALTHY
                        health.last_failure = get_timestamp()
                        health.consecutive_failures += 1
                        health.error_message = str(e)
                
                # Continue to next provider
                continue
        
        # All providers failed
        error_msg = f"All providers failed for agent {agent_id}. Tried: {providers_tried}. Last error: {str(last_error)}"
        raise RuntimeError(error_msg)
    
    def get_active_provider(self, agent_id: str) -> Optional[str]:
        """Get currently active provider for an agent"""
        return self._active_providers.get(agent_id)
    
    def switch_provider(
        self,
        agent_id: str,
        provider_id: str
    ) -> bool:
        """
        Manually switch to a different provider.
        
        Args:
            agent_id: Agent identifier
            provider_id: Provider ID to switch to
            
        Returns:
            bool: True if switch was successful
        """
        if agent_id not in self._failover_configs:
            return False
        
        config = self._failover_configs[agent_id]
        provider_chain = self._provider_chain.get(agent_id, [])
        
        if provider_id not in provider_chain:
            return False
        
        if provider_id not in self._providers:
            return False
        
        # Check if provider is healthy
        is_healthy, _, _ = self.check_provider_health(provider_id)
        if not is_healthy:
            return False
        
        with self._lock:
            self._active_providers[agent_id] = provider_id
        
        return True
    
    def _start_health_checks(self, agent_id: str) -> None:
        """Start background health checks for an agent"""
        if agent_id in self._health_check_threads:
            return  # Already running
        
        config = self._failover_configs.get(agent_id)
        if not config or not config.health_check_enabled:
            return
        
        def health_check_loop():
            while not self._stop_health_checks:
                try:
                    # Check all providers in the chain
                    provider_chain = self._provider_chain.get(agent_id, [])
                    for provider_id in provider_chain:
                        if provider_id in self._providers:
                            self.check_provider_health(
                                provider_id,
                                timeout=config.health_check_timeout
                            )
                    
                    # Check if we need to switch providers
                    if config.auto_failover_enabled:
                        self._check_and_switch_provider(agent_id)
                    
                    # Sleep until next check
                    time.sleep(config.health_check_interval)
                    
                except Exception as e:
                    # Log error but continue
                    print(f"Health check error for {agent_id}: {e}")
                    time.sleep(config.health_check_interval)
        
        thread = threading.Thread(target=health_check_loop, daemon=True)
        thread.start()
        self._health_check_threads[agent_id] = thread
    
    def _check_and_switch_provider(self, agent_id: str) -> None:
        """Check if provider should be switched based on health"""
        config = self._failover_configs.get(agent_id)
        if not config:
            return
        
        current_provider_id = self._active_providers.get(agent_id)
        if not current_provider_id:
            return
        
        health = self._provider_health.get(current_provider_id)
        if not health:
            return
        
        # Check if current provider has too many consecutive failures
        if health.consecutive_failures >= config.max_consecutive_failures:
            # Try to switch to next healthy provider
            provider_chain = self._provider_chain.get(agent_id, [])
            current_index = provider_chain.index(current_provider_id) if current_provider_id in provider_chain else -1
            
            # Try next providers in chain
            for next_provider_id in provider_chain[current_index + 1:]:
                is_healthy, _, _ = self.check_provider_health(
                    next_provider_id,
                    timeout=config.health_check_timeout
                )
                
                if is_healthy:
                    # Switch to this provider
                    with self._lock:
                        self._active_providers[agent_id] = next_provider_id
                    return
    
    def remove_agent(self, agent_id: str) -> None:
        """Remove failover configuration for an agent"""
        with self._lock:
            self._failover_configs.pop(agent_id, None)
            self._provider_chain.pop(agent_id, None)
            self._active_providers.pop(agent_id, None)
            # Stop health check thread
            if agent_id in self._health_check_threads:
                # Thread will stop on next iteration due to stop flag
                pass
    
    def get_failover_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get failover statistics for an agent"""
        config = self._failover_configs.get(agent_id)
        if not config:
            return {}
        
        active_provider = self._active_providers.get(agent_id)
        provider_chain = self._provider_chain.get(agent_id, [])
        
        provider_health_status = {}
        for provider_id in provider_chain:
            health = self._provider_health.get(provider_id)
            if health:
                provider_health_status[provider_id] = health.to_dict()
        
        return {
            'agent_id': agent_id,
            'primary_provider': config.primary_provider_id,
            'backup_providers': config.backup_provider_ids,
            'active_provider': active_provider,
            'provider_chain': provider_chain,
            'health_check_enabled': config.health_check_enabled,
            'auto_failover_enabled': config.auto_failover_enabled,
            'provider_health': provider_health_status
        }
