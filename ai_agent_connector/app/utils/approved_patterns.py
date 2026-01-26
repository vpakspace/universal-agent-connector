"""
Approved SQL query patterns system
Pre-defines vetted SQL patterns for common queries
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
from ..utils.helpers import get_timestamp


class PatternType(Enum):
    """Types of approved patterns"""
    TEMPLATE = "template"  # SQL template with parameters
    FUNCTION = "function"  # Python function that generates SQL
    STATIC = "static"  # Static SQL query


@dataclass
class ApprovedPattern:
    """An approved SQL query pattern"""
    pattern_id: str
    name: str
    description: str
    pattern_type: PatternType
    sql_template: Optional[str] = None  # For TEMPLATE type
    function_name: Optional[str] = None  # For FUNCTION type
    static_sql: Optional[str] = None  # For STATIC type
    parameters: List[str] = field(default_factory=list)  # Required parameters
    natural_language_keywords: List[str] = field(default_factory=list)  # Keywords that match this pattern
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    use_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'pattern_id': self.pattern_id,
            'name': self.name,
            'description': self.description,
            'pattern_type': self.pattern_type.value,
            'sql_template': self.sql_template,
            'function_name': self.function_name,
            'static_sql': self.static_sql,
            'parameters': self.parameters,
            'natural_language_keywords': self.natural_language_keywords,
            'tags': self.tags,
            'enabled': self.enabled,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'use_count': self.use_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApprovedPattern':
        """Create from dictionary"""
        return cls(
            pattern_id=data['pattern_id'],
            name=data['name'],
            description=data['description'],
            pattern_type=PatternType(data.get('pattern_type', 'template')),
            sql_template=data.get('sql_template'),
            function_name=data.get('function_name'),
            static_sql=data.get('static_sql'),
            parameters=data.get('parameters', []),
            natural_language_keywords=data.get('natural_language_keywords', []),
            tags=data.get('tags', []),
            enabled=data.get('enabled', True),
            created_by=data.get('created_by'),
            created_at=data.get('created_at'),
            use_count=data.get('use_count', 0)
        )
    
    def matches(self, natural_language_query: str) -> bool:
        """
        Check if natural language query matches this pattern.
        
        Args:
            natural_language_query: Natural language query
            
        Returns:
            bool: True if query matches pattern keywords
        """
        if not self.enabled:
            return False
        
        query_lower = natural_language_query.lower()
        
        # Check if any keywords match
        for keyword in self.natural_language_keywords:
            if keyword.lower() in query_lower:
                return True
        
        return False
    
    def generate_sql(self, parameters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Generate SQL from this pattern.
        
        Args:
            parameters: Parameter values
            
        Returns:
            SQL query string or None if generation fails
        """
        if self.pattern_type == PatternType.STATIC:
            return self.static_sql
        
        elif self.pattern_type == PatternType.TEMPLATE:
            if not self.sql_template:
                return None
            
            sql = self.sql_template
            if parameters:
                for param_name in self.parameters:
                    placeholder = f"{{{{{param_name}}}}}"
                    value = parameters.get(param_name, '')
                    # Escape SQL injection (basic protection)
                    if isinstance(value, str):
                        value = value.replace("'", "''")
                    sql = sql.replace(placeholder, str(value))
            
            return sql
        
        elif self.pattern_type == PatternType.FUNCTION:
            # Function-based patterns would call registered functions
            # For now, return None (would need function registry)
            return None
        
        return None


