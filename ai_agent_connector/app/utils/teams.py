"""
Team management system with isolated database connections and agents
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from ..utils.helpers import get_timestamp
import uuid


class TeamRole(Enum):
    """Team member roles"""
    VIEWER = "viewer"  # Can view queries and results
    EDITOR = "editor"  # Can execute queries and create agents
    ADMIN = "admin"  # Full team management


@dataclass
class TeamMember:
    """A team member"""
    user_id: str
    role: TeamRole
    joined_at: str = field(default_factory=get_timestamp)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'role': self.role.value,
            'joined_at': self.joined_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamMember':
        """Create from dictionary"""
        return cls(
            user_id=data['user_id'],
            role=TeamRole(data['role']),
            joined_at=data.get('joined_at', get_timestamp())
        )


@dataclass
class Team:
    """A team with isolated resources"""
    team_id: str
    name: str
    description: Optional[str] = None
    created_by: str = ""
    created_at: str = field(default_factory=get_timestamp)
    members: Dict[str, TeamMember] = field(default_factory=dict)  # user_id -> TeamMember
    agent_ids: List[str] = field(default_factory=list)  # Agents belonging to this team
    database_configs: List[Dict[str, Any]] = field(default_factory=list)  # Database connections for this team
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'team_id': self.team_id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'members': {uid: m.to_dict() for uid, m in self.members.items()},
            'agent_ids': self.agent_ids,
            'database_configs_count': len(self.database_configs),
            'tags': self.tags,
            'member_count': len(self.members)
        }
    
    def add_member(self, user_id: str, role: TeamRole) -> None:
        """Add a member to the team"""
        self.members[user_id] = TeamMember(user_id=user_id, role=role)
    
    def remove_member(self, user_id: str) -> bool:
        """Remove a member from the team"""
        if user_id in self.members:
            del self.members[user_id]
            return True
        return False
    
    def update_member_role(self, user_id: str, role: TeamRole) -> bool:
        """Update a member's role"""
        if user_id in self.members:
            self.members[user_id].role = role
            return True
        return False
    
    def has_member(self, user_id: str) -> bool:
        """Check if user is a member"""
        return user_id in self.members
    
    def get_member_role(self, user_id: str) -> Optional[TeamRole]:
        """Get member's role"""
        member = self.members.get(user_id)
        return member.role if member else None


