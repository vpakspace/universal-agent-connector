"""
Semantic Router for MCP Server
Uses business ontology to filter tools and reduce context bloat
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "FastMCP is required. Install it with: pip install fastmcp"
    )

# Initialize FastMCP server
# FastMCP creates an MCP server that can be used with Claude Desktop and other MCP clients
mcp = FastMCP("Semantic Router MCP Server")

# Load business ontology
ONTOLOGY_PATH = Path(__file__).parent / "business_ontology.json"
ontology: Dict[str, Dict[str, Any]] = {}

def load_ontology() -> Dict[str, Dict[str, Any]]:
    """Load business ontology from JSON file"""
    global ontology
    if ontology:
        return ontology
    
    try:
        with open(ONTOLOGY_PATH, 'r', encoding='utf-8') as f:
            ontology = json.load(f)
        return ontology
    except FileNotFoundError:
        raise FileNotFoundError(f"Ontology file not found: {ONTOLOGY_PATH}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in ontology file: {e}")


# Track tool usage for "most-used" filtering
tool_usage_count: Dict[str, int] = {}


def resolve_concept(natural_language_query: str) -> Optional[str]:
    """
    Extract business concept from natural language query using keyword matching.
    
    Args:
        natural_language_query: Natural language query string
        
    Returns:
        Concept name (Revenue, Customer, Inventory, Employee, Transaction) or None
        
    Example:
        resolve_concept("How much revenue last quarter?") -> "Revenue"
        resolve_concept("List all customers") -> "Customer"
    """
    if not natural_language_query:
        return None
    
    query_lower = natural_language_query.lower()
    
    # Keyword mappings for each concept
    # Revenue keywords
    revenue_keywords = [
        'revenue', 'sales', 'money', 'income', 'earnings', 'profit',
        'invoice', 'payment', 'billing', 'revenue', 'sales data',
        'total sales', 'monthly revenue', 'quarterly revenue'
    ]
    
    # Customer keywords
    customer_keywords = [
        'customer', 'client', 'buyer', 'user', 'account',
        'customer list', 'customer profile', 'customer segment',
        'lifetime value', 'customer satisfaction', 'client data'
    ]
    
    # Inventory keywords
    inventory_keywords = [
        'inventory', 'stock', 'product', 'warehouse', 'supply',
        'stock levels', 'low stock', 'inventory value', 'products',
        'warehouse inventory', 'stock reorder', 'availability'
    ]
    
    # Employee keywords
    employee_keywords = [
        'employee', 'staff', 'worker', 'personnel', 'hr',
        'employee list', 'department', 'payroll', 'attendance',
        'team', 'staffing', 'salary', 'employee performance'
    ]
    
    # Transaction keywords
    transaction_keywords = [
        'transaction', 'payment', 'transfer', 'purchase', 'order',
        'transaction history', 'payment log', 'financial transaction',
        'transaction summary', 'transaction report', 'payment history'
    ]
    
    # Score each concept by keyword matches
    scores = {
        'Revenue': sum(1 for keyword in revenue_keywords if keyword in query_lower),
        'Customer': sum(1 for keyword in customer_keywords if keyword in query_lower),
        'Inventory': sum(1 for keyword in inventory_keywords if keyword in query_lower),
        'Employee': sum(1 for keyword in employee_keywords if keyword in query_lower),
        'Transaction': sum(1 for keyword in transaction_keywords if keyword in query_lower),
    }
    
    # Return concept with highest score (if score > 0)
    max_score = max(scores.values())
    if max_score > 0:
        # Return first concept with max score
        for concept, score in scores.items():
            if score == max_score:
                return concept
    
    return None


def get_tools_for_concept(concept: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get tools related to a specific business concept.
    
    Args:
        concept: Business concept name (Revenue, Customer, etc.)
        limit: Maximum number of tools to return (default: 10)
        
    Returns:
        List of tool definitions in MCP format
    """
    ontology_data = load_ontology()
    
    if concept not in ontology_data:
        return []
    
    concept_data = ontology_data[concept]
    tool_names = concept_data.get('tools', [])
    
    # Limit to max 10 tools per concept
    tool_names = tool_names[:limit]
    
    # Generate tool definitions
    tools = []
    for tool_name in tool_names:
        # Track usage
        tool_usage_count[tool_name] = tool_usage_count.get(tool_name, 0)
        
        # Create tool definition in MCP format
        tool_def = {
            "name": tool_name,
            "description": f"{concept_data.get('description', '')} - {tool_name}",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": f"Query related to {concept.lower()} operations"
                    }
                },
                "required": ["query"]
            }
        }
        tools.append(tool_def)
    
    return tools


