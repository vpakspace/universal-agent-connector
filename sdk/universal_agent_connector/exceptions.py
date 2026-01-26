"""
Exception classes for the Universal Agent Connector SDK
"""


class UniversalAgentConnectorError(Exception):
    """Base exception for all SDK errors"""
    pass


class APIError(UniversalAgentConnectorError):
    """Raised when API returns an error response"""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class AuthenticationError(APIError):
    """Raised when authentication fails"""
    pass


class NotFoundError(APIError):
    """Raised when a resource is not found (404)"""
    pass


class ValidationError(APIError):
    """Raised when request validation fails (400)"""
    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded (429)"""
    pass


class ConnectionError(UniversalAgentConnectorError):
    """Raised when connection to API fails"""
    pass
