"""
Error message formatting for clear, actionable error messages
"""

from typing import Dict, List, Optional, Any
import re


class ErrorFormatter:
    """
    Formats database errors into clear, actionable messages.
    """
    
    # Common error patterns and their user-friendly messages
    ERROR_PATTERNS = [
        # PostgreSQL errors
        (r'column "(.+)" does not exist', r'Invalid column name: "\1". Please check the column name and try again.'),
        (r'relation "(.+)" does not exist', r'Table "\1" does not exist. Please check the table name and try again.'),
        (r'syntax error at or near "(.+)"', r'SQL syntax error near "\1". Please check your query syntax.'),
        (r'permission denied for (.+)', r'Permission denied: You do not have access to "\1".'),
        (r'duplicate key value violates unique constraint', r'Duplicate entry: This record already exists.'),
        (r'violates foreign key constraint', r'Referential integrity error: The referenced record does not exist.'),
        (r'null value in column "(.+)" violates not-null constraint', r'Required field "\1" cannot be empty.'),
        (r'value too long for type', r'Value is too long for this field. Please shorten the value.'),
        (r'connection.*refused', r'Database connection refused. Please check if the database server is running.'),
        (r'connection.*timeout', r'Database connection timeout. The server may be overloaded or unreachable.'),
        (r'authentication failed', r'Database authentication failed. Please check your credentials.'),
        
        # MySQL errors
        (r'Unknown column \'(.+)\' in', r'Invalid column name: "\1". Please check the column name and try again.'),
        (r'Table \'(.+)\' doesn\'t exist', r'Table "\1" does not exist. Please check the table name and try again.'),
        (r'You have an error in your SQL syntax', r'SQL syntax error. Please check your query syntax.'),
        (r'Access denied for user', r'Database access denied. Please check your credentials.'),
        (r'Duplicate entry', r'Duplicate entry: This record already exists.'),
        
        # Generic errors
        (r'timeout', r'Operation timed out. The query took too long to execute.'),
        (r'connection.*lost', r'Database connection lost. Please try again.'),
        (r'network.*error', r'Network error: Unable to reach the database server.'),
        (r'out of memory', r'Out of memory: The query requires too much memory to execute.'),
    ]
    
    @staticmethod
    def format_error(
        error: Exception,
        query: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format an error into a clear, actionable message.
        
        Args:
            error: The exception that occurred
            query: Optional query that failed
            context: Optional additional context
            
        Returns:
            Dict with formatted error information
        """
        error_message = str(error)
        error_type = type(error).__name__
        
        # Try to match error patterns
        user_friendly_message = ErrorFormatter._match_error_pattern(error_message)
        
        # If no pattern matched, create a generic message
        if not user_friendly_message:
            user_friendly_message = ErrorFormatter._create_generic_message(error_type, error_message)
        
        # Extract actionable details
        actionable_details = ErrorFormatter._extract_actionable_details(error_message, error_type)
        
        # Build response
        formatted_error = {
            'error_type': error_type,
            'error_message': error_message,
            'user_friendly_message': user_friendly_message,
            'actionable_details': actionable_details,
            'suggested_fixes': ErrorFormatter._suggest_fixes(error_type, error_message, query)
        }
        
        if query:
            formatted_error['query'] = query[:200]  # Truncate long queries
        
        if context:
            formatted_error['context'] = context
        
        return formatted_error
    
    @staticmethod
    def _match_error_pattern(error_message: str) -> Optional[str]:
        """Match error message against known patterns"""
        error_lower = error_message.lower()
        
        for pattern, replacement in ErrorFormatter.ERROR_PATTERNS:
            match = re.search(pattern, error_lower, re.IGNORECASE)
            if match:
                # Replace placeholders in replacement
                formatted = replacement
                for i, group in enumerate(match.groups(), 1):
                    formatted = formatted.replace(f'\\{i}', group)
                return formatted
        
        return None
    
    @staticmethod
    def _create_generic_message(error_type: str, error_message: str) -> str:
        """Create a generic user-friendly message"""
        # Extract key information from error type
        if 'Connection' in error_type or 'Timeout' in error_type:
            return 'Database connection error. Please check your connection settings and try again.'
        elif 'Permission' in error_type or 'Access' in error_type:
            return 'Access denied. Please check your permissions and try again.'
        elif 'Syntax' in error_type or 'Parse' in error_type:
            return 'Query syntax error. Please check your query and try again.'
        elif 'Integrity' in error_type or 'Constraint' in error_type:
            return 'Data integrity error. Please check your data and try again.'
        else:
            return f'An error occurred: {error_message[:100]}. Please check your query and try again.'
    
    @staticmethod
    def _extract_actionable_details(error_message: str, error_type: str) -> Dict[str, Any]:
        """Extract actionable details from error message"""
        details = {}
        
        # Extract column/table names
        column_match = re.search(r'column ["\']?([^"\']+)["\']?', error_message, re.IGNORECASE)
        if column_match:
            details['column'] = column_match.group(1)
        
        table_match = re.search(r'(?:table|relation) ["\']?([^"\']+)["\']?', error_message, re.IGNORECASE)
        if table_match:
            details['table'] = table_match.group(1)
        
        # Extract constraint names
        constraint_match = re.search(r'constraint ["\']?([^"\']+)["\']?', error_message, re.IGNORECASE)
        if constraint_match:
            details['constraint'] = constraint_match.group(1)
        
        # Extract line numbers for syntax errors
        line_match = re.search(r'line (\d+)', error_message, re.IGNORECASE)
        if line_match:
            details['line_number'] = int(line_match.group(1))
        
        return details
    
    @staticmethod
    def _suggest_fixes(error_type: str, error_message: str, query: Optional[str]) -> List[str]:
        """Suggest fixes based on error type and message"""
        suggestions = []
        error_lower = error_message.lower()
        
        if 'column' in error_lower and 'does not exist' in error_lower:
            suggestions.append('Check the column name spelling and case sensitivity')
            suggestions.append('Verify the column exists in the table')
            if query:
                suggestions.append('Review your SELECT statement for typos')
        
        elif 'table' in error_lower and ('does not exist' in error_lower or "doesn't exist" in error_lower):
            suggestions.append('Check the table name spelling')
            suggestions.append('Verify the table exists in the database')
            suggestions.append('Check if you need to specify a schema (e.g., schema.table)')
        
        elif 'syntax' in error_lower or 'parse' in error_lower:
            suggestions.append('Check for missing or extra commas, quotes, or parentheses')
            suggestions.append('Verify SQL keywords are spelled correctly')
            suggestions.append('Check for unclosed quotes or parentheses')
        
        elif 'permission' in error_lower or 'access denied' in error_lower:
            suggestions.append('Contact your administrator to grant the required permissions')
            suggestions.append('Verify you are using the correct database user')
        
        elif 'connection' in error_lower or 'timeout' in error_lower:
            suggestions.append('Check if the database server is running')
            suggestions.append('Verify network connectivity')
            suggestions.append('Check firewall settings')
            suggestions.append('Try again in a few moments')
        
        elif 'duplicate' in error_lower or 'unique constraint' in error_lower:
            suggestions.append('Check if a record with the same key already exists')
            suggestions.append('Use UPDATE instead of INSERT if updating existing records')
        
        elif 'foreign key' in error_lower:
            suggestions.append('Ensure the referenced record exists before creating this record')
            suggestions.append('Check the foreign key relationship is correct')
        
        elif 'null' in error_lower and 'not-null' in error_lower:
            suggestions.append('Provide a value for all required fields')
            suggestions.append('Check which fields are marked as NOT NULL')
        
        else:
            suggestions.append('Review the error message for specific details')
            suggestions.append('Check the query syntax and data types')
            suggestions.append('Contact support if the issue persists')
        
        return suggestions

