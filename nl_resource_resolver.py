"""
Natural Language to MCP Resource URI Resolver
Maps natural language queries to MCP resource URIs and tools using concept extraction
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "FastMCP is required. Install it with: pip install fastmcp"
    )

from concept_extractor import extract_concepts, extract_primary_concept

# Initialize FastMCP server
mcp = FastMCP("NL Resource Resolver MCP Server")

# Load resource mapper
RESOURCE_MAPPER_PATH = Path(__file__).parent / "resource_mapper.json"
_resource_mapper: Dict[str, Dict[str, Any]] = {}


def load_resource_mapper() -> Dict[str, Dict[str, Any]]:
    """
    Load resource mapper from JSON file
    
    Returns:
        Dictionary mapping concepts to resources and tools
    """
    global _resource_mapper
    
    if _resource_mapper:
        return _resource_mapper
    
    try:
        with open(RESOURCE_MAPPER_PATH, 'r', encoding='utf-8') as f:
            _resource_mapper = json.load(f)
        return _resource_mapper
    except FileNotFoundError:
        raise FileNotFoundError(f"Resource mapper file not found: {RESOURCE_MAPPER_PATH}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in resource mapper: {e}")


@dataclass
class ResolutionResult:
    """Result of natural language query resolution"""
    matched_concepts: List[str] = field(default_factory=list)
    resource_uris: List[str] = field(default_factory=list)
    suggested_tools: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    explanation: str = ""
    requires_permissions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "matched_concepts": self.matched_concepts,
            "resource_uris": self.resource_uris,
            "suggested_tools": self.suggested_tools,
            "confidence_score": round(self.confidence_score, 2),
            "explanation": self.explanation,
            "requires_permissions": self.requires_permissions
        }


def resolve_template(template: str, tenant_id: str) -> str:
    """
    Resolve URI template by replacing {{tenant}} placeholder with actual tenant_id
    
    Args:
        template: URI template with {{tenant}} placeholder
        tenant_id: Actual tenant identifier
        
    Returns:
        Resolved URI string
        
    Example:
        resolve_template("mcp://{{tenant}}/postgres/customers", "tenant_001")
        # Returns: "mcp://tenant_001/postgres/customers"
    """
    return template.replace("{{tenant}}", tenant_id)


def rank_tools(
    concepts: List[str],
    available_tools: List[str],
    concept_to_tools: Dict[str, List[str]],
    max_tools: int = 5
) -> List[str]:
    """
    Rank and return top most relevant tools based on matched concepts
    
    Args:
        concepts: List of matched concept names
        available_tools: List of all available tools (for filtering)
        concept_to_tools: Dictionary mapping concepts to their tools
        max_tools: Maximum number of tools to return (default: 5)
        
    Returns:
        List of ranked tool names
    """
    if not concepts:
        # Return generic search tool if no concepts matched
        generic_tools = ["search_resources", "query_data", "list_tables"]
        return [tool for tool in generic_tools if tool in available_tools][:max_tools]
    
    # Count tool occurrences across all matched concepts
    tool_scores: Dict[str, int] = Counter()
    
    for concept in concepts:
        concept_tools = concept_to_tools.get(concept, [])
        for tool in concept_tools:
            if tool in available_tools:  # Only include available tools
                tool_scores[tool] += 1
    
    # Sort by score (descending), then alphabetically
    ranked_tools = sorted(
        tool_scores.items(),
        key=lambda x: (-x[1], x[0])  # Negative score for descending sort
    )
    
    # Return top tools
    top_tools = [tool for tool, score in ranked_tools[:max_tools]]
    
    # If we don't have enough tools, add from concepts even if not scored
    if len(top_tools) < max_tools:
        all_tools = set(top_tools)
        for concept in concepts:
            concept_tools = concept_to_tools.get(concept, [])
            for tool in concept_tools:
                if tool in available_tools and tool not in all_tools:
                    all_tools.add(tool)
                    top_tools.append(tool)
                    if len(top_tools) >= max_tools:
                        break
            if len(top_tools) >= max_tools:
                break
    
    return top_tools[:max_tools]


def calculate_overall_confidence(concept_scores: List[Tuple[str, float]]) -> float:
    """
    Calculate overall confidence score from concept scores
    
    Uses weighted average with higher weights for top concepts.
    
    Args:
        concept_scores: List of (concept, score) tuples
        
    Returns:
        Overall confidence score (0.0 to 1.0)
    """
    if not concept_scores:
        return 0.0
    
    # Use weighted average (top concepts weighted more)
    total_weight = 0.0
    weighted_sum = 0.0
    
    for i, (concept, score) in enumerate(concept_scores):
        # Weight decreases for lower-ranked concepts
        weight = 1.0 / (i + 1)
        weighted_sum += score * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return weighted_sum / total_weight


def generate_explanation(
    query: str,
    matched_concepts: List[str],
    confidence_score: float
) -> str:
    """
    Generate human-readable explanation of the resolution
    
    Args:
        query: Original query
        matched_concepts: List of matched concepts
        confidence_score: Overall confidence score
        
    Returns:
        Explanation string
    """
    if not matched_concepts:
        return "No specific business concepts detected. Using generic search tools."
    
    if len(matched_concepts) == 1:
        return f"Detected '{matched_concepts[0]}' concept with {confidence_score:.0%} confidence"
    else:
        concepts_str = "', '".join(matched_concepts)
        return f"Detected multiple concepts ('{concepts_str}') with {confidence_score:.0%} confidence"


def resolve_query(
    nl_query: str,
    tenant_id: str,
    available_tools: Optional[List[str]] = None
) -> ResolutionResult:
    """
    Resolve natural language query to MCP resource URIs and tools
    
    This is the main function that:
    1. Extracts business concepts from the query
    2. Maps concepts to resource URIs
    3. Suggests relevant tools
    4. Calculates confidence scores
    
    Args:
        nl_query: Natural language query string
        tenant_id: Tenant identifier for URI resolution
        available_tools: Optional list of available tools (for filtering)
        
    Returns:
        ResolutionResult with matched concepts, resources, tools, and confidence
        
    Example:
        result = resolve_query(
            "Show me customer purchase history for last quarter",
            "tenant_001"
        )
        # Returns ResolutionResult with Customer and Transaction concepts,
        # corresponding resource URIs, and suggested tools
    """
    if not nl_query or not nl_query.strip():
        return ResolutionResult(
            explanation="Empty query provided",
            confidence_score=0.0
        )
    
    # Load resource mapper
    resource_mapper = load_resource_mapper()
    
    # Extract concepts with confidence scores
    concept_scores = extract_concepts(nl_query, min_confidence=0.3)
    
    # Get matched concept names
    matched_concepts = [concept for concept, score in concept_scores]
    
    # Collect resources and tools from matched concepts
    all_resource_uris: List[str] = []
    all_tools: List[str] = []
    all_permissions: List[str] = []
    concept_to_tools: Dict[str, List[str]] = {}
    
    for concept in matched_concepts:
        concept_config = resource_mapper.get(concept, {})
        
        # Collect resources (resolve templates)
        resources = concept_config.get("resources", [])
        for resource_template in resources:
            resolved_uri = resolve_template(resource_template, tenant_id)
            if resolved_uri not in all_resource_uris:
                all_resource_uris.append(resolved_uri)
        
        # Collect tools
        tools = concept_config.get("tools", [])
        concept_to_tools[concept] = tools
        all_tools.extend(tools)
        
        # Collect required permissions
        permissions = concept_config.get("requires", [])
        all_permissions.extend(permissions)
    
    # Remove duplicate permissions
    unique_permissions = list(set(all_permissions))
    
    # Rank tools (filter by available_tools if provided)
    if available_tools is None:
        available_tools = list(set(all_tools))  # Use all tools if not specified
    
    suggested_tools = rank_tools(matched_concepts, available_tools, concept_to_tools)
    
    # Calculate overall confidence score
    confidence_score = calculate_overall_confidence(concept_scores)
    
    # Generate explanation
    explanation = generate_explanation(nl_query, matched_concepts, confidence_score)
    
    # Handle edge case: no concepts matched
    if not matched_concepts:
        # Return generic resources and tools
        all_resource_uris = [f"mcp://{tenant_id}/postgres/*"]  # Generic search
        suggested_tools = ["search_resources", "query_data", "list_tables"][:5]
        confidence_score = 0.1  # Low confidence for generic match
    
    return ResolutionResult(
        matched_concepts=matched_concepts,
        resource_uris=all_resource_uris,
        suggested_tools=suggested_tools,
        confidence_score=confidence_score,
        explanation=explanation,
        requires_permissions=unique_permissions
    )


@mcp.tool()
def resolve_semantic_query(
    nl_query: str,
    tenant_id: str,
    available_tools: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    FastMCP tool to resolve natural language query to MCP resources and tools
    
    This tool accepts a natural language query and returns structured resolution
    with matched concepts, resource URIs, suggested tools, and confidence scores.
    
    Args:
        nl_query: Natural language query (e.g., "Show me customer purchase history")
        tenant_id: Tenant identifier for URI resolution
        available_tools: Optional list of available tools for filtering
        
    Returns:
        Dictionary with resolution result (JSON-serializable)
        
    Example:
        {
            "matched_concepts": ["Customer", "Transaction"],
            "resource_uris": ["mcp://tenant_001/postgres/customers", ...],
            "suggested_tools": ["query_customer_orders", ...],
            "confidence_score": 0.87,
            "explanation": "Detected customer analysis with time-based filtering"
        }
    """
    result = resolve_query(nl_query, tenant_id, available_tools)
    return result.to_dict()


# MCP Server Entry Point
if __name__ == "__main__":
    mcp.run()

