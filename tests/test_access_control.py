"""
Unit tests for access control resource-level permissions

=============================================================================
POSTGRESQL CONFIGURATION DETAILS
=============================================================================

The PostgreSQL database connector supports two configuration methods:

1. ENVIRONMENT VARIABLES:
   ----------------------
   Set these environment variables for default database connection:
   
   DB_HOST       - Database hostname (e.g., 'localhost', 'db.example.com')
   DB_PORT       - Database port (default: 5432)
   DB_USER       - Database username (e.g., 'postgres')
   DB_PASSWORD   - Database password
   DB_NAME       - Database name (e.g., 'mydb', 'analytics')

   Example .env file:
   ------------------
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=your-password
   DB_NAME=your-database

2. CONNECTION STRING:
   ------------------
   Use a PostgreSQL connection string in the format:
   
   postgresql://[user[:password]@][host][:port][/database]
   
   Examples:
   ---------
   postgresql://user:pass@localhost:5432/mydb
   postgresql://postgres:secret@db.example.com:5432/analytics
   postgresql://user@localhost/dbname  (no password)
   postgresql://user:pass@localhost/dbname  (default port 5432)

3. INDIVIDUAL PARAMETERS:
   ----------------------
   Pass parameters directly to DatabaseConnector:
   
   from ai_agent_connector.app.db.connector import DatabaseConnector
   
   connector = DatabaseConnector(
       host='localhost',
       port=5432,
       user='postgres',
       password='your-password',
       database='mydb'
   )

4. API CONFIGURATION:
   ------------------
   When registering an agent via API, use either format:
   
   Option A - Individual parameters:
   {
     "database": {
       "host": "localhost",
       "port": 5432,
       "user": "postgres",
       "password": "password",
       "database": "testdb"
     }
   }
   
   Option B - Connection string:
   {
     "database": {
       "connection_string": "postgresql://user:pass@host:port/db",
       "type": "postgresql"
     }
   }

REQUIRED PARAMETERS:
-------------------
- host (or DB_HOST env var)
- user (or DB_USER env var)
- database (or DB_NAME env var)
- password (or DB_PASSWORD env var) - optional if using trust auth
- port (or DB_PORT env var) - defaults to 5432 if not provided

CONNECTION PRIORITY:
-------------------
1. Explicit parameters passed to DatabaseConnector()
2. Environment variables (DB_HOST, DB_USER, etc.)
3. Connection string (if provided, overrides individual params)

IMPLEMENTATION LOCATION:
------------------------
File: ai_agent_connector/app/db/connector.py
Class: DatabaseConnector

=============================================================================
"""

from ai_agent_connector.app.permissions.access_control import AccessControl, Permission


class TestAccessControl:
    """Verify resource permission helpers"""
    
    def setup_method(self):
        self.access_control = AccessControl()
    
    def test_set_and_get_resource_permissions(self):
        self.access_control.set_resource_permissions(
            agent_id='agent-1',
            resource_id='public.orders',
            permissions=[Permission.READ, Permission.WRITE],
            resource_type='table'
        )
        
        resources = self.access_control.get_resource_permissions('agent-1')
        assert 'public.orders' in resources
        assert Permission.READ in resources['public.orders']['permissions']
        assert Permission.WRITE in resources['public.orders']['permissions']
    
    def test_has_resource_permission(self):
        self.access_control.set_resource_permissions(
            'agent-1',
            'dataset.sales',
            [Permission.READ],
            resource_type='dataset'
        )
        
        assert self.access_control.has_resource_permission('agent-1', 'dataset.sales', Permission.READ)
        assert not self.access_control.has_resource_permission('agent-1', 'dataset.sales', Permission.WRITE)
    
    def test_revoke_resource(self):
        self.access_control.set_resource_permissions('agent-1', 'table1', [Permission.READ])
        removed = self.access_control.revoke_resource('agent-1', 'table1')
        assert removed is True
        assert self.access_control.get_resource_permissions('agent-1') == {}
    
    def test_revoke_all_agent_permissions(self):
        """Test revoking all permissions for an agent"""
        # Set up permissions
        self.access_control.grant_permission('agent-1', Permission.READ)
        self.access_control.grant_permission('agent-1', Permission.WRITE)
        self.access_control.set_resource_permissions('agent-1', 'table1', [Permission.READ])
        self.access_control.set_resource_permissions('agent-1', 'table2', [Permission.WRITE])
        
        # Verify permissions exist
        assert len(self.access_control.get_permissions('agent-1')) == 2
        assert len(self.access_control.get_resource_permissions('agent-1')) == 2
        
        # Revoke all permissions
        revoked = self.access_control.revoke_all_agent_permissions('agent-1')
        assert revoked is True
        
        # Verify all permissions are removed
        assert len(self.access_control.get_permissions('agent-1')) == 0
        assert len(self.access_control.get_resource_permissions('agent-1')) == 0
    
    def test_revoke_all_agent_permissions_no_permissions(self):
        """Test revoking all permissions for an agent with no permissions"""
        revoked = self.access_control.revoke_all_agent_permissions('agent-none')
        assert revoked is False



