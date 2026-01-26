"""
Version control system for agent configurations
Tracks configuration history and enables rollback
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from copy import deepcopy
from ..utils.helpers import get_timestamp


@dataclass
class ConfigurationVersion:
    """A versioned configuration snapshot"""
    version: int
    timestamp: str
    config: Dict[str, Any]
    description: Optional[str] = None
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'version': self.version,
            'timestamp': self.timestamp,
            'config': self.config,
            'description': self.description,
            'created_by': self.created_by,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigurationVersion':
        """Create from dictionary"""
        return cls(
            version=data['version'],
            timestamp=data['timestamp'],
            config=data['config'],
            description=data.get('description'),
            created_by=data.get('created_by'),
            tags=data.get('tags', [])
        )


class ConfigurationVersionControl:
    """
    Version control system for agent configurations.
    Tracks all configuration changes and enables rollback.
    """
    
    def __init__(self):
        """Initialize version control"""
        # agent_id -> list of ConfigurationVersion (newest first)
        self._versions: Dict[str, List[ConfigurationVersion]] = {}
        # agent_id -> current version number
        self._current_versions: Dict[str, int] = {}
    
    def create_version(
        self,
        agent_id: str,
        config: Dict[str, Any],
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> ConfigurationVersion:
        """
        Create a new version of agent configuration.
        
        Args:
            agent_id: Agent identifier
            config: Configuration dictionary
            description: Optional description of changes
            created_by: Optional user/admin who created this version
            tags: Optional tags for this version
            
        Returns:
            ConfigurationVersion: Created version
        """
        current_version = self._current_versions.get(agent_id, 0)
        new_version = current_version + 1
        
        version = ConfigurationVersion(
            version=new_version,
            timestamp=get_timestamp(),
            config=deepcopy(config),
            description=description,
            created_by=created_by,
            tags=tags or []
        )
        
        if agent_id not in self._versions:
            self._versions[agent_id] = []
        
        # Add to beginning (newest first)
        self._versions[agent_id].insert(0, version)
        self._current_versions[agent_id] = new_version
        
        return version
    
    def get_version(self, agent_id: str, version: Optional[int] = None) -> Optional[ConfigurationVersion]:
        """
        Get a specific version of configuration.
        
        Args:
            agent_id: Agent identifier
            version: Version number (None for current/latest)
            
        Returns:
            ConfigurationVersion or None if not found
        """
        if agent_id not in self._versions:
            return None
        
        versions = self._versions[agent_id]
        if not versions:
            return None
        
        if version is None:
            # Return latest
            return versions[0]
        
        # Find specific version
        for v in versions:
            if v.version == version:
                return v
        
        return None
    
    def list_versions(self, agent_id: str, limit: Optional[int] = None) -> List[ConfigurationVersion]:
        """
        List all versions for an agent.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum number of versions to return
            
        Returns:
            List of ConfigurationVersion (newest first)
        """
        if agent_id not in self._versions:
            return []
        
        versions = self._versions[agent_id]
        if limit:
            return versions[:limit]
        return versions
    
    def get_current_version(self, agent_id: str) -> Optional[int]:
        """
        Get current version number for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Current version number or None
        """
        return self._current_versions.get(agent_id)
    
    def rollback_to_version(
        self,
        agent_id: str,
        version: int,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> ConfigurationVersion:
        """
        Rollback to a specific version.
        Creates a new version with the rolled-back configuration.
        
        Args:
            agent_id: Agent identifier
            version: Version to rollback to
            description: Description for the rollback
            created_by: User/admin performing rollback
            
        Returns:
            ConfigurationVersion: New version created from rollback
            
        Raises:
            ValueError: If version not found
        """
        target_version = self.get_version(agent_id, version)
        if not target_version:
            raise ValueError(f"Version {version} not found for agent {agent_id}")
        
        # Create new version from target version's config
        rollback_description = description or f"Rollback to version {version}"
        return self.create_version(
            agent_id=agent_id,
            config=target_version.config,
            description=rollback_description,
            created_by=created_by,
            tags=['rollback', f'from_version_{version}']
        )
    
    def compare_versions(
        self,
        agent_id: str,
        version1: int,
        version2: int
    ) -> Dict[str, Any]:
        """
        Compare two versions of configuration.
        
        Args:
            agent_id: Agent identifier
            version1: First version number
            version2: Second version number
            
        Returns:
            Dict containing comparison results
        """
        v1 = self.get_version(agent_id, version1)
        v2 = self.get_version(agent_id, version2)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
        
        # Simple comparison (can be enhanced with deep diff)
        changes = []
        all_keys = set(v1.config.keys()) | set(v2.config.keys())
        
        for key in all_keys:
            val1 = v1.config.get(key)
            val2 = v2.config.get(key)
            
            if val1 != val2:
                changes.append({
                    'field': key,
                    'old_value': val1,
                    'new_value': val2
                })
        
        return {
            'version1': version1,
            'version2': version2,
            'changes': changes,
            'total_changes': len(changes)
        }
    
    def delete_agent_versions(self, agent_id: str) -> None:
        """Delete all versions for an agent"""
        self._versions.pop(agent_id, None)
        self._current_versions.pop(agent_id, None)
    
    def get_version_history_summary(self, agent_id: str) -> Dict[str, Any]:
        """
        Get summary of version history for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dict containing version history summary
        """
        versions = self.list_versions(agent_id)
        
        return {
            'agent_id': agent_id,
            'total_versions': len(versions),
            'current_version': self._current_versions.get(agent_id),
            'versions': [v.to_dict() for v in versions[:10]]  # Last 10 versions
        }

