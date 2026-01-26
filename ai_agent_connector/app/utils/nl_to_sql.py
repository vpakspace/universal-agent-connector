"""
Natural Language to SQL conversion using LLM
"""

import os
import json
from typing import Optional, Dict, List, Any
from ..db import DatabaseConnector
from .air_gapped import is_air_gapped_mode, get_local_ai_config, AirGappedModeError

# Global cost tracker instance (will be initialized in routes.py)
_cost_tracker = None

def set_cost_tracker(tracker):
    """Set the global cost tracker instance"""
    global _cost_tracker
    _cost_tracker = tracker


class NLToSQLConverter:
    """Converts natural language queries to SQL using LLM"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, api_base: Optional[str] = None):
        """
        Initialize the NL to SQL converter
        
        Args:
            api_key: API key (defaults to OPENAI_API_KEY env var, or LOCAL_AI_API_KEY for local)
            model: Model to use for conversion (default: gpt-4o-mini or LOCAL_AI_MODEL)
            api_base: API base URL (for local models, defaults to LOCAL_AI_BASE_URL)
        """
        # Check air-gapped mode
        if is_air_gapped_mode():
            # Use local AI configuration
            local_config = get_local_ai_config()
            self.api_base = api_base or local_config['base_url']
            self.model = model or local_config['model']
            self.api_key = api_key or local_config.get('api_key') or 'not-needed'
        else:
            # Use OpenAI or custom configuration
            self.api_key = api_key or os.getenv('OPENAI_API_KEY')
            self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            self.api_base = api_base or os.getenv('OPENAI_BASE_URL')  # Optional, defaults to OpenAI
        
        self._client = None
    
    def _get_client(self):
        """Lazy load OpenAI-compatible client"""
        if self._client is None:
            try:
                import openai
                
                # Check air-gapped mode
                if is_air_gapped_mode():
                    # Use local AI
                    if not self.api_base:
                        local_config = get_local_ai_config()
                        self.api_base = local_config['base_url']
                    self._client = openai.OpenAI(
                        base_url=self.api_base,
                        api_key=self.api_key or 'not-needed',
                        timeout=60  # Longer timeout for local models
                    )
                else:
                    # Use OpenAI or custom endpoint
                    if not self.api_key and not self.api_base:
                        raise ValueError(
                            "OPENAI_API_KEY environment variable is required, or enable air-gapped mode"
                        )
                    if self.api_base:
                        # Custom endpoint
                        self._client = openai.OpenAI(
                            base_url=self.api_base,
                            api_key=self.api_key or 'not-needed'
                        )
                    else:
                        # Standard OpenAI
                        self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package is required. Install it with: pip install openai"
                )
        return self._client
    
    def get_schema_info(self, connector: DatabaseConnector) -> Dict[str, Any]:
        """
        Get database schema information to help with SQL generation
        
        Args:
            connector: Database connector instance
            
        Returns:
            Dict containing schema information
        """
        try:
            connector.connect()
            
            # Get tables and their columns
            schema_query = """
                SELECT 
                    t.table_schema,
                    t.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default
                FROM information_schema.tables t
                JOIN information_schema.columns c 
                    ON t.table_schema = c.table_schema 
                    AND t.table_name = c.table_name
                WHERE t.table_type = 'BASE TABLE'
                    AND t.table_schema NOT IN ('information_schema', 'pg_catalog')
                ORDER BY t.table_schema, t.table_name, c.ordinal_position
            """
            
            results = connector.execute_query(schema_query, fetch=True, as_dict=False)
            
            # Organize by table
            schema = {}
            for row in results:
                schema_name, table_name, col_name, data_type, nullable, default = row
                full_table = f"{schema_name}.{table_name}" if schema_name != 'public' else table_name
                
                if full_table not in schema:
                    schema[full_table] = {
                        'schema': schema_name,
                        'table': table_name,
                        'columns': []
                    }
                
                schema[full_table]['columns'].append({
                    'name': col_name,
                    'type': data_type,
                    'nullable': nullable == 'YES',
                    'default': default
                })
            
            return {
                'tables': list(schema.keys()),
                'schema': schema
            }
            
        except Exception as e:
            # Return minimal schema info on error
            return {
                'tables': [],
                'schema': {},
                'error': str(e)
            }
        finally:
            try:
                connector.disconnect()
            except Exception:
                pass
    
    def convert_to_sql(
        self,
        natural_language_query: str,
        schema_info: Optional[Dict[str, Any]] = None,
        database_type: str = "PostgreSQL",
        custom_prompt: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convert natural language query to SQL
        
        Args:
            natural_language_query: Natural language question
            schema_info: Optional schema information
            database_type: Type of database (default: PostgreSQL)
            custom_prompt: Optional custom prompt template with system_prompt and user_prompt_template
            
        Returns:
            Dict containing SQL query and metadata
        """
        if not natural_language_query or not natural_language_query.strip():
            return {
                'error': 'Natural language query is required',
                'sql': None
            }
        
        try:
            client = self._get_client()
            
            # Use custom prompt if provided
            if custom_prompt:
                system_prompt = custom_prompt.get('system_prompt', '')
                user_prompt = custom_prompt.get('user_prompt', natural_language_query)
            else:
                # Build default system prompt
                system_prompt = f"""You are a SQL expert specializing in {database_type} databases.
Your task is to convert natural language questions into accurate SQL queries.

Rules:
1. Generate ONLY valid {database_type} SQL
2. Use proper table and column names from the schema
3. For PostgreSQL, use proper schema.table notation when needed
4. Return ONLY the SQL query, no explanations or markdown
5. Use parameterized queries with %s for values when appropriate
6. Ensure the query is safe and follows best practices

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
                    system_prompt += "\nNo schema information available. Use standard table/column names."
                
                user_prompt = natural_language_query
            
            # Make API call
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for more deterministic SQL
                max_tokens=500
            )
            
            sql_query = response.choices[0].message.content.strip()
            
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
                        operation_type='nl_to_sql',
                        metadata={'query': natural_language_query}
                    )
                except Exception:
                    pass  # Don't fail if cost tracking fails
            
            # Clean up SQL (remove markdown code blocks if present)
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            elif sql_query.startswith("```"):
                sql_query = sql_query[3:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            sql_query = sql_query.strip()
            
            return {
                'sql': sql_query,
                'natural_language': natural_language_query,
                'model': self.model
            }
            
        except Exception as e:
            return {
                'error': f'Failed to convert to SQL: {str(e)}',
                'sql': None,
                'natural_language': natural_language_query
            }
    
    def convert_with_schema(
        self,
        natural_language_query: str,
        connector: DatabaseConnector,
        database_type: str = "PostgreSQL"
    ) -> Dict[str, Any]:
        """
        Convert natural language to SQL with automatic schema detection
        
        Args:
            natural_language_query: Natural language question
            connector: Database connector to get schema from
            database_type: Type of database
            
        Returns:
            Dict containing SQL query and metadata
        """
        schema_info = self.get_schema_info(connector)
        return self.convert_to_sql(natural_language_query, schema_info, database_type)

