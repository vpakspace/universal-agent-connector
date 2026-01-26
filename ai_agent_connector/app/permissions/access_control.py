"""
Access control and permission management
"""

from typing import Dict, List, Optional
from enum import Enum


class Permission(Enum):
    """Permission types"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class AccessControl:
    """Manages access control and permissions"""
    
    def __init__(self):
        """Initialize access control"""
        self.permissions: Dict[str, List[Permission]] = {}  # agent_id -> permissions
        # agent_id -> resource_id -> {type: str, permissions: List[Permission]}
        self.resource_permissions: Dict[str, Dict[str, Dict[str, List[Permission]]]] = {}
    
    def grant_permission(self, agent_id: str, permission: Permission):
        """
        Grant a permission to an agent
        
        Args:
            agent_id: Agent identifier
            permission: Permission to grant
        """
        if agent_id not in self.permissions:
            self.permissions[agent_id] = []
        
        if permission not in self.permissions[agent_id]:
            self.permissions[agent_id].append(permission)
    
    def revoke_permission(self, agent_id: str, permission: Permission):
        """
        Revoke a permission from an agent
        
        Args:
            agent_id: Agent identifier
            permission: Permission to revoke
        """
        if agent_id in self.permissions:
            if permission in self.permissions[agent_id]:
                self.permissions[agent_id].remove(permission)
    
    def has_permission(self, agent_id: str, permission: Permission) -> bool:
        """
        Check if an agent has a specific permission
        
        Args:
            agent_id: Agent identifier
            permission: Permission to check
            
        Returns:
            bool: True if agent has permission, False otherwise
        """
        if permission == Permission.ADMIN:
            return Permission.ADMIN in self.permissions.get(agent_id, [])
        
        return permission in self.permissions.get(agent_id, [])
    
    def get_permissions(self, agent_id: str) -> List[Permission]:
        """
        Get all permissions for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List[Permission]: List of permissions
        """
        return self.permissions.get(agent_id, [])
    
    def set_resource_permissions(
        self,
        agent_id: str,
        resource_id: str,
        permissions: List[Permission],
        resource_type: str = "table"
    ) -> None:
        """
        Replace the permissions list for a resource.
        """
        if agent_id not in self.resource_permissions:
            self.resource_permissions[agent_id] = {}
        
        unique_permissions = []
        for perm in permissions:
            if perm not in unique_permissions:
                unique_permissions.append(perm)
        
        self.resource_permissions[agent_id][resource_id] = {
            'type': resource_type,
            'permissions': unique_permissions
        }
    
    def get_resource_permissions(self, agent_id: str) -> Dict[str, Dict[str, List[Permission]]]:
        """
        Get all resource-level permissions for an agent.
        """
        return self.resource_permissions.get(agent_id, {})
    
    def has_resource_permission(
        self,
        agent_id: str,
        resource_id: str,
        permission: Permission
    ) -> bool:
        """
        Check if the agent has a permission on a specific resource.
        """
        agent_resources = self.resource_permissions.get(agent_id, {})
        resource_entry = agent_resources.get(resource_id)
        if not resource_entry:
            return False
        return permission in resource_entry.get('permissions', [])
    
    def revoke_resource(self, agent_id: str, resource_id: str) -> bool:
        """
        Remove all permissions associated with a resource.
        """
        agent_resources = self.resource_permissions.get(agent_id)
        if not agent_resources or resource_id not in agent_resources:
            return False
        
        del agent_resources[resource_id]
        if not agent_resources:
            self.resource_permissions.pop(agent_id, None)
        return True
    
    def revoke_all_agent_permissions(self, agent_id: str) -> bool:
        """
        Revoke all permissions for an agent (both general and resource-level).
        This is used when an agent is completely revoked.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            bool: True if any permissions were removed, False if agent had no permissions
        """
        had_permissions = False
        
        # Remove general permissions
        if agent_id in self.permissions:
            self.permissions.pop(agent_id)
            had_permissions = True
        
        # Remove all resource-level permissions
        if agent_id in self.resource_permissions:
            self.resource_permissions.pop(agent_id)
            had_permissions = True
        
        return had_permissions


