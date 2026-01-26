"""
Example MCP Tool using Governance Middleware
Demonstrates how to use @governed_mcp_tool decorator
"""

from typing import Dict, Any, Optional
from mcp_governance_middleware import governed_mcp_tool, MCPSecurityError

# Mock MCP decorator for demonstration
# In real usage, this would be: from fastmcp import FastMCP; mcp = FastMCP("...")
class MockMCP:
    """Mock MCP for demonstration"""
    @staticmethod
    def tool():
        """Mock tool decorator"""
        def decorator(func):
            return func
        return decorator

mcp = MockMCP()


@governed_mcp_tool(mcp.tool(), requires_pii=True, sensitivity_level="standard")
async def query_customer_data(
    customer_id: str,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query customer data - Example tool with governance middleware.
    
    This tool is automatically wrapped with:
    - Policy validation (rate limits, RLS, complexity, PII access)
    - PII masking in results
    - Audit logging
    
    Args:
        customer_id: Customer ID to query
        user_id: User ID (extracted from context if not provided)
        tenant_id: Tenant ID (extracted from context if not provided)
    
    Returns:
        Customer data (PII fields will be masked)
    
    Raises:
        MCPSecurityError: If policy validation fails
    """
    # Mock customer data (in real implementation, this would query a database)
    mock_customer_data = {
        "customer_id": customer_id,
        "name": "John Doe",
        "email": "john.doe@example.com",  # Will be masked
        "phone": "(555) 123-4567",  # Will be masked (last 4 digits kept)
        "ssn": "123-45-6789",  # Will be masked (last 4 digits kept)
        "address": "123 Main St, Anytown, USA",
        "account_balance": 1000.50
    }
    
    return mock_customer_data


# Example of sync function with governance
@governed_mcp_tool(mcp.tool(), requires_pii=False, sensitivity_level="standard")
def get_product_info(product_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get product information - Example sync tool with governance.
    
    Args:
        product_id: Product ID
        user_id: User ID (extracted from context)
    
    Returns:
        Product information
    """
    return {
        "product_id": product_id,
        "name": "Example Product",
        "price": 99.99,
        "description": "This is an example product"
    }


# Example usage (for testing)
if __name__ == "__main__":
    import asyncio
    
    async def test_example():
        """Test the example tool"""
        try:
            # This will fail if user doesn't have PII permission
            result = await query_customer_data(
                customer_id="12345",
                user_id="test_user",
                tenant_id="test_tenant"
            )
            print("Result:", result)
            print("Note: Email, phone, and SSN should be masked")
        except MCPSecurityError as e:
            print(f"Security Error: {e.message}")
            print(f"Suggestions: {e.suggestions}")
    
    # Run test
    asyncio.run(test_example())