class ApprovedPatternManager:
    """
    Manages approved SQL query patterns.
    Matches natural language queries to vetted SQL patterns.
    """
    
    def __init__(self):
        """Initialize pattern manager"""
        # pattern_id -> ApprovedPattern
        self._patterns: Dict[str, ApprovedPattern] = {}
        # Function registry for FUNCTION type patterns
        self._functions: Dict[str, Callable] = {}
    
    def register_pattern(self, pattern: ApprovedPattern) -> None:
        """
        Register an approved pattern.
        
        Args:
            pattern: ApprovedPattern to register
        """
        self._patterns[pattern.pattern_id] = pattern
    
    def create_pattern(
        self,
        name: str,
        description: str,
        sql_template: Optional[str] = None,
        static_sql: Optional[str] = None,
        natural_language_keywords: Optional[List[str]] = None,
        parameters: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> ApprovedPattern:
        """
        Create a new approved pattern.
        
        Args:
            name: Pattern name
            description: Pattern description
            sql_template: SQL template with {param} placeholders
            static_sql: Static SQL query
            natural_language_keywords: Keywords that match this pattern
            parameters: Required parameters
            tags: Tags for categorization
            created_by: Creator ID
            
        Returns:
            ApprovedPattern: Created pattern
        """
        import uuid
        
        # Determine pattern type
        if static_sql:
            pattern_type = PatternType.STATIC
        elif sql_template:
            pattern_type = PatternType.TEMPLATE
            # Extract parameters from template if not provided
            if parameters is None:
                import re
                param_pattern = r'\{\{(\w+)\}\}'
                parameters = list(set(re.findall(param_pattern, sql_template)))
        else:
            raise ValueError("Either sql_template or static_sql must be provided")
        
        pattern = ApprovedPattern(
            pattern_id=str(uuid.uuid4()),
            name=name,
            description=description,
            pattern_type=pattern_type,
            sql_template=sql_template,
            static_sql=static_sql,
            parameters=parameters or [],
            natural_language_keywords=natural_language_keywords or [],
            tags=tags or [],
            created_by=created_by,
            created_at=get_timestamp()
        )
        
        self._patterns[pattern.pattern_id] = pattern
        
        return pattern
    
    def find_matching_pattern(
        self,
        natural_language_query: str,
        tags: Optional[List[str]] = None
    ) -> Optional[ApprovedPattern]:
        """
        Find an approved pattern that matches a natural language query.
        
        Args:
            natural_language_query: Natural language query
            tags: Optional tags to filter by
            
        Returns:
            ApprovedPattern if found, None otherwise
        """
        candidates = []
        
        for pattern in self._patterns.values():
            if not pattern.enabled:
                continue
            
            # Filter by tags if provided
            if tags and not any(tag in pattern.tags for tag in tags):
                continue
            
            # Check if query matches
            if pattern.matches(natural_language_query):
                candidates.append(pattern)
        
        if not candidates:
            return None
        
        # Return first match (could be enhanced with scoring)
        # Update use count
        candidates[0].use_count += 1
        return candidates[0]
    
    def get_pattern(self, pattern_id: str) -> Optional[ApprovedPattern]:
        """Get a pattern by ID"""
        return self._patterns.get(pattern_id)
    
    def list_patterns(
        self,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True
    ) -> List[ApprovedPattern]:
        """
        List all approved patterns.
        
        Args:
            tags: Filter by tags
            enabled_only: Only return enabled patterns
            
        Returns:
            List of ApprovedPattern objects
        """
        patterns = list(self._patterns.values())
        
        if enabled_only:
            patterns = [p for p in patterns if p.enabled]
        
        if tags:
            patterns = [p for p in patterns if any(tag in p.tags for tag in tags)]
        
        # Sort by use_count
        patterns.sort(key=lambda x: x.use_count, reverse=True)
        
        return patterns
    
    def update_pattern(
        self,
        pattern_id: str,
        updates: Dict[str, Any]
    ) -> Optional[ApprovedPattern]:
        """Update a pattern"""
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return None
        
        if 'name' in updates:
            pattern.name = updates['name']
        if 'description' in updates:
            pattern.description = updates['description']
        if 'enabled' in updates:
            pattern.enabled = updates['enabled']
        if 'tags' in updates:
            pattern.tags = updates['tags']
        if 'natural_language_keywords' in updates:
            pattern.natural_language_keywords = updates['natural_language_keywords']
        
        return pattern
    
    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern"""
        if pattern_id in self._patterns:
            del self._patterns[pattern_id]
            return True
        return False

