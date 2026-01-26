"""
SQL query suggestion system for ambiguous natural language inputs
Generates multiple optimized SQL query options
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import os
import json

# Global cost tracker instance (will be initialized in routes.py)
_cost_tracker = None

def set_cost_tracker(tracker):
    """Set the global cost tracker instance"""
    global _cost_tracker
    _cost_tracker = tracker


@dataclass
class QuerySuggestion:
    """A suggested SQL query option"""
    sql: str
    confidence: float  # 0.0 to 1.0
    explanation: str
    estimated_cost: Optional[str] = None  # e.g., "low", "medium", "high"
    optimization_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'sql': self.sql,
            'confidence': self.confidence,
            'explanation': self.explanation,
            'estimated_cost': self.estimated_cost,
            'optimization_notes': self.optimization_notes
        }


class QuerySuggestionEngine:
    """
    Generates multiple SQL query suggestions for ambiguous natural language inputs.
    Uses LLM to generate optimized alternatives.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize query suggestion engine.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use for suggestions
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy load OpenAI client"""
        if self._client is None:
            try:
                import openai
                if not self.api_key:
                    raise ValueError("OPENAI_API_KEY environment variable is required")
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package is required")
        return self._client
    
    def suggest_queries(
        self,
        natural_language_query: str,
        schema_info: Optional[Dict[str, Any]] = None,
        database_type: str = "PostgreSQL",
        num_suggestions: int = 3
    ) -> List[QuerySuggestion]:
        """
        Generate multiple SQL query suggestions for an ambiguous natural language query.
        
        Args:
            natural_language_query: Natural language question
            schema_info: Optional schema information
            database_type: Type of database
            num_suggestions: Number of suggestions to generate (default: 3)
            
        Returns:
            List of QuerySuggestion objects, sorted by confidence
        """
        if not natural_language_query or not natural_language_query.strip():
            return []
        
        try:
            client = self._get_client()
            
            # Build system prompt for generating multiple optimized queries
            system_prompt = f"""You are a SQL optimization expert specializing in {database_type} databases.
Your task is to generate multiple optimized SQL query options for ambiguous natural language questions.

For each query, provide:
1. The SQL query (valid {database_type} SQL only)
2. Confidence score (0.0 to 1.0) - how well this query matches the intent
3. Brief explanation of the interpretation
4. Estimated cost (low/medium/high) - query performance estimate
5. Optimization notes (indexes used, query patterns, etc.)

Generate {num_suggestions} different interpretations/optimizations of the query.
Return as JSON array with format:
[
    {{
        "sql": "SELECT ...",
        "confidence": 0.95,
        "explanation": "...",
        "estimated_cost": "low",
        "optimization_notes": "..."
    }},
    ...
]

Schema Information:"""
            
            # Add schema information if available
            if schema_info and schema_info.get('schema'):
                schema_text = "\n\nTables and Columns:\n"
                for table_name, table_info in schema_info['schema'].items():
                    schema_text += f"\n{table_name}:\n"
                    for col in table_info['columns']:
                        schema_text += f"  - {col['name']} ({col['type']})\n"
                system_prompt += schema_text
            else:
                system_prompt += "\nNo schema information available."
            
            # Make API call
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Generate {num_suggestions} optimized SQL query options for: {natural_language_query}. Return as JSON array."}
                    ],
                    temperature=0.3,  # Slightly higher for variety
                    max_tokens=1500
                )
            except Exception as e:
                # If JSON mode fails, try without it
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Generate {num_suggestions} optimized SQL query options for: {natural_language_query}. Return as JSON array."}
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
            
            content = response.choices[0].message.content.strip()
            
            # Track cost
            if _cost_tracker and hasattr(response, 'usage'):
                try:
                    usage_data = {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    }
                    _cost_tracker.track_call(
                        provider='openai',
                        model=self.model,
                        usage=usage_data,
                        agent_id=None,
                        operation_type='suggestion',
                        metadata={'query': natural_language_query, 'num_suggestions': num_suggestions}
                    )
                except Exception:
                    pass  # Don't fail if cost tracking fails
            
            # Parse JSON response
            try:
                data = json.loads(content)
                # Handle both {"suggestions": [...]} and [...] formats
                if isinstance(data, dict) and 'suggestions' in data:
                    suggestions_data = data['suggestions']
                elif isinstance(data, list):
                    suggestions_data = data
                else:
                    suggestions_data = [data]
                
                suggestions = []
                for sug_data in suggestions_data:
                    suggestion = QuerySuggestion(
                        sql=sug_data.get('sql', '').strip(),
                        confidence=float(sug_data.get('confidence', 0.5)),
                        explanation=sug_data.get('explanation', ''),
                        estimated_cost=sug_data.get('estimated_cost'),
                        optimization_notes=sug_data.get('optimization_notes')
                    )
                    # Clean SQL (remove markdown if present)
                    if suggestion.sql.startswith("```sql"):
                        suggestion.sql = suggestion.sql[6:]
                    elif suggestion.sql.startswith("```"):
                        suggestion.sql = suggestion.sql[3:]
                    if suggestion.sql.endswith("```"):
                        suggestion.sql = suggestion.sql[:-3]
                    suggestion.sql = suggestion.sql.strip()
                    
                    if suggestion.sql:
                        suggestions.append(suggestion)
                
                # Sort by confidence (highest first)
                suggestions.sort(key=lambda x: x.confidence, reverse=True)
                
                return suggestions
                
            except json.JSONDecodeError:
                # Fallback: try to extract SQL from text response
                return self._parse_suggestions_from_text(content)
            
        except Exception as e:
            # Return empty list on error
            return []
    
    def _parse_suggestions_from_text(self, text: str) -> List[QuerySuggestion]:
        """Fallback parser for text responses"""
        suggestions = []
        # Simple heuristic: look for SQL queries in the text
        import re
        sql_pattern = r'SELECT.*?(?=\n\n|\Z)'
        matches = re.finditer(sql_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for i, match in enumerate(matches):
            sql = match.group(0).strip()
            if sql:
                suggestions.append(QuerySuggestion(
                    sql=sql,
                    confidence=0.8 - (i * 0.1),  # Decreasing confidence
                    explanation=f"Option {i+1}",
                    estimated_cost="medium"
                ))
        
        return suggestions[:3]  # Return max 3

