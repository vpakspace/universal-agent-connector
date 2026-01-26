"""
Autocomplete suggestions for table/column names
Provides autocomplete suggestions for natural language queries
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import re


@dataclass
class AutocompleteSuggestion:
    """An autocomplete suggestion"""
    text: str
    type: str  # 'table', 'column', 'keyword'
    display_text: str
    description: Optional[str] = None
    relevance_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'type': self.type,
            'display_text': self.display_text,
            'description': self.description,
            'relevance_score': self.relevance_score
        }


class AutocompleteProvider:
    """
    Provides autocomplete suggestions for table and column names.
    """
    
    def __init__(self):
        """Initialize autocomplete provider"""
        pass
    
    def get_suggestions(
        self,
        query: str,
        cursor_position: int,
        schema_info: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[AutocompleteSuggestion]:
        """
        Get autocomplete suggestions for a query.
        
        Args:
            query: Current query text
            cursor_position: Cursor position in query
            schema_info: Schema information
            context: Optional context (current table, etc.)
            
        Returns:
            List of AutocompleteSuggestion objects
        """
        suggestions = []
        
        # Extract current word being typed
        current_word = self._extract_current_word(query, cursor_position)
        
        if not current_word:
            return suggestions
        
        current_word_lower = current_word.lower()
        
        # Get tables
        tables = schema_info.get('tables', {})
        for table_name, table_info in tables.items():
            if current_word_lower in table_name.lower() or table_name.lower().startswith(current_word_lower):
                score = self._calculate_relevance(table_name, current_word)
                suggestions.append(AutocompleteSuggestion(
                    text=table_name,
                    type='table',
                    display_text=table_name,
                    description=table_info.get('description', f"Table: {table_name}"),
                    relevance_score=score
                ))
        
        # Get columns (if context has a table)
        if context and context.get('current_table'):
            table_name = context['current_table']
            table_info = tables.get(table_name, {})
            columns = table_info.get('columns', [])
            
            for col in columns:
                col_name = col.get('name', '')
                if current_word_lower in col_name.lower() or col_name.lower().startswith(current_word_lower):
                    score = self._calculate_relevance(col_name, current_word)
                    suggestions.append(AutocompleteSuggestion(
                        text=col_name,
                        type='column',
                        display_text=f"{table_name}.{col_name}",
                        description=col.get('description', f"Column: {col_name} ({col.get('type', 'unknown')})"),
                        relevance_score=score
                    ))
        else:
            # Search all columns across all tables
            for table_name, table_info in tables.items():
                columns = table_info.get('columns', [])
                for col in columns:
                    col_name = col.get('name', '')
                    if current_word_lower in col_name.lower() or col_name.lower().startswith(current_word_lower):
                        score = self._calculate_relevance(col_name, current_word) * 0.8  # Lower score for cross-table
                        suggestions.append(AutocompleteSuggestion(
                            text=col_name,
                            type='column',
                            display_text=f"{table_name}.{col_name}",
                            description=col.get('description', f"Column: {col_name} ({col.get('type', 'unknown')})"),
                            relevance_score=score
                        ))
        
        # Add SQL keywords if they match
        sql_keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'ORDER BY', 'GROUP BY', 'HAVING', 'LIMIT']
        for keyword in sql_keywords:
            if current_word_lower in keyword.lower() or keyword.lower().startswith(current_word_lower):
                suggestions.append(AutocompleteSuggestion(
                    text=keyword,
                    type='keyword',
                    display_text=keyword,
                    description=f"SQL keyword: {keyword}",
                    relevance_score=0.5
                ))
        
        # Sort by relevance score
        suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit to top 20
        return suggestions[:20]
    
    def _extract_current_word(self, query: str, cursor_position: int) -> str:
        """Extract the current word being typed"""
        if cursor_position < 0 or cursor_position > len(query):
            return ""
        
        # Find word boundaries
        start = cursor_position
        end = cursor_position
        
        # Move start backwards to beginning of word
        while start > 0 and (query[start - 1].isalnum() or query[start - 1] in ['_', '.']):
            start -= 1
        
        # Move end forwards to end of word
        while end < len(query) and (query[end].isalnum() or query[end] in ['_', '.']):
            end += 1
        
        return query[start:end]
    
    def _calculate_relevance(self, candidate: str, query: str) -> float:
        """Calculate relevance score for a candidate"""
        candidate_lower = candidate.lower()
        query_lower = query.lower()
        
        score = 0.0
        
        # Exact match
        if candidate_lower == query_lower:
            score += 1.0
        # Starts with query
        elif candidate_lower.startswith(query_lower):
            score += 0.8
        # Contains query
        elif query_lower in candidate_lower:
            score += 0.5
        
        # Length penalty (shorter is better)
        length_penalty = min(len(candidate) / 50.0, 0.3)
        score -= length_penalty
        
        return max(0.0, score)
    
    def get_table_suggestions(
        self,
        partial_name: str,
        schema_info: Dict[str, Any]
    ) -> List[AutocompleteSuggestion]:
        """
        Get table name suggestions.
        
        Args:
            partial_name: Partial table name
            schema_info: Schema information
            
        Returns:
            List of table suggestions
        """
        suggestions = []
        partial_lower = partial_name.lower()
        
        tables = schema_info.get('tables', {})
        for table_name, table_info in tables.items():
            if partial_lower in table_name.lower() or table_name.lower().startswith(partial_lower):
                score = self._calculate_relevance(table_name, partial_name)
                suggestions.append(AutocompleteSuggestion(
                    text=table_name,
                    type='table',
                    display_text=table_name,
                    description=table_info.get('description', f"Table: {table_name}"),
                    relevance_score=score
                ))
        
        suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
        return suggestions[:10]
    
    def get_column_suggestions(
        self,
        table_name: str,
        partial_name: str,
        schema_info: Dict[str, Any]
    ) -> List[AutocompleteSuggestion]:
        """
        Get column name suggestions for a table.
        
        Args:
            table_name: Table name
            partial_name: Partial column name
            schema_info: Schema information
            
        Returns:
            List of column suggestions
        """
        suggestions = []
        partial_lower = partial_name.lower()
        
        tables = schema_info.get('tables', {})
        table_info = tables.get(table_name, {})
        columns = table_info.get('columns', [])
        
        for col in columns:
            col_name = col.get('name', '')
            if partial_lower in col_name.lower() or col_name.lower().startswith(partial_lower):
                score = self._calculate_relevance(col_name, partial_name)
                suggestions.append(AutocompleteSuggestion(
                    text=col_name,
                    type='column',
                    display_text=f"{table_name}.{col_name}",
                    description=col.get('description', f"Column: {col_name} ({col.get('type', 'unknown')})"),
                    relevance_score=score
                ))
        
        suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
        return suggestions[:10]

