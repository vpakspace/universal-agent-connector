"""
Dynamic MCP Tool Registry (JAG Universal)

Automatically generates MCP tool definitions from ontology classes.
Creates CRUD operations and specialized query tools based on ontology structure.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import re

from .ontology_adapter import OntologyClass, OntologyProperty


@dataclass
class MCPToolDefinition:
    """Definition of an MCP tool generated from ontology"""
    tool_name: str
    ontology_class: str  # Class URI this tool operates on
    tool_type: str  # "crud" or "query"
    description: str
    required_params: List[Dict[str, Any]] = field(default_factory=list)
    optional_params: List[Dict[str, Any]] = field(default_factory=list)
    axioms: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None


class ToolRegistry:
    """
    Registry for dynamically generated MCP tools from ontology.
    
    Scans ontology and generates tool definitions for:
    - CRUD operations (get_, create_, update_, delete_)
    - Property-based queries (find_by_age, filter_by_status)
    """
    
    def __init__(self, enable_crud: bool = True, enable_queries: bool = True):
        """
        Initialize tool registry.
        
        Args:
            enable_crud: Generate CRUD operations
            enable_queries: Generate query tools
        """
        self.enable_crud = enable_crud
        self.enable_queries = enable_queries
        self.tools: Dict[str, MCPToolDefinition] = {}
    
    def scan_ontology(
        self,
        classes: List[OntologyClass],
        properties: List[OntologyProperty],
        axioms: List[Any] = None
    ) -> List[MCPToolDefinition]:
        """
        Scan ontology and generate MCP tool definitions.
        
        Args:
            classes: List of ontology classes
            properties: List of ontology properties
            axioms: List of ontology axioms (optional)
            
        Returns:
            List of MCPToolDefinition objects
        """
        tools = []
        
        # Generate CRUD tools for each class
        if self.enable_crud:
            for cls in classes:
                tools.extend(self._generate_crud_tools(cls, properties))
        
        # Generate query tools based on properties
        if self.enable_queries:
            for prop in properties:
                tools.extend(self._generate_query_tools(prop, classes))
        
        # Store tools in registry
        for tool in tools:
            self.tools[tool.tool_name] = tool
        
        return tools
    
    def _generate_crud_tools(
        self,
        cls: OntologyClass,
        properties: List[OntologyProperty]
    ) -> List[MCPToolDefinition]:
        """Generate CRUD operations for a class"""
        tools = []
        class_name = self._sanitize_name(cls.label or cls.uri.split('#')[-1].split('/')[-1])
        
        # Get properties for this class
        class_properties = [
            p for p in properties
            if p.domain == cls.uri or cls.uri in (p.domain or '')
        ]
        
        # GET tool
        tools.append(MCPToolDefinition(
            tool_name=f"get_{class_name.lower()}",
            ontology_class=cls.uri,
            tool_type="crud",
            description=f"Retrieve {cls.label or class_name} by ID. {cls.comment or ''}",
            required_params=[
                {"name": "id", "type": "string", "description": f"{class_name} identifier"}
            ],
            return_type=cls.uri
        ))
        
        # CREATE tool
        create_params = []
        for prop in class_properties:
            param = {
                "name": self._sanitize_name(prop.label or prop.uri.split('#')[-1]),
                "type": self._map_property_type(prop.range),
                "description": prop.comment or f"{prop.label} property"
            }
            if prop.cardinality and prop.cardinality.get('min', 0) > 0:
                create_params.append(param)
            else:
                create_params.append({**param, "optional": True})
        
        tools.append(MCPToolDefinition(
            tool_name=f"create_{class_name.lower()}",
            ontology_class=cls.uri,
            tool_type="crud",
            description=f"Create a new {cls.label or class_name}. {cls.comment or ''}",
            required_params=[p for p in create_params if not p.get('optional')],
            optional_params=[p for p in create_params if p.get('optional')],
            return_type=cls.uri
        ))
        
        # UPDATE tool
        update_params = [
            {"name": "id", "type": "string", "description": f"{class_name} identifier"}
        ] + create_params
        
        tools.append(MCPToolDefinition(
            tool_name=f"update_{class_name.lower()}",
            ontology_class=cls.uri,
            tool_type="crud",
            description=f"Update an existing {cls.label or class_name}. {cls.comment or ''}",
            required_params=[p for p in update_params if not p.get('optional')],
            optional_params=[p for p in update_params if p.get('optional')],
            return_type=cls.uri
        ))
        
        # DELETE tool
        tools.append(MCPToolDefinition(
            tool_name=f"delete_{class_name.lower()}",
            ontology_class=cls.uri,
            tool_type="crud",
            description=f"Delete a {cls.label or class_name} by ID. {cls.comment or ''}",
            required_params=[
                {"name": "id", "type": "string", "description": f"{class_name} identifier"}
            ],
            return_type="boolean"
        ))
        
        # LIST tool
        tools.append(MCPToolDefinition(
            tool_name=f"list_{class_name.lower()}s",
            ontology_class=cls.uri,
            tool_type="crud",
            description=f"List all {cls.label or class_name} entities. {cls.comment or ''}",
            optional_params=[
                {"name": "limit", "type": "integer", "description": "Maximum number of results"},
                {"name": "offset", "type": "integer", "description": "Offset for pagination"}
            ],
            return_type=f"List[{cls.uri}]"
        ))
        
        return tools
    
    def _generate_query_tools(
        self,
        prop: OntologyProperty,
        classes: List[OntologyClass]
    ) -> List[MCPToolDefinition]:
        """Generate query tools based on property"""
        tools = []
        prop_name = self._sanitize_name(prop.label or prop.uri.split('#')[-1])
        
        # Find class that uses this property
        domain_class = None
        for cls in classes:
            if cls.uri == prop.domain or prop.domain in cls.uri:
                domain_class = cls
                break
        
        if not domain_class:
            return tools
        
        class_name = self._sanitize_name(domain_class.label or domain_class.uri.split('#')[-1])
        
        # Generate find_by_* tool
        tools.append(MCPToolDefinition(
            tool_name=f"find_{class_name.lower()}_by_{prop_name.lower()}",
            ontology_class=domain_class.uri,
            tool_type="query",
            description=f"Find {domain_class.label or class_name} by {prop.label or prop_name}. {prop.comment or ''}",
            required_params=[
                {
                    "name": prop_name.lower(),
                    "type": self._map_property_type(prop.range),
                    "description": prop.comment or f"{prop.label} value"
                }
            ],
            return_type=f"List[{domain_class.uri}]"
        ))
        
        # Generate filter_by_* tool (for range queries)
        if prop.range and ('int' in prop.range.lower() or 'float' in prop.range.lower() or 'date' in prop.range.lower()):
            tools.append(MCPToolDefinition(
                tool_name=f"filter_{class_name.lower()}_by_{prop_name.lower()}",
                ontology_class=domain_class.uri,
                tool_type="query",
                description=f"Filter {domain_class.label or class_name} by {prop.label or prop_name} range. {prop.comment or ''}",
                optional_params=[
                    {
                        "name": f"{prop_name.lower()}_min",
                        "type": self._map_property_type(prop.range),
                        "description": f"Minimum {prop.label} value"
                    },
                    {
                        "name": f"{prop_name.lower()}_max",
                        "type": self._map_property_type(prop.range),
                        "description": f"Maximum {prop.label} value"
                    }
                ],
                return_type=f"List[{domain_class.uri}]"
            ))
        
        return tools
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for use in tool names"""
        # Remove special characters, convert to camelCase
        name = re.sub(r'[^a-zA-Z0-9]', '_', name)
        # Convert to camelCase
        parts = name.split('_')
        return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:]) if len(parts) > 1 else parts[0].lower()
    
    def _map_property_type(self, range_uri: Optional[str]) -> str:
        """Map ontology range to Python/MCP type"""
        if not range_uri:
            return "string"
        
        range_lower = range_uri.lower()
        
        # XSD types
        if 'string' in range_lower or 'text' in range_lower:
            return "string"
        elif 'int' in range_lower or 'integer' in range_lower:
            return "integer"
        elif 'float' in range_lower or 'double' in range_lower or 'decimal' in range_lower:
            return "float"
        elif 'bool' in range_lower or 'boolean' in range_lower:
            return "boolean"
        elif 'date' in range_lower or 'datetime' in range_lower:
            return "string"  # ISO 8601 string
        else:
            return "string"  # Default
    
    def get_tool(self, tool_name: str) -> Optional[MCPToolDefinition]:
        """Get tool definition by name"""
        return self.tools.get(tool_name)
    
    def list_tools(self, tool_type: Optional[str] = None) -> List[MCPToolDefinition]:
        """List all tools, optionally filtered by type"""
        if tool_type:
            return [t for t in self.tools.values() if t.tool_type == tool_type]
        return list(self.tools.values())


def scan_ontology(
    ontology_file: str,
    enable_crud: bool = True,
    enable_queries: bool = True
) -> List[MCPToolDefinition]:
    """
    Convenience function to scan ontology and generate tools.
    
    Args:
        ontology_file: Path to ontology file
        enable_crud: Generate CRUD operations
        enable_queries: Generate query tools
        
    Returns:
        List of MCPToolDefinition objects
    """
    from .ontology_adapter import get_ontology_adapter
    
    adapter = get_ontology_adapter(ontology_file)
    ontology_data = adapter.parse_ontology(ontology_file)
    
    classes = adapter.extract_classes(ontology_data)
    properties = adapter.extract_properties(ontology_data)
    axioms = adapter.extract_axioms(ontology_data)
    
    registry = ToolRegistry(enable_crud=enable_crud, enable_queries=enable_queries)
    return registry.scan_ontology(classes, properties, axioms)

