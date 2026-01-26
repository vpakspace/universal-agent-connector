"""
Contextual help tooltips for database schemas
Provides explanations and help for database schemas, tables, and columns
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json


@dataclass
class SchemaHelp:
    """Schema help information"""
    resource_type: str  # 'database', 'table', 'column'
    resource_name: str
    description: str
    examples: List[str] = None
    related_resources: List[str] = None
    data_type: Optional[str] = None
    constraints: List[str] = None
    usage_tips: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'resource_type': self.resource_type,
            'resource_name': self.resource_name,
            'description': self.description,
            'examples': self.examples or [],
            'related_resources': self.related_resources or [],
            'data_type': self.data_type,
            'constraints': self.constraints or [],
            'usage_tips': self.usage_tips or []
        }


class SchemaHelpProvider:
    """
    Provides contextual help for database schemas.
    """
    
    def __init__(self):
        """Initialize schema help provider"""
        # resource_key -> SchemaHelp
        self._help_cache: Dict[str, SchemaHelp] = {}
    
    def get_table_help(
        self,
        table_name: str,
        schema_info: Optional[Dict[str, Any]] = None
    ) -> SchemaHelp:
        """
        Get help information for a table.
        
        Args:
            table_name: Table name
            schema_info: Optional schema information
            
        Returns:
            SchemaHelp object
        """
        cache_key = f"table:{table_name}"
        
        if cache_key in self._help_cache:
            return self._help_cache[cache_key]
        
        # Generate help from schema info if available
        description = f"Table '{table_name}'"
        examples = []
        related_resources = []
        usage_tips = []
        
        if schema_info:
            table_info = schema_info.get('tables', {}).get(table_name, {})
            
            if table_info:
                description = table_info.get('description', description)
                columns = table_info.get('columns', [])
                
                # Generate examples
                if columns:
                    col_names = [col.get('name', '') for col in columns[:3]]
                    examples.append(f"SELECT * FROM {table_name} LIMIT 10")
                    examples.append(f"SELECT {', '.join(col_names)} FROM {table_name}")
                
                # Related resources (columns)
                related_resources = [col.get('name', '') for col in columns[:5]]
                
                # Usage tips
                usage_tips.append(f"Use WHERE clauses to filter {table_name} data")
                if columns:
                    usage_tips.append(f"Available columns: {', '.join([col.get('name', '') for col in columns[:5]])}")
        
        help_info = SchemaHelp(
            resource_type='table',
            resource_name=table_name,
            description=description,
            examples=examples,
            related_resources=related_resources,
            usage_tips=usage_tips
        )
        
        self._help_cache[cache_key] = help_info
        return help_info
    
    def get_column_help(
        self,
        table_name: str,
        column_name: str,
        schema_info: Optional[Dict[str, Any]] = None
    ) -> SchemaHelp:
        """
        Get help information for a column.
        
        Args:
            table_name: Table name
            column_name: Column name
            schema_info: Optional schema information
            
        Returns:
            SchemaHelp object
        """
        cache_key = f"column:{table_name}.{column_name}"
        
        if cache_key in self._help_cache:
            return self._help_cache[cache_key]
        
        # Generate help from schema info if available
        description = f"Column '{column_name}' in table '{table_name}'"
        data_type = None
        constraints = []
        examples = []
        usage_tips = []
        
        if schema_info:
            table_info = schema_info.get('tables', {}).get(table_name, {})
            columns = table_info.get('columns', [])
            
            for col in columns:
                if col.get('name') == column_name:
                    data_type = col.get('type')
                    description = col.get('description', description)
                    
                    # Extract constraints
                    if col.get('nullable') is False:
                        constraints.append('NOT NULL')
                    if col.get('primary_key'):
                        constraints.append('PRIMARY KEY')
                    if col.get('unique'):
                        constraints.append('UNIQUE')
                    if col.get('foreign_key'):
                        constraints.append(f"FOREIGN KEY -> {col.get('foreign_key')}")
                    
                    # Generate examples
                    examples.append(f"SELECT {column_name} FROM {table_name}")
                    examples.append(f"SELECT * FROM {table_name} WHERE {column_name} = 'value'")
                    
                    # Usage tips
                    if data_type:
                        usage_tips.append(f"Data type: {data_type}")
                    if constraints:
                        usage_tips.append(f"Constraints: {', '.join(constraints)}")
                    
                    break
        
        help_info = SchemaHelp(
            resource_type='column',
            resource_name=f"{table_name}.{column_name}",
            description=description,
            examples=examples,
            data_type=data_type,
            constraints=constraints,
            usage_tips=usage_tips
        )
        
        self._help_cache[cache_key] = help_info
        return help_info
    
    def get_database_help(
        self,
        database_name: str,
        schema_info: Optional[Dict[str, Any]] = None
    ) -> SchemaHelp:
        """
        Get help information for a database.
        
        Args:
            database_name: Database name
            schema_info: Optional schema information
            
        Returns:
            SchemaHelp object
        """
        cache_key = f"database:{database_name}"
        
        if cache_key in self._help_cache:
            return self._help_cache[cache_key]
        
        description = f"Database '{database_name}'"
        examples = []
        related_resources = []
        usage_tips = []
        
        if schema_info:
            tables = schema_info.get('tables', {})
            table_names = list(tables.keys())[:10]
            
            description = f"Database '{database_name}' with {len(tables)} tables"
            related_resources = table_names
            
            examples.append(f"List all tables: SELECT table_name FROM information_schema.tables")
            if table_names:
                examples.append(f"Query example: SELECT * FROM {table_names[0]} LIMIT 10")
            
            usage_tips.append(f"Available tables: {', '.join(table_names[:5])}")
            if len(table_names) > 5:
                usage_tips.append(f"... and {len(table_names) - 5} more tables")
        
        help_info = SchemaHelp(
            resource_type='database',
            resource_name=database_name,
            description=description,
            examples=examples,
            related_resources=related_resources,
            usage_tips=usage_tips
        )
        
        self._help_cache[cache_key] = help_info
        return help_info
    
    def clear_cache(self):
        """Clear help cache"""
        self._help_cache.clear()

