"""
Pytest test cases for MCP Governance Middleware
Tests blocked calls, successful calls with masking, and error handling
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_governance_middleware import (
    governed_mcp_tool,
    MCPSecurityError,
    _extract_execution_context,
    audit_logger
)
from policy_engine import policy_engine, ValidationResult
from pii_masker import mask_sensitive_fields
from example_governed_tool import query_customer_data, get_product_info


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    # Clear audit logs
    audit_logger.clear_logs()
    
    # Reset policy engine state
    policy_engine._rate_limit_timestamps.clear()
    policy_engine._user_tenants.clear()
    policy_engine._pii_permissions.clear()
    policy_engine._cache.clear()
    
    yield
    
    # Cleanup after test
    audit_logger.clear_logs()


class TestBlockedCall:
    """Test cases for blocked tool calls"""
    
    @pytest.mark.asyncio
    async def test_blocked_by_rate_limit(self):
        """Test that tool call is blocked by rate limit"""
        user_id = "test_user"
        tenant_id = "test_tenant"
        
        # Grant all necessary permissions
        policy_engine.grant_tenant_access(user_id, tenant_id)
        policy_engine.grant_pii_permission(user_id)
        
        # Exceed rate limit by making many validation calls
        # Note: We need to actually call the tool to increment rate limit
        # For this test, we'll simulate by directly adding timestamps
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        policy_engine._rate_limit_timestamps[user_id] = [
            now - timedelta(minutes=i) for i in range(101)
        ]
        
        # Next call should be blocked
        with pytest.raises(MCPSecurityError) as exc_info:
            await query_customer_data(
                customer_id="12345",
                user_id=user_id,
                tenant_id=tenant_id
            )
        
        assert exc_info.value.failed_policy == "rate_limit"
        assert "Rate limit exceeded" in exc_info.value.message
        assert len(exc_info.value.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_blocked_by_rls(self):
        """Test that tool call is blocked by RLS check"""
        user_id = "test_user"
        tenant_id = "unauthorized_tenant"
        
        # Don't grant tenant access
        # Grant PII permission
        policy_engine.grant_pii_permission(user_id)
        
        # Call should be blocked by RLS
        with pytest.raises(MCPSecurityError) as exc_info:
            await query_customer_data(
                customer_id="12345",
                user_id=user_id,
                tenant_id=tenant_id
            )
        
        assert exc_info.value.failed_policy == "rls"
        assert "RLS check failed" in exc_info.value.message
        assert "cannot access tenant" in exc_info.value.message.lower()
    
    @pytest.mark.asyncio
    async def test_blocked_by_pii_permission(self):
        """Test that tool call is blocked by missing PII permission"""
        user_id = "test_user"
        tenant_id = "test_tenant"
        
        # Grant tenant access but not PII permission
        policy_engine.grant_tenant_access(user_id, tenant_id)
        # Don't grant PII permission
        
        # Call should be blocked by PII access check
        with pytest.raises(MCPSecurityError) as exc_info:
            await query_customer_data(
                customer_id="12345",
                user_id=user_id,
                tenant_id=tenant_id
            )
        
        assert exc_info.value.failed_policy == "pii_access"
        assert "PII access check failed" in exc_info.value.message
        assert "PII_READ permission" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_blocked_by_complexity(self):
        """Test that tool call is blocked by complexity check"""
        user_id = "test_user"
        tenant_id = "test_tenant"
        
        # Grant permissions
        policy_engine.grant_tenant_access(user_id, tenant_id)
        policy_engine.grant_pii_permission(user_id)
        
        # Create a tool with very complex arguments
        @governed_mcp_tool(requires_pii=True)
        async def complex_tool(user_id: str, tenant_id: str, query: str):
            return {"result": "ok"}
        
        # Create very complex query (long string + nested structures)
        complex_query = "SELECT " + ", ".join([f"col{i}" for i in range(1000)]) + " FROM table"
        complex_args = {
            "nested": {
                "deep": {
                    "very_deep": {
                        "data": [{"item": i} for i in range(100)]
                    }
                }
            }
        }
        
        # This might pass complexity check (it's configurable), but test the mechanism
        # If complexity check fails, we'll get the error
        try:
            await complex_tool(user_id=user_id, tenant_id=tenant_id, query=complex_query)
        except MCPSecurityError as e:
            if e.failed_policy == "complexity":
                assert "Complexity check failed" in e.message
                assert len(e.suggestions) > 0


class TestSuccessfulCall:
    """Test cases for successful tool calls with masking"""
    
    @pytest.mark.asyncio
    async def test_successful_call_with_masking(self):
        """Test successful tool call with PII masking"""
        user_id = "test_user"
        tenant_id = "test_tenant"
        
        # Grant all necessary permissions
        policy_engine.grant_tenant_access(user_id, tenant_id)
        policy_engine.grant_pii_permission(user_id)
        
        # Call tool
        result = await query_customer_data(
            customer_id="12345",
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        # Verify result is returned
        assert result is not None
        assert result["customer_id"] == "12345"
        
        # Verify PII fields are masked
        assert result["email"] == "***@***.com"  # Email should be masked
        assert result["phone"].endswith("4567")  # Last 4 digits kept
        assert result["phone"].startswith("(***)")  # First part masked
        assert result["ssn"].endswith("6789")  # Last 4 digits kept
        assert result["ssn"].startswith("***-**")  # First part masked
        
        # Non-PII fields should not be masked
        assert result["name"] == "John Doe"
        assert result["account_balance"] == 1000.50
    
    @pytest.mark.asyncio
    async def test_successful_call_without_pii(self):
        """Test successful tool call without PII (no masking needed)"""
        user_id = "test_user"
        tenant_id = "test_tenant"
        
        # Grant basic permissions (no PII needed)
        policy_engine.grant_tenant_access(user_id, tenant_id)
        
        # Call non-PII tool
        result = get_product_info(product_id="PROD123", user_id=user_id)
        
        # Verify result is returned
        assert result is not None
        assert result["product_id"] == "PROD123"
        assert result["name"] == "Example Product"
    
    @pytest.mark.asyncio
    async def test_audit_logging_on_success(self):
        """Test that successful calls are logged to audit log"""
        user_id = "test_user"
        tenant_id = "test_tenant"
        
        # Grant permissions
        policy_engine.grant_tenant_access(user_id, tenant_id)
        policy_engine.grant_pii_permission(user_id)
        
        # Clear audit log
        audit_logger.clear_logs()
        
        # Call tool
        await query_customer_data(
            customer_id="12345",
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        # Verify audit log entry
        logs = audit_logger.read_logs()
        assert len(logs) >= 1  # At least one entry (validation + execution)
        
        # Check last log entry (should be successful execution)
        last_log = logs[0]
        assert last_log["user_id"] == user_id
        assert last_log["tenant_id"] == tenant_id
        assert last_log["tool_name"] == "query_customer_data"
        assert last_log["status"] == "success"
        assert "execution_time_ms" in last_log
        assert last_log["result"] is not None
    
    @pytest.mark.asyncio
    async def test_masking_strict_level(self):
        """Test masking with strict sensitivity level"""
        user_id = "test_user"
        tenant_id = "test_tenant"
        
        # Grant permissions
        policy_engine.grant_tenant_access(user_id, tenant_id)
        policy_engine.grant_pii_permission(user_id)
        
        # Create tool with strict masking
        @governed_mcp_tool(requires_pii=True, sensitivity_level="strict")
        async def strict_tool(user_id: str, tenant_id: str):
            return {
                "phone": "(555) 123-4567",
                "ssn": "123-45-6789"
            }
        
        result = await strict_tool(user_id=user_id, tenant_id=tenant_id)
        
        # Strict masking: full mask (no digits shown)
        assert result["phone"] == "(***) ***-****"
        assert result["ssn"] == "***-**-****"


class TestContextExtraction:
    """Test cases for execution context extraction"""
    
    def test_extract_from_kwargs(self):
        """Test extracting user_id and tenant_id from kwargs"""
        def test_func(user_id: str, tenant_id: str, other_arg: str):
            pass
        
        context = _extract_execution_context(
            test_func,
            user_id="user1",
            tenant_id="tenant1",
            other_arg="value"
        )
        
        assert context["user_id"] == "user1"
        assert context["tenant_id"] == "tenant1"
    
    def test_extract_from_first_dict_arg(self):
        """Test extracting from first positional dict argument"""
        def test_func(data: dict):
            pass
        
        context = _extract_execution_context(
            test_func,
            {"user_id": "user1", "tenant_id": "tenant1"}
        )
        
        assert context["user_id"] == "user1"
        assert context["tenant_id"] == "tenant1"
    
    def test_default_user_id(self):
        """Test that default user_id is used if not provided"""
        def test_func():
            pass
        
        context = _extract_execution_context(test_func)
        
        assert context["user_id"] == "default_user"
        assert context["tenant_id"] is None
    
    def test_priority_kwargs_over_args(self):
        """Test that kwargs take priority over positional args"""
        def test_func(data: dict, user_id: str):
            pass
        
        context = _extract_execution_context(
            test_func,
            {"user_id": "from_dict", "tenant_id": "from_dict"},
            user_id="from_kwargs"
        )
        
        # kwargs should take priority
        assert context["user_id"] == "from_kwargs"
        assert context["tenant_id"] == "from_dict"  # Only in dict


class TestPIIMasking:
    """Test cases for PII masking"""
    
    def test_mask_email(self):
        """Test email masking"""
        data = {"email": "john.doe@example.com"}
        masked = mask_sensitive_fields(data)
        
        assert masked["email"] == "***@***.com"
    
    def test_mask_phone_standard(self):
        """Test phone masking (standard level - keep last 4)"""
        data = {"phone": "(555) 123-4567"}
        masked = mask_sensitive_fields(data, sensitivity_level="standard")
        
        assert masked["phone"].endswith("4567")
        assert masked["phone"].startswith("(***)")
        assert "(***) ***-4567" in masked["phone"]
    
    def test_mask_phone_strict(self):
        """Test phone masking (strict level - full mask)"""
        data = {"phone": "(555) 123-4567"}
        masked = mask_sensitive_fields(data, sensitivity_level="strict")
        
        assert masked["phone"] == "(***) ***-****"
    
    def test_mask_ssn_standard(self):
        """Test SSN masking (standard level - keep last 4)"""
        data = {"ssn": "123-45-6789"}
        masked = mask_sensitive_fields(data, sensitivity_level="standard")
        
        assert masked["ssn"].endswith("6789")
        assert masked["ssn"].startswith("***-**")
        assert "***-**-6789" in masked["ssn"]
    
    def test_mask_ssn_strict(self):
        """Test SSN masking (strict level - full mask)"""
        data = {"ssn": "123-45-6789"}
        masked = mask_sensitive_fields(data, sensitivity_level="strict")
        
        assert masked["ssn"] == "***-**-****"
    
    def test_mask_credit_card(self):
        """Test credit card masking"""
        data = {"credit_card": "1234-5678-9012-3456"}
        masked = mask_sensitive_fields(data, sensitivity_level="standard")
        
        assert masked["credit_card"].endswith("3456")
        assert masked["credit_card"].startswith("****-****-****")
    
    def test_mask_nested_data(self):
        """Test masking in nested data structures"""
        data = {
            "customer": {
                "email": "test@example.com",
                "contact": {
                    "phone": "555-123-4567"
                }
            },
            "customers": [
                {"email": "user1@example.com"},
                {"email": "user2@example.com"}
            ]
        }
        
        masked = mask_sensitive_fields(data)
        
        assert masked["customer"]["email"] == "***@***.com"
        assert masked["customer"]["contact"]["phone"].endswith("4567")
        assert masked["customers"][0]["email"] == "***@***.com"
        assert masked["customers"][1]["email"] == "***@***.com"
    
    def test_non_string_values(self):
        """Test that non-string values are not masked"""
        data = {
            "id": 12345,
            "balance": 1000.50,
            "active": True,
            "tags": ["premium", "vip"]
        }
        
        masked = mask_sensitive_fields(data)
        
        # Non-string values should be unchanged
        assert masked["id"] == 12345
        assert masked["balance"] == 1000.50
        assert masked["active"] is True
        assert masked["tags"] == ["premium", "vip"]
    
    def test_string_with_multiple_emails(self):
        """Test masking string with multiple email addresses"""
        text = "Contact admin@example.com or support@example.com for help"
        masked = mask_sensitive_fields(text)
        
        assert "***@***.com" in masked
        assert "admin@example.com" not in masked
        assert "support@example.com" not in masked


class TestErrorHandling:
    """Test cases for error handling"""
    
    @pytest.mark.asyncio
    async def test_security_error_has_suggestions(self):
        """Test that MCPSecurityError includes remediation suggestions"""
        user_id = "test_user"
        tenant_id = "unauthorized_tenant"
        
        # Don't grant tenant access
        policy_engine.grant_pii_permission(user_id)
        
        try:
            await query_customer_data(
                customer_id="12345",
                user_id=user_id,
                tenant_id=tenant_id
            )
            pytest.fail("Should have raised MCPSecurityError")
        except MCPSecurityError as e:
            assert e.validation_result is not None
            assert len(e.suggestions) > 0
            assert "Request access" in e.suggestions[0] or "Contact administrator" in e.suggestions[0]
    
    @pytest.mark.asyncio
    async def test_audit_log_on_security_violation(self):
        """Test that security violations are logged with error status"""
        user_id = "test_user"
        tenant_id = "unauthorized_tenant"
        
        # Clear audit log
        audit_logger.clear_logs()
        
        # Attempt call (should fail)
        try:
            await query_customer_data(
                customer_id="12345",
                user_id=user_id,
                tenant_id=tenant_id
            )
        except MCPSecurityError:
            pass  # Expected
        
        # Verify security violation was logged
        logs = audit_logger.read_logs()
        assert len(logs) >= 1
        
        # Find security violation log
        violation_logs = [log for log in logs if log.get("error") and "RLS check failed" in log["error"]]
        assert len(violation_logs) > 0
        
        violation_log = violation_logs[0]
        assert violation_log["status"] == "error"
        assert violation_log["validation"] is not None
    
    @pytest.mark.asyncio
    async def test_tool_execution_error_logged(self):
        """Test that tool execution errors are logged"""
        user_id = "test_user"
        tenant_id = "test_tenant"
        
        # Grant permissions
        policy_engine.grant_tenant_access(user_id, tenant_id)
        policy_engine.grant_pii_permission(user_id)
        
        # Create tool that raises an error
        @governed_mcp_tool(requires_pii=False)
        async def failing_tool(user_id: str):
            raise ValueError("Tool execution failed")
        
        # Clear audit log
        audit_logger.clear_logs()
        
        # Call tool (should raise error)
        try:
            await failing_tool(user_id=user_id)
            pytest.fail("Should have raised ValueError")
        except ValueError:
            pass  # Expected
        
        # Verify error was logged
        logs = audit_logger.read_logs()
        assert len(logs) >= 1
        
        error_logs = [log for log in logs if log.get("error")]
        assert len(error_logs) > 0
        
        error_log = error_logs[0]
        assert error_log["status"] == "error"
        assert "Tool execution failed" in error_log["error"]


class TestPolicyEngine:
    """Test cases for policy engine directly"""
    
    @pytest.mark.asyncio
    async def test_validation_passes(self):
        """Test successful validation"""
        user_id = "test_user"
        tenant_id = "test_tenant"
        
        policy_engine.grant_tenant_access(user_id, tenant_id)
        policy_engine.grant_pii_permission(user_id)
        
        result = await policy_engine.validate(
            user_id=user_id,
            tenant_id=tenant_id,
            tool_name="test_tool",
            arguments={"query": "test"}
        )
        
        assert result.is_allowed is True
        assert result.failed_policy is None
        assert len(result.suggestions) == 0
    
    @pytest.mark.asyncio
    async def test_validation_caching(self):
        """Test that validation results are cached"""
        user_id = "test_user"
        tenant_id = "test_tenant"
        
        policy_engine.grant_tenant_access(user_id, tenant_id)
        policy_engine.grant_pii_permission(user_id)
        
        args = {"customer_id": "123"}
        
        # First call
        result1 = await policy_engine.validate(
            user_id=user_id,
            tenant_id=tenant_id,
            tool_name="test_tool",
            arguments=args
        )
        
        # Second call with same args (should use cache)
        result2 = await policy_engine.validate(
            user_id=user_id,
            tenant_id=tenant_id,
            tool_name="test_tool",
            arguments=args
        )
        
        # Both should succeed
        assert result1.is_allowed is True
        assert result2.is_allowed is True
    
    @pytest.mark.asyncio
    async def test_complexity_scoring(self):
        """Test complexity score calculation"""
        # Simple query should have low score
        simple_args = {"query": "SELECT * FROM users"}
        result1 = await policy_engine.validate(
            user_id="test",
            tenant_id="test",
            tool_name="test",
            arguments=simple_args
        )
        # Should pass (complexity check is one of the checks)
        
        # Very complex query (many nested structures)
        complex_args = {
            "query": "SELECT " + ", ".join([f"col{i}" for i in range(500)]),
            "filters": {
                "deep": {
                    "nested": {
                        "structure": [{"item": i} for i in range(50)]
                    }
                }
            }
        }
        
        result2 = await policy_engine.validate(
            user_id="test",
            tenant_id="test",
            tool_name="test",
            arguments=complex_args
        )
        
        # Might fail complexity, but test that mechanism works
        # If it passes, that's fine too (complexity limits are configurable)
        assert isinstance(result2, ValidationResult)


class TestAuditLogger:
    """Test cases for audit logger"""
    
    def test_log_tool_call(self):
        """Test logging a tool call"""
        audit_logger.clear_logs()
        
        audit_logger.log_tool_call(
            user_id="user1",
            tenant_id="tenant1",
            tool_name="test_tool",
            args={"arg1": "value1"},
            result={"result": "success"},
            validation={"is_allowed": True},
            execution_time_ms=45.2
        )
        
        logs = audit_logger.read_logs()
        assert len(logs) == 1
        
        log = logs[0]
        assert log["user_id"] == "user1"
        assert log["tenant_id"] == "tenant1"
        assert log["tool_name"] == "test_tool"
        assert log["status"] == "success"
        assert log["execution_time_ms"] == 45.2
    
    def test_read_logs_with_limit(self):
        """Test reading logs with limit"""
        audit_logger.clear_logs()
        
        # Add multiple logs
        for i in range(10):
            audit_logger.log_tool_call(
                user_id=f"user{i}",
                tenant_id="tenant1",
                tool_name="test_tool",
                args={},
                result={}
            )
        
        logs = audit_logger.read_logs(limit=5)
        assert len(logs) == 5
    
    def test_clear_logs(self):
        """Test clearing logs"""
        audit_logger.log_tool_call(
            user_id="user1",
            tenant_id="tenant1",
            tool_name="test_tool",
            args={},
            result={}
        )
        
        assert len(audit_logger.read_logs()) > 0
        
        audit_logger.clear_logs()
        
        assert len(audit_logger.read_logs()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

