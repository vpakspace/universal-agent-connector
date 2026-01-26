"""
Test exception classes
"""

import pytest
from universal_agent_connector import (
    UniversalAgentConnectorError,
    APIError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ConnectionError
)


class TestExceptionHierarchy:
    """Test exception class hierarchy"""
    
    def test_base_exception(self):
        """Test base exception"""
        error = UniversalAgentConnectorError("Base error")
        assert str(error) == "Base error"
        assert isinstance(error, Exception)
    
    def test_api_error(self):
        """Test APIError"""
        error = APIError("API error", status_code=500, response={"message": "Error"})
        assert str(error) == "API error"
        assert error.status_code == 500
        assert error.response == {"message": "Error"}
        assert isinstance(error, UniversalAgentConnectorError)
    
    def test_authentication_error(self):
        """Test AuthenticationError"""
        error = AuthenticationError("Auth failed", status_code=401)
        assert str(error) == "Auth failed"
        assert error.status_code == 401
        assert isinstance(error, APIError)
        assert isinstance(error, UniversalAgentConnectorError)
    
    def test_not_found_error(self):
        """Test NotFoundError"""
        error = NotFoundError("Not found", status_code=404)
        assert str(error) == "Not found"
        assert error.status_code == 404
        assert isinstance(error, APIError)
    
    def test_validation_error(self):
        """Test ValidationError"""
        error = ValidationError("Invalid input", status_code=400)
        assert str(error) == "Invalid input"
        assert error.status_code == 400
        assert isinstance(error, APIError)
    
    def test_rate_limit_error(self):
        """Test RateLimitError"""
        error = RateLimitError("Rate limit exceeded", status_code=429)
        assert str(error) == "Rate limit exceeded"
        assert error.status_code == 429
        assert isinstance(error, APIError)
    
    def test_connection_error(self):
        """Test ConnectionError"""
        error = ConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, UniversalAgentConnectorError)
    
    def test_exception_inheritance(self):
        """Test exception inheritance chain"""
        auth_error = AuthenticationError("Test")
        assert isinstance(auth_error, APIError)
        assert isinstance(auth_error, UniversalAgentConnectorError)
        assert isinstance(auth_error, Exception)
        
        not_found = NotFoundError("Test")
        assert isinstance(not_found, APIError)
        assert isinstance(not_found, UniversalAgentConnectorError)
        
        conn_error = ConnectionError("Test")
        assert isinstance(conn_error, UniversalAgentConnectorError)
        assert not isinstance(conn_error, APIError)


class TestExceptionUsage:
    """Test exception usage in error handling"""
    
    def test_catch_base_exception(self):
        """Test catching base exception"""
        try:
            raise UniversalAgentConnectorError("Base error")
        except UniversalAgentConnectorError as e:
            assert str(e) == "Base error"
    
    def test_catch_specific_exception(self):
        """Test catching specific exception"""
        try:
            raise NotFoundError("Not found", status_code=404)
        except NotFoundError as e:
            assert e.status_code == 404
        except APIError:
            pytest.fail("Should catch NotFoundError, not APIError")
    
    def test_catch_parent_exception(self):
        """Test catching parent exception"""
        try:
            raise AuthenticationError("Auth failed", status_code=401)
        except APIError as e:
            assert e.status_code == 401
            assert isinstance(e, AuthenticationError)
    
    def test_exception_with_response_data(self):
        """Test exception with response data"""
        response_data = {
            "error": "Invalid request",
            "details": {"field": "email", "issue": "invalid format"}
        }
        error = ValidationError("Validation failed", status_code=400, response=response_data)
        
        assert error.response == response_data
        assert error.response["error"] == "Invalid request"
        assert "details" in error.response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
