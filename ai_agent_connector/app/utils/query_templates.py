"""
Query template system for saving and reusing frequently used queries
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from ..utils.helpers import get_timestamp
import uuid


@dataclass
class QueryTemplate:
    """A saved query template"""
    template_id: str
    name: str
    description: Optional[str] = None
    natural_language: Optional[str] = None  # Original NL query if applicable
    sql: str = ""
    parameters: List[str] = field(default_factory=list)  # Parameter placeholders
    tags: List[str] = field(default_factory=list)
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    last_used_at: Optional[str] = None
    use_count: int = 0
    is_public: bool = False  # Public templates available to all agents
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'natural_language': self.natural_language,
            'sql': self.sql,
            'parameters': self.parameters,
            'tags': self.tags,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'last_used_at': self.last_used_at,
            'use_count': self.use_count,
            'is_public': self.is_public
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryTemplate':
        """Create from dictionary"""
        return cls(
            template_id=data['template_id'],
            name=data['name'],
            description=data.get('description'),
            natural_language=data.get('natural_language'),
            sql=data['sql'],
            parameters=data.get('parameters', []),
            tags=data.get('tags', []),
            created_by=data.get('created_by'),
            created_at=data.get('created_at'),
            last_used_at=data.get('last_used_at'),
            use_count=data.get('use_count', 0),
            is_public=data.get('is_public', False)
        )
    
    def apply_parameters(self, params: Dict[str, Any]) -> str:
        """
        Apply parameters to template SQL.
        
        Args:
            params: Dictionary of parameter values
            
        Returns:
            SQL query with parameters applied
        """
        sql = self.sql
        for param_name in self.parameters:
            placeholder = f"{{{{{param_name}}}}}"
            value = params.get(param_name, '')
            # Escape SQL injection (basic protection)
            if isinstance(value, str):
                value = value.replace("'", "''")
            sql = sql.replace(placeholder, str(value))
        return sql


class QueryTemplateManager:
    """
    Manages query templates for saving and reusing queries.
    """
    
    def __init__(self):
        """Initialize template manager"""
        # template_id -> QueryTemplate
        self._templates: Dict[str, QueryTemplate] = {}
        # agent_id -> list of template_ids
        self._agent_templates: Dict[str, List[str]] = {}
        # Public templates (available to all)
        self._public_templates: List[str] = []
    
    def create_template(
        self,
        name: str,
        sql: str,
        natural_language: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None,
        is_public: bool = False
    ) -> QueryTemplate:
        """
        Create a new query template.
        
        Args:
            name: Template name
            sql: SQL query (can contain {param_name} placeholders)
            natural_language: Original natural language query
            description: Template description
            parameters: List of parameter names
            tags: List of tags
            created_by: Creator agent/user ID
            is_public: Whether template is public
            
        Returns:
            QueryTemplate: Created template
        """
        template_id = str(uuid.uuid4())
        
        # Extract parameters from SQL if not provided
        if parameters is None:
            import re
            param_pattern = r'\{\{(\w+)\}\}'
            parameters = list(set(re.findall(param_pattern, sql)))
        
        template = QueryTemplate(
            template_id=template_id,
            name=name,
            description=description,
            natural_language=natural_language,
            sql=sql,
            parameters=parameters or [],
            tags=tags or [],
            created_by=created_by,
            created_at=get_timestamp(),
            is_public=is_public
        )
        
        self._templates[template_id] = template
        
        if is_public:
            self._public_templates.append(template_id)
        elif created_by:
            if created_by not in self._agent_templates:
                self._agent_templates[created_by] = []
            self._agent_templates[created_by].append(template_id)
        
        return template
    
    def get_template(self, template_id: str) -> Optional[QueryTemplate]:
        """Get a template by ID"""
        return self._templates.get(template_id)
    
    def list_templates(
        self,
        agent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> List[QueryTemplate]:
        """
        List templates available to an agent.
        
        Args:
            agent_id: Agent ID (None for all public templates)
            tags: Filter by tags
            search: Search in name/description
            
        Returns:
            List of QueryTemplate objects
        """
        templates = []
        
        # Get agent-specific templates
        if agent_id and agent_id in self._agent_templates:
            for template_id in self._agent_templates[agent_id]:
                template = self._templates.get(template_id)
                if template:
                    templates.append(template)
        
        # Get public templates
        for template_id in self._public_templates:
            template = self._templates.get(template_id)
            if template:
                templates.append(template)
        
        # Apply filters
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates
                if search_lower in t.name.lower() or
                (t.description and search_lower in t.description.lower())
            ]
        
        # Sort by use_count and last_used_at
        templates.sort(key=lambda x: (x.use_count, x.last_used_at or ''), reverse=True)
        
        return templates
    
    def use_template(
        self,
        template_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Use a template and return the SQL query.
        
        Args:
            template_id: Template ID
            parameters: Parameter values
            
        Returns:
            SQL query string or None if template not found
        """
        template = self._templates.get(template_id)
        if not template:
            return None
        
        # Update usage stats
        template.use_count += 1
        template.last_used_at = get_timestamp()
        
        # Apply parameters
        if parameters:
            return template.apply_parameters(parameters)
        else:
            return template.sql
    
    def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any]
    ) -> Optional[QueryTemplate]:
        """
        Update a template.
        
        Args:
            template_id: Template ID
            updates: Dictionary of updates
            
        Returns:
            Updated QueryTemplate or None if not found
        """
        template = self._templates.get(template_id)
        if not template:
            return None
        
        # Update fields
        if 'name' in updates:
            template.name = updates['name']
        if 'description' in updates:
            template.description = updates['description']
        if 'sql' in updates:
            template.sql = updates['sql']
            # Re-extract parameters
            import re
            param_pattern = r'\{\{(\w+)\}\}'
            template.parameters = list(set(re.findall(param_pattern, template.sql)))
        if 'tags' in updates:
            template.tags = updates['tags']
        if 'is_public' in updates:
            template.is_public = updates['is_public']
            # Update public templates list
            if updates['is_public'] and template_id not in self._public_templates:
                self._public_templates.append(template_id)
            elif not updates['is_public'] and template_id in self._public_templates:
                self._public_templates.remove(template_id)
        
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: Template ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if template_id not in self._templates:
            return False
        
        template = self._templates[template_id]
        
        # Remove from agent templates
        if template.created_by and template.created_by in self._agent_templates:
            self._agent_templates[template.created_by] = [
                tid for tid in self._agent_templates[template.created_by]
                if tid != template_id
            ]
        
        # Remove from public templates
        if template_id in self._public_templates:
            self._public_templates.remove(template_id)
        
        # Delete template
        del self._templates[template_id]
        
        return True
    
    def remove_agent_templates(self, agent_id: str) -> None:
        """Remove all templates for an agent"""
        if agent_id in self._agent_templates:
            for template_id in self._agent_templates[agent_id]:
                self._templates.pop(template_id, None)
            del self._agent_templates[agent_id]

