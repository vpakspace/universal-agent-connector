"""
Self-Healing Query System using MCP Sampling
Recovers from SQL errors by asking LLM for corrections via MCP sampling
"""

import re
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "FastMCP is required. Install it with: pip install fastmcp"
    )

from ontology_matcher import (
    find_semantic_alternatives,
    save_learned_mapping,
    ColumnNotFoundError,
    TableNotFoundError,
    TypeMismatchError
)
from mock_sql_executor import MockSQLExecutor

# Initialize FastMCP server
mcp = FastMCP("Self-Healing Query Server")

# Global SQL executor instance
sql_executor = MockSQLExecutor()


def build_healing_prompt(
    failed_column: str,
    table: str,
    alternatives: List[str],
    error_message: str
) -> str:
    """
    Build a prompt for the LLM to suggest column corrections
    
    Args:
        failed_column: Column name that failed
        table: Table name
        alternatives: List of alternative column names found
        error_message: Original error message
    
    Returns:
        Prompt string for LLM
    """
    alternatives_str = ", ".join(alternatives) if alternatives else "none found"
    
    prompt = f"""A SQL query failed because column '{failed_column}' does not exist in table '{table}'.

Error: {error_message}

Available alternative column names (based on semantic similarity): {alternatives_str}

Based on the error and the available alternatives, suggest the MOST LIKELY correct column name to use instead of '{failed_column}'.

Respond with ONLY the column name (no quotes, no explanation, just the column name). If none of the alternatives seem correct, respond with "NONE".

Suggested column:"""
    
    return prompt


async def request_sampling(prompt: str, system_prompt: Optional[str] = None) -> str:
    """
    Request sampling from MCP host LLM
    
    This function uses MCP's sampling protocol to ask the host LLM for help.
    In FastMCP, this is typically done through a sampling endpoint or method.
    
    Args:
        prompt: User prompt/question
        system_prompt: Optional system prompt for context
    
    Returns:
        LLM response text
    """
    # Note: FastMCP sampling implementation may vary
    # This is a placeholder that shows the expected interface
    # In actual FastMCP, you might use:
    # - mcp.sample() method
    # - mcp.request_sampling() method
    # - Or a sampling tool/endpoint
    
    # For now, we'll use a simple mock implementation
    # In production, replace this with actual MCP sampling call
    try:
        # Attempt to use MCP sampling if available
        if hasattr(mcp, 'sample'):
            response = await mcp.sample(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt or "You are a database schema expert.",
                max_tokens=100
            )
            return response
        elif hasattr(mcp, 'request_sampling'):
            response = await mcp.request_sampling({
                "messages": [{"role": "user", "content": prompt}],
                "systemPrompt": system_prompt or "You are a database schema expert.",
                "maxTokens": 100
            })
            return response
        else:
            # Fallback: Simple rule-based matching (for testing without MCP sampling)
            return _mock_llm_response(prompt, failed_column=None)
    except Exception as e:
        # If sampling fails, fall back to first alternative or mock response
        print(f"Warning: MCP sampling failed: {e}. Using fallback.")
        return _mock_llm_response(prompt, failed_column=None)


def _mock_llm_response(prompt: str, failed_column: Optional[str] = None) -> str:
    """
    Mock LLM response for testing (fallback when MCP sampling not available)
    
    In production, this should not be used - real MCP sampling should be implemented.
    
    Args:
        prompt: The prompt sent to LLM
        failed_column: The failed column name (if known)
    
    Returns:
        Mock response (column name)
    """
    # Extract alternatives from prompt
    if "Available alternative column names" in prompt:
        match = re.search(r'Available alternative column names.*?: (.+?)\n', prompt)
        if match:
            alternatives_str = match.group(1)
            if alternatives_str != "none found":
                alternatives = [alt.strip() for alt in alternatives_str.split(",")]
                # Return first alternative as mock suggestion
                return alternatives[0].strip()
    
    return "NONE"


