"""
Utility helper functions
"""

import json
from typing import Any, Dict, Optional
from datetime import datetime


def format_response(data: Any, status_code: int = 200) -> tuple:
    """
    Format API response
    
    Args:
        data: Response data
        status_code: HTTP status code
        
    Returns:
        tuple: (formatted_data, status_code)
    """
    if isinstance(data, dict):
        return data, status_code
    return {'data': data}, status_code


def validate_json(data: Dict, required_fields: list) -> Optional[str]:
    """
    Validate JSON data contains required fields
    
    Args:
        data: JSON data to validate
        required_fields: List of required field names
        
    Returns:
        Optional[str]: Error message if validation fails, None otherwise
    """
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    
    return None


def get_timestamp() -> str:
    """
    Get current timestamp as ISO format string
    
    Returns:
        str: ISO formatted timestamp
    """
    return datetime.utcnow().isoformat() + 'Z'


def safe_json_loads(data: str) -> Optional[Dict]:
    """
    Safely parse JSON string
    
    Args:
        data: JSON string to parse
        
    Returns:
        Optional[Dict]: Parsed JSON or None if invalid
    """
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None

