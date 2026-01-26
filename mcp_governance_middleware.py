"""
Governance Middleware for MCP Tools
Wraps MCP tool executions with security policies, PII masking, and audit logging
"""

import functools
import time
import asyncio
from typing import Callable, Any, Dict, Optional
import inspect

from policy_engine import policy_engine, ValidationResult
from pii_masker import mask_sensitive_fields
from mock_audit_logger import AuditLogger

# Global audit logger instance
audit_logger = AuditLogger()


class MCPSecurityError(Exception):
    """Security violation error raised when policy validation fails"""
    
    def __init__(self, message: str, validation_result: ValidationResult):
        """
        Initialize security error
        
        Args:
            message: Error message
            validation_result: Validation result that failed
        """
        self.message = message
        self.validation_result = validation_result
        self.failed_policy = validation_result.failed_policy
        self.suggestions = validation_result.suggestions
        super().__init__(self.message)


def _extract_execution_context(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Extract user_id and tenant_id from execution context.
    
    This function looks for user_id and tenant_id in:
    1. Function keyword arguments
    2. First positional argument if it's a dict with these keys
    3. MCP context (if available)
    
    Args:
        func: The function being called
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Dict with user_id, tenant_id, and other context info
    """
    context = {
        "user_id": None,
        "tenant_id": None
    }
    
    # Check keyword arguments first
    if "user_id" in kwargs:
        context["user_id"] = kwargs["user_id"]
    if "tenant_id" in kwargs:
        context["tenant_id"] = kwargs["tenant_id"]
    
    # Check first positional argument if it's a dict
    if args and isinstance(args[0], dict):
        first_arg = args[0]
        if "user_id" in first_arg:
            context["user_id"] = first_arg["user_id"]
        if "tenant_id" in first_arg:
            context["tenant_id"] = first_arg["tenant_id"]
    
    # Try to get from MCP context (if available)
    # This would typically come from MCP request metadata
    # For now, we'll use a default or require it to be passed
    
    # If still not found, use defaults (for testing/demo)
    if not context["user_id"]:
        context["user_id"] = "default_user"
    
    return context


def governed_mcp_tool(
    mcp_tool_decorator: Optional[Callable] = None,
    requires_pii: bool = False,
    sensitivity_level: str = "standard"
):
    """
    Decorator that wraps MCP tool execution with governance policies.
    
    This decorator should be used in combination with @mcp.tool() like this:
    
        @governed_mcp_tool(mcp.tool())
        async def my_tool(...):
            ...
    
    Or as a wrapper around an existing tool:
    
        @governed_mcp_tool(requires_pii=True)
        @mcp.tool()
        async def my_tool(...):
            ...
    
    The decorator:
    1. Extracts user_id and tenant_id from execution context
    2. Validates against policies BEFORE tool execution
    3. Logs the attempt (audit trail)
    4. Executes tool only if validation passes
    5. Applies PII masking to results
    6. Logs the result
    
    Args:
        mcp_tool_decorator: The MCP tool decorator (from FastMCP)
        requires_pii: Whether this tool requires PII_READ permission
        sensitivity_level: PII masking sensitivity level ("standard" or "strict")
    
    Returns:
        Decorated function with governance middleware
    """
    def decorator(func: Callable) -> Callable:
        # Check if function is async
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await _execute_with_governance(
                    func, args, kwargs, requires_pii, sensitivity_level, is_async=True
                )
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # For sync functions, we need to handle async validation
                return _execute_with_governance_sync(
                    func, args, kwargs, requires_pii, sensitivity_level
                )
            return sync_wrapper
        
        # If mcp_tool_decorator is provided, wrap the function with it
        if mcp_tool_decorator:
            if is_async:
                return mcp_tool_decorator(async_wrapper)
            else:
                return mcp_tool_decorator(sync_wrapper)
        
        if is_async:
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


async def _execute_with_governance(
    func: Callable,
    args: tuple,
    kwargs: Dict[str, Any],
    requires_pii: bool,
    sensitivity_level: str,
    is_async: bool = True
) -> Any:
    """
    Execute function with governance middleware (async version)
    
    Args:
        func: Function to execute
        args: Positional arguments
        kwargs: Keyword arguments
        requires_pii: Whether function requires PII permission
        sensitivity_level: PII masking sensitivity level
        is_async: Whether function is async
    
    Returns:
        Function result (masked if contains PII)
    
    Raises:
        MCPSecurityError: If validation fails
    """
    start_time = time.time()
    
    # Extract execution context
    context = _extract_execution_context(func, *args, **kwargs)
    user_id = context["user_id"]
    tenant_id = context["tenant_id"]
    
    # Get tool name from function
    tool_name = func.__name__
    
    # Prepare arguments for validation (remove sensitive data if needed)
    validation_args = {**kwargs}
    if args:
        # Convert positional args to dict if possible
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())
        for i, arg in enumerate(args):
            if i < len(param_names):
                validation_args[param_names[i]] = arg
    
    # Validate against policies BEFORE execution
    validation_result = await policy_engine.validate(
        user_id=user_id,
        tenant_id=tenant_id,
        tool_name=tool_name,
        arguments=validation_args
    )
    
    # Log the attempt (before execution)
    audit_logger.log_tool_call(
        user_id=user_id,
        tenant_id=tenant_id,
        tool_name=tool_name,
        args=validation_args,
        validation=validation_result.__dict__,
        execution_time_ms=None,  # Not executed yet
        error=None
    )
    
    # Check if validation passed
    if not validation_result.is_allowed:
        error_message = f"Security policy violation: {validation_result.reason}"
        
        # Log security violation with HIGH severity
        audit_logger.log_tool_call(
            user_id=user_id,
            tenant_id=tenant_id,
            tool_name=tool_name,
            args=validation_args,
            validation=validation_result.__dict__,
            execution_time_ms=None,
            error=error_message
        )
        
        # Raise security error with remediation suggestions
        raise MCPSecurityError(error_message, validation_result)
    
    # Execute tool
    try:
        if is_async:
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Apply PII masking to results
        masked_result = mask_sensitive_fields(result, sensitivity_level=sensitivity_level)
        
        # Log successful execution
        audit_logger.log_tool_call(
            user_id=user_id,
            tenant_id=tenant_id,
            tool_name=tool_name,
            args=validation_args,
            result=masked_result,  # Log masked result
            validation=validation_result.__dict__,
            execution_time_ms=execution_time_ms,
            error=None
        )
        
        # Return masked result
        return masked_result
        
    except MCPSecurityError:
        # Re-raise security errors
        raise
    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        error_message = str(e)
        
        # Log error
        audit_logger.log_tool_call(
            user_id=user_id,
            tenant_id=tenant_id,
            tool_name=tool_name,
            args=validation_args,
            validation=validation_result.__dict__,
            execution_time_ms=execution_time_ms,
            error=error_message
        )
        
        # Re-raise the exception
        raise


def _execute_with_governance_sync(
    func: Callable,
    args: tuple,
    kwargs: Dict[str, Any],
    requires_pii: bool,
    sensitivity_level: str
) -> Any:
    """
    Execute function with governance middleware (sync version)
    
    For sync functions, we run async validation in an event loop
    
    Args:
        func: Function to execute
        args: Positional arguments
        kwargs: Keyword arguments
        requires_pii: Whether function requires PII permission
        sensitivity_level: PII masking sensitivity level
    
    Returns:
        Function result (masked if contains PII)
    
    Raises:
        MCPSecurityError: If validation fails
    """
    # Create event loop for async validation
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Run async governance wrapper
    return loop.run_until_complete(
        _execute_with_governance(
            func, args, kwargs, requires_pii, sensitivity_level, is_async=False
        )
    )


# Convenience function for creating governed tools without decorator chaining
def create_governed_tool(
    func: Callable,
    mcp_tool_decorator: Optional[Callable] = None,
    requires_pii: bool = False,
    sensitivity_level: str = "standard"
) -> Callable:
    """
    Create a governed MCP tool from a function
    
    Args:
        func: Function to wrap
        mcp_tool_decorator: MCP tool decorator (from FastMCP)
        requires_pii: Whether tool requires PII permission
        sensitivity_level: PII masking sensitivity level
    
    Returns:
        Governed tool function
    """
    # Apply governance decorator
    governed_func = governed_mcp_tool(
        mcp_tool_decorator=mcp_tool_decorator,
        requires_pii=requires_pii,
        sensitivity_level=sensitivity_level
    )(func)
    
    return governed_func