def get_top_tools(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get top N most-used tools across all concepts.
    
    Args:
        limit: Maximum number of tools to return (default: 10)
        
    Returns:
        List of tool definitions
    """
    # If no usage data, return tools from first concept
    if not tool_usage_count:
        ontology_data = load_ontology()
        first_concept = list(ontology_data.keys())[0] if ontology_data else None
        if first_concept:
            return get_tools_for_concept(first_concept, limit)
        return []
    
    # Sort by usage count (descending)
    sorted_tools = sorted(tool_usage_count.items(), key=lambda x: x[1], reverse=True)
    top_tool_names = [name for name, _ in sorted_tools[:limit]]
    
    # Generate tool definitions for top tools
    tools = []
    ontology_data = load_ontology()
    
    for tool_name in top_tool_names:
        # Find which concept this tool belongs to
        concept_for_tool = None
        for concept, data in ontology_data.items():
            if tool_name in data.get('tools', []):
                concept_for_tool = concept
                break
        
        if concept_for_tool:
            concept_data = ontology_data[concept_for_tool]
            tool_def = {
                "name": tool_name,
                "description": f"{concept_data.get('description', '')} - {tool_name}",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": f"Query related to {concept_for_tool.lower()} operations"
                        }
                    },
                    "required": ["query"]
                }
            }
            tools.append(tool_def)
    
    return tools


# MCP Resource: ontology://{concept}
# This resource exposes tools filtered by business concept
@mcp.resource("ontology://{concept}")
def ontology_resource(concept: str) -> Dict[str, Any]:
    """
    MCP Resource handler for semantic ontology filtering.
    
    This resource is called when a client requests: ontology://Revenue, ontology://Customer, etc.
    It returns schema information and available tools for that concept.
    
    Args:
        concept: Business concept name from the URI (e.g., "Revenue" from "ontology://Revenue")
        
    Returns:
        Resource content with tools and schema information
    """
    ontology_data = load_ontology()
    
    # Validate concept exists
    if concept not in ontology_data:
        return {
            "error": f"Unknown concept: {concept}",
            "available_concepts": list(ontology_data.keys())
        }
    
    concept_data = ontology_data[concept]
    tools = get_tools_for_concept(concept, limit=10)
    
    # Build resource content
    content = {
        "concept": concept,
        "description": concept_data.get("description", ""),
        "tables": concept_data.get("tables", []),
        "tools": [tool["name"] for tool in tools],
        "tool_count": len(tools),
        "sample_queries": concept_data.get("sample_queries", []),
        "schema": {
            "concept": concept,
            "tables": concept_data.get("tables", []),
            "available_tools": tools
        }
    }
    
    # Return as JSON string (MCP resources return text content)
    return {
        "uri": f"ontology://{concept}",
        "name": f"{concept} Ontology",
        "description": concept_data.get("description", ""),
        "mimeType": "application/json",
        "text": json.dumps(content, indent=2)
    }


# Override tools/list to be concept-aware
@mcp.tool()
def tools_list(current_concept: Optional[str] = None) -> Dict[str, Any]:
    """
    List available tools, optionally filtered by business concept.
    
    MCP-specific: This decorator registers this as a tool that can be called by MCP clients.
    The tool name becomes "tools_list" in the MCP protocol.
    
    Args:
        current_concept: Optional business concept to filter tools (Revenue, Customer, etc.)
        
    Returns:
        Dictionary with list of tools and metadata
    """
    start_time = time.time()
    
    try:
        if current_concept:
            # Filter by concept
            tools = get_tools_for_concept(current_concept, limit=10)
            concept_info = {
                "concept": current_concept,
                "filtered": True
            }
        else:
            # Return top 10 most-used tools
            tools = get_top_tools(limit=10)
            concept_info = {
                "concept": None,
                "filtered": False,
                "filter_type": "most_used"
            }
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            "tools": tools,
            "count": len(tools),
            "metadata": {
                **concept_info,
                "response_time_ms": round(elapsed_ms, 2),
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "tools": [],
            "count": 0
        }


# Helper tool to resolve concept from natural language
@mcp.tool()
def resolve_concept_tool(natural_language_query: str) -> Dict[str, Any]:
    """
    Resolve business concept from natural language query.
    
    This is a helper tool that clients can use to determine which concept
    a query relates to before requesting tools.
    
    Args:
        natural_language_query: Natural language query string
        
    Returns:
        Dictionary with resolved concept and ontology information
    """
    concept = resolve_concept(natural_language_query)
    ontology_data = load_ontology()
    
    if concept and concept in ontology_data:
        concept_data = ontology_data[concept]
        return {
            "concept": concept,
            "description": concept_data.get("description", ""),
            "ontology_uri": f"ontology://{concept}",
            "available_tables": concept_data.get("tables", []),
            "tool_count": len(concept_data.get("tools", [])),
            "sample_queries": concept_data.get("sample_queries", [])
        }
    else:
        return {
            "concept": None,
            "message": "No concept matched. Available concepts: " + ", ".join(ontology_data.keys()),
            "available_concepts": list(ontology_data.keys())
        }


# Tool to get ontology information
@mcp.tool()
def get_ontology_info() -> Dict[str, Any]:
    """
    Get information about the business ontology.
    
    Returns metadata about all available concepts.
    
    Returns:
        Dictionary with ontology metadata
    """
    ontology_data = load_ontology()
    
    concepts_info = {}
    for concept, data in ontology_data.items():
        concepts_info[concept] = {
            "description": data.get("description", ""),
            "table_count": len(data.get("tables", [])),
            "tool_count": len(data.get("tools", [])),
            "ontology_uri": f"ontology://{concept}"
        }
    
    return {
        "concepts": concepts_info,
        "total_concepts": len(concepts_info),
        "concept_names": list(concepts_info.keys())
    }


# Track tool usage when tools are called
def track_tool_usage(tool_name: str):
    """Track that a tool was used (called by tool handlers)"""
    tool_usage_count[tool_name] = tool_usage_count.get(tool_name, 0) + 1


# Example tool implementations (these would be replaced with actual implementations)
@mcp.tool()
def query_sales(query: str) -> Dict[str, Any]:
    """Query sales data - Example Revenue tool"""
    track_tool_usage("query_sales")
    return {
        "result": f"Sales query executed: {query}",
        "status": "success"
    }


@mcp.tool()
def get_customer_list(query: str) -> Dict[str, Any]:
    """Get customer list - Example Customer tool"""
    track_tool_usage("get_customer_list")
    return {
        "result": f"Customer list query executed: {query}",
        "status": "success"
    }


# MCP Server Entry Point
# FastMCP automatically handles MCP protocol communication
# When run as a script, it starts the MCP server
if __name__ == "__main__":
    # FastMCP handles the MCP server lifecycle
    # This will run the server using stdio transport (standard for MCP)
    mcp.run()