def parse_llm_response(response: str) -> Optional[str]:
    """
    Parse LLM response to extract column name
    
    Args:
        response: LLM response text
    
    Returns:
        Column name or None if no valid suggestion
    """
    # Clean response: remove quotes, whitespace, newlines
    cleaned = response.strip().strip('"').strip("'").strip()
    
    # Remove common prefixes/suffixes
    cleaned = re.sub(r'^(The|Suggested|Correct|Column name:?)\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    
    # If response is "NONE" or empty, return None
    if not cleaned or cleaned.upper() == "NONE":
        return None
    
    # Return cleaned column name
    return cleaned


def rebuild_query(original_query: str, old_column: str, new_column: str) -> str:
    """
    Rebuild SQL query with corrected column name
    
    Args:
        original_query: Original SQL query
        old_column: Column name to replace
        new_column: New column name
    
    Returns:
        Modified SQL query
    """
    # Use regex to replace column name (case-insensitive, word boundaries)
    pattern = r'\b' + re.escape(old_column) + r'\b'
    
    def replace_func(match):
        matched_text = match.group(0)
        # Preserve original case for first letter if needed
        if matched_text[0].isupper():
            return new_column.capitalize()
        return new_column.lower()
    
    modified_query = re.sub(pattern, replace_func, original_query, flags=re.IGNORECASE)
    
    return modified_query


@mcp.tool()
async def query_with_healing(
    table: str,
    column: str,
    filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a SQL query with self-healing capabilities.
    
    If the query fails due to column/table not found, the system will:
    1. Find semantic alternatives from ontology
    2. Ask LLM (via MCP sampling) for the best correction
    3. Retry with corrected query
    4. Learn the mapping for future use
    
    Args:
        table: Table name to query
        column: Column name to select
        filter: Optional WHERE clause filter (e.g., "id = 1")
    
    Returns:
        Dictionary with query results and healing information
    """
    # Build initial query
    query = f"SELECT {column} FROM {table}"
    if filter:
        query += f" WHERE {filter}"
    
    max_retries = 2
    attempt = 0
    last_error = None
    healing_history = []
    
    while attempt <= max_retries:
        try:
            # Execute query
            result = sql_executor.execute(query)
            
            # Success!
            response = {
                "success": True,
                "query": query,
                "result": result,
                "attempt": attempt + 1,
                "healing_applied": len(healing_history) > 0,
                "healing_history": healing_history
            }
            
            # If healing was applied, save the mapping
            if healing_history:
                last_healing = healing_history[-1]
                save_learned_mapping(
                    table=table,
                    failed_column=last_healing["failed_column"],
                    suggested_column=last_healing["suggested_column"]
                )
            
            return response
            
        except ColumnNotFoundError as e:
            last_error = e
            error_message = str(e)
            
            # Extract column name from error
            column_match = re.search(r"Column '([^']+)'", error_message)
            failed_column = column_match.group(1) if column_match else column
            
            # Don't heal if we've already tried this
            if any(h["failed_column"] == failed_column for h in healing_history):
                break
            
            # Find semantic alternatives
            alternatives = find_semantic_alternatives(failed_column, table)
            
            if not alternatives:
                # No alternatives found, fail
                return {
                    "success": False,
                    "error": error_message,
                    "query": query,
                    "attempt": attempt + 1,
                    "healing_applied": False,
                    "message": "No semantic alternatives found for failed column"
                }
            
            # Build healing prompt
            healing_prompt = build_healing_prompt(
                failed_column=failed_column,
                table=table,
                alternatives=alternatives,
                error_message=error_message
            )
            
            # Request LLM suggestion via MCP sampling
            try:
                llm_response = await request_sampling(
                    prompt=healing_prompt,
                    system_prompt="You are a database schema expert. Suggest the most likely correct column name."
                )
                
                suggested_column = parse_llm_response(llm_response)
                
                if not suggested_column or suggested_column not in alternatives:
                    # LLM didn't suggest a valid alternative
                    # Use first alternative as fallback
                    suggested_column = alternatives[0]
                
            except Exception as e:
                # If sampling fails, use first alternative
                print(f"Warning: LLM sampling failed: {e}. Using first alternative.")
                suggested_column = alternatives[0]
            
            # Rebuild query with suggested column
            query = rebuild_query(query, failed_column, suggested_column)
            
            # Record healing attempt
            healing_history.append({
                "failed_column": failed_column,
                "alternatives": alternatives,
                "suggested_column": suggested_column,
                "llm_response": llm_response if 'llm_response' in locals() else None
            })
            
            attempt += 1
            
        except TableNotFoundError as e:
            # Table not found - don't try to heal
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "attempt": attempt + 1,
                "healing_applied": False,
                "message": "Table not found - cannot heal"
            }
        
        except TypeMismatchError as e:
            # Type mismatch - don't try to heal
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "attempt": attempt + 1,
                "healing_applied": False,
                "message": "Type mismatch - cannot heal"
            }
        
        except Exception as e:
            # Other errors - don't try to heal
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "attempt": attempt + 1,
                "healing_applied": False,
                "message": f"Unexpected error: {type(e).__name__}"
            }
    
    # Max retries exceeded
    return {
        "success": False,
        "error": str(last_error) if last_error else "Unknown error",
        "query": query,
        "attempt": attempt + 1,
        "healing_applied": len(healing_history) > 0,
        "healing_history": healing_history,
        "message": f"Max retries ({max_retries}) exceeded"
    }


# MCP Server Entry Point
if __name__ == "__main__":
    mcp.run()

