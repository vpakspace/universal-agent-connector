"""
Automatic database failover system
Fails over to backup database if primary is unavailable
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from ..utils.helpers import get_timestamp
from ..db import DatabaseConnector
import time


class FailoverStatus(Enum):
    """Failover status"""
    PRIMARY = "primary"  # Using primary database
    FAILOVER = "failover"  # Using backup database
    FAILED = "failed"  # All databases failed


@dataclass
class DatabaseEndpoint:
    """A database endpoint (primary or backup)"""
    endpoint_id: str
    name: str
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    connection_string: Optional[str] = None
    database_type: Optional[str] = None
    is_primary: bool = False
    is_active: bool = True
    last_failure: Optional[str] = None
    failure_count: int = 0
    priority: int = 0  # Lower number = higher priority
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'endpoint_id': self.endpoint_id,
            'name': self.name,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'database_type': self.database_type,
            'is_primary': self.is_primary,
            'is_active': self.is_active,
            'last_failure': self.last_failure,
            'failure_count': self.failure_count,
            'priority': self.priority
        }


class DatabaseFailoverManager:
    """
    Manages automatic failover to backup databases.
    """
    
    def __init__(self, health_check_interval_seconds: int = 60):
        """
        Initialize failover manager.
        
        Args:
            health_check_interval_seconds: Interval for health checks
        """
        # agent_id -> list of DatabaseEndpoint
        self._endpoints: Dict[str, List[DatabaseEndpoint]] = {}
        # agent_id -> current endpoint_id
        self._current_endpoints: Dict[str, str] = {}
        # agent_id -> failover status
        self._failover_status: Dict[str, FailoverStatus] = {}
        self.health_check_interval = health_check_interval_seconds
    
    def register_endpoints(
        self,
        agent_id: str,
        endpoints: List[DatabaseEndpoint]
    ) -> None:
        """
        Register database endpoints for an agent.
        
        Args:
            agent_id: Agent ID
            endpoints: List of database endpoints (primary first, then backups)
        """
        # Sort by priority and is_primary
        sorted_endpoints = sorted(
            endpoints,
            key=lambda e: (e.is_primary, e.priority),
            reverse=True
        )
        
        self._endpoints[agent_id] = sorted_endpoints
        
        # Set primary as current
        primary = next((e for e in sorted_endpoints if e.is_primary), sorted_endpoints[0] if sorted_endpoints else None)
        if primary:
            self._current_endpoints[agent_id] = primary.endpoint_id
            self._failover_status[agent_id] = FailoverStatus.PRIMARY
    
    def get_current_endpoint(self, agent_id: str) -> Optional[DatabaseEndpoint]:
        """Get current active endpoint for an agent"""
        if agent_id not in self._endpoints:
            return None
        
        current_id = self._current_endpoints.get(agent_id)
        if not current_id:
            return None
        
        endpoints = self._endpoints[agent_id]
        return next((e for e in endpoints if e.endpoint_id == current_id), None)
    
    def get_database_connector(self, agent_id: str) -> Optional[DatabaseConnector]:
        """
        Get database connector for current endpoint.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            DatabaseConnector or None if no endpoints available
        """
        endpoint = self.get_current_endpoint(agent_id)
        if not endpoint or not endpoint.is_active:
            return None
        
        # Build connector config
        config = {}
        if endpoint.connection_string:
            config['connection_string'] = endpoint.connection_string
        else:
            config['host'] = endpoint.host
            config['port'] = endpoint.port
            config['user'] = endpoint.user
            config['password'] = endpoint.password
            config['database'] = endpoint.database
        
        if endpoint.database_type:
            config['database_type'] = endpoint.database_type
        
        return DatabaseConnector(**config)
    
    def record_failure(self, agent_id: str, endpoint_id: Optional[str] = None) -> bool:
        """
        Record a failure for an endpoint and attempt failover.
        
        Args:
            agent_id: Agent ID
            endpoint_id: Optional specific endpoint ID (uses current if not provided)
            
        Returns:
            bool: True if failover occurred, False otherwise
        """
        if agent_id not in self._endpoints:
            return False
        
        endpoints = self._endpoints[agent_id]
        
        # Find the failed endpoint
        if endpoint_id:
            failed_endpoint = next((e for e in endpoints if e.endpoint_id == endpoint_id), None)
        else:
            failed_endpoint = self.get_current_endpoint(agent_id)
        
        if not failed_endpoint:
            return False
        
        # Record failure
        failed_endpoint.failure_count += 1
        failed_endpoint.last_failure = get_timestamp()
        failed_endpoint.is_active = False
        
        # Try to failover to next available endpoint
        return self._attempt_failover(agent_id, failed_endpoint)
    
    def _attempt_failover(self, agent_id: str, failed_endpoint: DatabaseEndpoint) -> bool:
        """Attempt to failover to next available endpoint"""
        endpoints = self._endpoints[agent_id]
        
        # Find next available endpoint (higher priority or next in list)
        current_priority = failed_endpoint.priority
        current_is_primary = failed_endpoint.is_primary
        
        # Try to find backup endpoint
        backup = None
        for endpoint in endpoints:
            if endpoint.endpoint_id == failed_endpoint.endpoint_id:
                continue
            
            if endpoint.is_active:
                # Prefer endpoints with higher priority (lower number) or non-primary backups
                if not backup:
                    backup = endpoint
                elif endpoint.priority < backup.priority:
                    backup = endpoint
                elif not endpoint.is_primary and backup.is_primary:
                    backup = endpoint
        
        if backup:
            # Test backup connection
            connector = self._create_connector_for_endpoint(backup)
            if connector:
                try:
                    connector.connect()
                    connector.disconnect()
                    
                    # Failover successful
                    self._current_endpoints[agent_id] = backup.endpoint_id
                    if backup.is_primary:
                        self._failover_status[agent_id] = FailoverStatus.PRIMARY
                    else:
                        self._failover_status[agent_id] = FailoverStatus.FAILOVER
                    
                    return True
                except Exception:
                    # Backup also failed, mark as inactive
                    backup.is_active = False
                    backup.failure_count += 1
                    backup.last_failure = get_timestamp()
        
        # No available backup
        self._failover_status[agent_id] = FailoverStatus.FAILED
        return False
    
    def _create_connector_for_endpoint(self, endpoint: DatabaseEndpoint) -> Optional[DatabaseConnector]:
        """Create a database connector for an endpoint"""
        config = {}
        if endpoint.connection_string:
            config['connection_string'] = endpoint.connection_string
        else:
            config['host'] = endpoint.host
            config['port'] = endpoint.port
            config['user'] = endpoint.user
            config['password'] = endpoint.password
            config['database'] = endpoint.database
        
        if endpoint.database_type:
            config['database_type'] = endpoint.database_type
        
        return DatabaseConnector(**config)
    
    def test_endpoint(self, endpoint: DatabaseEndpoint) -> bool:
        """
        Test if an endpoint is available.
        
        Args:
            endpoint: Database endpoint to test
            
        Returns:
            bool: True if endpoint is available
        """
        connector = self._create_connector_for_endpoint(endpoint)
        if not connector:
            return False
        
        try:
            connector.connect()
            connector.disconnect()
            endpoint.is_active = True
            return True
        except Exception:
            endpoint.is_active = False
            endpoint.failure_count += 1
            endpoint.last_failure = get_timestamp()
            return False
    
    def get_failover_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get failover status for an agent"""
        if agent_id not in self._endpoints:
            return None
        
        status = self._failover_status.get(agent_id, FailoverStatus.PRIMARY)
        current_endpoint = self.get_current_endpoint(agent_id)
        endpoints = self._endpoints[agent_id]
        
        return {
            'agent_id': agent_id,
            'status': status.value,
            'current_endpoint': current_endpoint.to_dict() if current_endpoint else None,
            'endpoints': [e.to_dict() for e in endpoints],
            'available_endpoints': len([e for e in endpoints if e.is_active]),
            'total_endpoints': len(endpoints)
        }
    
    def reset_endpoint(self, agent_id: str, endpoint_id: str) -> bool:
        """
        Reset an endpoint (mark as active again, useful after fixing issues).
        
        Args:
            agent_id: Agent ID
            endpoint_id: Endpoint ID to reset
            
        Returns:
            bool: True if reset successful
        """
        if agent_id not in self._endpoints:
            return False
        
        endpoint = next(
            (e for e in self._endpoints[agent_id] if e.endpoint_id == endpoint_id),
            None
        )
        
        if not endpoint:
            return False
        
        # Test endpoint
        if self.test_endpoint(endpoint):
            endpoint.is_active = True
            endpoint.failure_count = 0
            endpoint.last_failure = None
            
            # If this is primary and we're in failover, switch back
            if endpoint.is_primary and self._failover_status.get(agent_id) == FailoverStatus.FAILOVER:
                self._current_endpoints[agent_id] = endpoint_id
                self._failover_status[agent_id] = FailoverStatus.PRIMARY
                return True
            
            return True
        
        return False