class TeamManager:
    """
    Manages teams with isolated database connections and agents.
    """
    
    def __init__(self):
        """Initialize team manager"""
        # team_id -> Team
        self._teams: Dict[str, Team] = {}
        # user_id -> list of team_ids
        self._user_teams: Dict[str, List[str]] = {}
        # agent_id -> team_id
        self._agent_teams: Dict[str, str] = {}
    
    def create_team(
        self,
        name: str,
        created_by: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Team:
        """
        Create a new team.
        
        Args:
            name: Team name
            created_by: User ID of creator
            description: Team description
            tags: Team tags
            
        Returns:
            Team: Created team
        """
        team_id = str(uuid.uuid4())
        
        team = Team(
            team_id=team_id,
            name=name,
            description=description,
            created_by=created_by,
            tags=tags or []
        )
        
        # Add creator as admin
        team.add_member(created_by, TeamRole.ADMIN)
        
        self._teams[team_id] = team
        
        # Track user's teams
        if created_by not in self._user_teams:
            self._user_teams[created_by] = []
        self._user_teams[created_by].append(team_id)
        
        return team
    
    def get_team(self, team_id: str) -> Optional[Team]:
        """Get a team by ID"""
        return self._teams.get(team_id)
    
    def list_teams(
        self,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Team]:
        """
        List teams.
        
        Args:
            user_id: Filter by user membership
            tags: Filter by tags
            
        Returns:
            List of Team objects
        """
        teams = list(self._teams.values())
        
        if user_id:
            teams = [t for t in teams if t.has_member(user_id)]
        
        if tags:
            teams = [t for t in teams if any(tag in t.tags for tag in tags)]
        
        return teams
    
    def update_team(
        self,
        team_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Team]:
        """Update a team"""
        team = self._teams.get(team_id)
        if not team:
            return None
        
        if 'name' in updates:
            team.name = updates['name']
        if 'description' in updates:
            team.description = updates['description']
        if 'tags' in updates:
            team.tags = updates['tags']
        
        return team
    
    def delete_team(self, team_id: str) -> bool:
        """Delete a team"""
        if team_id not in self._teams:
            return False
        
        team = self._teams[team_id]
        
        # Remove from user teams tracking
        for user_id in team.members.keys():
            if user_id in self._user_teams:
                self._user_teams[user_id] = [
                    tid for tid in self._user_teams[user_id] if tid != team_id
                ]
        
        # Remove agent associations
        for agent_id in team.agent_ids:
            self._agent_teams.pop(agent_id, None)
        
        del self._teams[team_id]
        return True
    
    def add_team_member(
        self,
        team_id: str,
        user_id: str,
        role: TeamRole
    ) -> bool:
        """Add a member to a team"""
        team = self._teams.get(team_id)
        if not team:
            return False
        
        team.add_member(user_id, role)
        
        # Track user's teams
        if user_id not in self._user_teams:
            self._user_teams[user_id] = []
        if team_id not in self._user_teams[user_id]:
            self._user_teams[user_id].append(team_id)
        
        return True
    
    def remove_team_member(self, team_id: str, user_id: str) -> bool:
        """Remove a member from a team"""
        team = self._teams.get(team_id)
        if not team:
            return False
        
        success = team.remove_member(user_id)
        
        if success:
            # Update user teams tracking
            if user_id in self._user_teams:
                self._user_teams[user_id] = [
                    tid for tid in self._user_teams[user_id] if tid != team_id
                ]
        
        return success
    
    def update_member_role(
        self,
        team_id: str,
        user_id: str,
        role: TeamRole
    ) -> bool:
        """Update a member's role in a team"""
        team = self._teams.get(team_id)
        if not team:
            return False
        
        return team.update_member_role(user_id, role)
    
    def assign_agent_to_team(self, agent_id: str, team_id: str) -> bool:
        """Assign an agent to a team"""
        team = self._teams.get(team_id)
        if not team:
            return False
        
        if agent_id not in team.agent_ids:
            team.agent_ids.append(agent_id)
        
        self._agent_teams[agent_id] = team_id
        return True
    
    def get_team_for_agent(self, agent_id: str) -> Optional[str]:
        """Get team ID for an agent"""
        return self._agent_teams.get(agent_id)
    
    def add_database_config(
        self,
        team_id: str,
        database_config: Dict[str, Any]
    ) -> bool:
        """Add a database configuration to a team"""
        team = self._teams.get(team_id)
        if not team:
            return False
        
        team.database_configs.append(database_config)
        return True
    
    def get_team_database_configs(self, team_id: str) -> List[Dict[str, Any]]:
        """Get database configurations for a team"""
        team = self._teams.get(team_id)
        if not team:
            return []
        
        return team.database_configs
    
    def check_permission(
        self,
        team_id: str,
        user_id: str,
        required_role: TeamRole
    ) -> bool:
        """
        Check if user has required role in team.
        
        Args:
            team_id: Team ID
            user_id: User ID
            required_role: Required role
            
        Returns:
            bool: True if user has required or higher role
        """
        team = self._teams.get(team_id)
        if not team:
            return False
        
        member = team.members.get(user_id)
        if not member:
            return False
        
        # Role hierarchy: VIEWER < EDITOR < ADMIN
        role_hierarchy = {
            TeamRole.VIEWER: 1,
            TeamRole.EDITOR: 2,
            TeamRole.ADMIN: 3
        }
        
        user_level = role_hierarchy.get(member.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level

