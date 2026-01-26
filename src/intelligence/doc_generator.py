"""
Documentation Generator (JAG Universal)

Auto-generates API documentation from ontology.
Creates OpenAPI/Swagger specs and Markdown docs.
"""

from typing import Dict, List, Optional, Any
import json
import os
from datetime import datetime

from .tool_registry import ToolRegistry, MCPToolDefinition
from .ontology_adapter import OntologyClass, OntologyProperty


class DocumentationGenerator:
    """
    Generates API documentation from ontology.
    
    Extracts rdfs:comment as descriptions and creates
    OpenAPI/Swagger specifications.
    """
    
    def __init__(self, output_dir: str = "./docs/api"):
        """
        Initialize documentation generator.
        
        Args:
            output_dir: Directory for generated documentation
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_openapi_spec(
        self,
        tools: List[MCPToolDefinition],
        title: str = "Ontology API",
        version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """
        Generate OpenAPI 3.0 specification from tools.
        
        Args:
            tools: List of MCP tool definitions
            title: API title
            version: API version
            
        Returns:
            OpenAPI specification dictionary
        """
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "version": version,
                "description": "Auto-generated API from ontology",
                "contact": {
                    "name": "JAG Intelligence Suite"
                }
            },
            "servers": [
                {
                    "url": "https://api.example.com/v1",
                    "description": "Production server"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
        
        # Generate paths for each tool
        for tool in tools:
            path = f"/{tool.tool_name}"
            
            # Determine HTTP method based on tool type
            if tool.tool_type == "crud":
                if tool.tool_name.startswith("get_") or tool.tool_name.startswith("list_"):
                    method = "get"
                elif tool.tool_name.startswith("create_"):
                    method = "post"
                elif tool.tool_name.startswith("update_"):
                    method = "put"
                elif tool.tool_name.startswith("delete_"):
                    method = "delete"
                else:
                    method = "post"
            else:
                method = "get"
            
            # Create operation
            operation = {
                "summary": tool.description,
                "description": tool.description,
                "operationId": tool.tool_name,
                "tags": [tool.ontology_class.split('#')[-1].split('/')[-1]],
                "parameters": [],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object"
                                }
                            }
                        }
                    }
                }
            }
            
            # Add parameters
            for param in tool.required_params + tool.optional_params:
                param_spec = {
                    "name": param["name"],
                    "in": "query" if method == "get" else "body",
                    "description": param.get("description", ""),
                    "required": param not in tool.optional_params,
                    "schema": {
                        "type": param.get("type", "string")
                    }
                }
                operation["parameters"].append(param_spec)
            
            # Add to paths
            if path not in spec["paths"]:
                spec["paths"][path] = {}
            spec["paths"][path][method] = operation
        
        return spec
    
    def generate_markdown_docs(
        self,
        tools: List[MCPToolDefinition],
        classes: List[OntologyClass],
        properties: List[OntologyProperty],
        title: str = "Ontology API Documentation"
    ) -> str:
        """
        Generate Markdown documentation.
        
        Args:
            tools: List of MCP tool definitions
            classes: List of ontology classes
            properties: List of ontology properties
            title: Documentation title
            
        Returns:
            Markdown string
        """
        lines = [
            f"# {title}",
            "",
            f"*Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Overview",
            "",
            f"This API provides access to {len(classes)} ontology classes through {len(tools)} tools.",
            "",
            "## Classes",
            ""
        ]
        
        # Document classes
        for cls in classes:
            lines.append(f"### {cls.label or cls.uri}")
            if cls.comment:
                lines.append(f"\n{cls.comment}\n")
            lines.append(f"- **URI**: `{cls.uri}`")
            if cls.parent_classes:
                lines.append(f"- **Extends**: {', '.join(cls.parent_classes)}")
            lines.append("")
        
        # Document tools
        lines.extend([
            "## Tools",
            ""
        ])
        
        # Group tools by type
        crud_tools = [t for t in tools if t.tool_type == "crud"]
        query_tools = [t for t in tools if t.tool_type == "query"]
        
        if crud_tools:
            lines.extend([
                "### CRUD Operations",
                ""
            ])
            for tool in crud_tools:
                lines.extend(self._format_tool_doc(tool))
        
        if query_tools:
            lines.extend([
                "### Query Operations",
                ""
            ])
            for tool in query_tools:
                lines.extend(self._format_tool_doc(tool))
        
        return "\n".join(lines)
    
    def _format_tool_doc(self, tool: MCPToolDefinition) -> List[str]:
        """Format tool documentation"""
        lines = [
            f"#### `{tool.tool_name}`",
            "",
            f"{tool.description}",
            "",
            "**Parameters:**",
            ""
        ]
        
        if tool.required_params:
            lines.append("*Required:*")
            for param in tool.required_params:
                lines.append(f"- `{param['name']}` ({param.get('type', 'string')}): {param.get('description', '')}")
            lines.append("")
        
        if tool.optional_params:
            lines.append("*Optional:*")
            for param in tool.optional_params:
                lines.append(f"- `{param['name']}` ({param.get('type', 'string')}): {param.get('description', '')}")
            lines.append("")
        
        if tool.return_type:
            lines.append(f"**Returns:** `{tool.return_type}`")
            lines.append("")
        
        return lines
    
    def save_openapi_spec(
        self,
        spec: Dict[str, Any],
        filename: str = "openapi.json"
    ) -> str:
        """Save OpenAPI spec to file"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2)
        return filepath
    
    def save_markdown_docs(
        self,
        markdown: str,
        filename: str = "api_documentation.md"
    ) -> str:
        """Save Markdown docs to file"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)
        return filepath


def generate_documentation(
    ontology_file: str,
    output_dir: str = "./docs/api",
    format: str = "openapi"
) -> Dict[str, str]:
    """
    Convenience function to generate documentation from ontology.
    
    Args:
        ontology_file: Path to ontology file
        output_dir: Output directory
        format: Output format ("openapi", "markdown", "both")
        
    Returns:
        Dictionary with paths to generated files
    """
    from .ontology_adapter import get_ontology_adapter
    from .tool_registry import scan_ontology
    
    # Parse ontology
    adapter = get_ontology_adapter(ontology_file)
    ontology_data = adapter.parse_ontology(ontology_file)
    classes = adapter.extract_classes(ontology_data)
    properties = adapter.extract_properties(ontology_data)
    
    # Generate tools
    tools = scan_ontology(ontology_file)
    
    # Generate documentation
    generator = DocumentationGenerator(output_dir)
    results = {}
    
    if format in ["openapi", "both"]:
        spec = generator.generate_openapi_spec(tools)
        results["openapi"] = generator.save_openapi_spec(spec)
    
    if format in ["markdown", "both"]:
        markdown = generator.generate_markdown_docs(tools, classes, properties)
        results["markdown"] = generator.save_markdown_docs(markdown)
    
    return results

