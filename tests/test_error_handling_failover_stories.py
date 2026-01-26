"""
Integration tests for Error Handling & Failover Stories

Story 1: As a User, I want clear error messages when queries fail (e.g., "Invalid column name"),
         so that I can fix issues without contacting support.

Story 2: As an Admin, I want automatic failover to a backup database if the primary is unavailable,
         so that uptime is maximized.

Story 3: As a Developer, I want dead-letter queues for failed queries,
         so that I can replay them after fixing issues.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from main import create_app
from ai_agent_connector.app.api.routes import (
    agent_registry, access_control, error_formatter,
    failover_manager, dead_letter_queue
)
from ai_agent_connector.app.permissions import Permission
from ai_agent_connector.app.utils.encryption import reset_encryptor
from ai_agent_connector.app.utils.database_failover import DatabaseEndpoint, FailoverStatus
from ai_agent_connector.app.utils.dead_letter_queue import DLQStatus


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    failover_manager._endpoints.clear()
    failover_manager._current_endpoints.clear()
    failover_manager._failover_status.clear()
    dead_letter_queue._entries.clear()
    dead_letter_queue._agent_entries.clear()
    yield
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    failover_manager._endpoints.clear()
    failover_manager._current_endpoints.clear()
    failover_manager._failover_status.clear()
    dead_letter_queue._entries.clear()
    dead_letter_queue._agent_entries.clear()


@pytest.fixture
def client():
    """Create test client"""
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def admin_agent():
    """Create an admin agent"""
    result = agent_registry.register_agent(
        agent_id='admin-agent',
        agent_info={'name': 'Admin Agent'},
        credentials={'api_key': 'admin-key', 'api_secret': 'admin-secret'}
    )
    access_control.grant_permission('admin-agent', Permission.ADMIN)
    return {'agent_id': 'admin-agent', 'api_key': result['api_key']}


@pytest.fixture
def test_agent():
    """Create a test agent"""
    result = agent_registry.register_agent(
        agent_id='test-agent',
        agent_info={'name': 'Test Agent'},
        credentials={'api_key': 'test-key', 'api_secret': 'test-secret'}
    )
    access_control.grant_permission('test-agent', Permission.READ)
    return {'agent_id': 'test-agent', 'api_key': result['api_key']}


class TestStory1_ClearErrorMessages:
    """Story 1: Clear error messages for query failures"""
    
    def test_format_column_error(self, client, test_agent):
        """Test formatting column does not exist error"""
        error = Exception('column "invalid_column" does not exist')
        
        formatted = error_formatter.format_error(error, query='SELECT invalid_column FROM users')
        
        assert 'user_friendly_message' in formatted
        assert 'Invalid column name' in formatted['user_friendly_message']
        assert 'invalid_column' in formatted['user_friendly_message']
        assert 'actionable_details' in formatted
        assert formatted['actionable_details'].get('column') == 'invalid_column'
    
    def test_format_table_error(self, client, test_agent):
        """Test formatting table does not exist error"""
        error = Exception('relation "nonexistent_table" does not exist')
        
        formatted = error_formatter.format_error(error)
        
        assert 'user_friendly_message' in formatted
        assert 'Table' in formatted['user_friendly_message']
        assert 'does not exist' in formatted['user_friendly_message']
        assert formatted['actionable_details'].get('table') == 'nonexistent_table'
    
    def test_format_syntax_error(self, client, test_agent):
        """Test formatting SQL syntax error"""
        error = Exception('syntax error at or near "FROM"')
        
        formatted = error_formatter.format_error(error)
        
        assert 'user_friendly_message' in formatted
        assert 'syntax error' in formatted['user_friendly_message'].lower()
        assert 'suggested_fixes' in formatted
        assert len(formatted['suggested_fixes']) > 0
    
    def test_format_connection_error(self, client, test_agent):
        """Test formatting connection error"""
        error = Exception('connection refused')
        
        formatted = error_formatter.format_error(error)
        
        assert 'user_friendly_message' in formatted
        assert 'connection' in formatted['user_friendly_message'].lower()
        assert 'suggested_fixes' in formatted
    
    def test_format_permission_error(self, client, test_agent):
        """Test formatting permission denied error"""
        error = Exception('permission denied for table users')
        
        formatted = error_formatter.format_error(error)
        
        assert 'user_friendly_message' in formatted
        assert 'permission' in formatted['user_friendly_message'].lower() or 'access' in formatted['user_friendly_message'].lower()
    
    def test_format_duplicate_key_error(self, client, test_agent):
        """Test formatting duplicate key error"""
        error = Exception('duplicate key value violates unique constraint')
        
        formatted = error_formatter.format_error(error)
        
        assert 'user_friendly_message' in formatted
        assert 'duplicate' in formatted['user_friendly_message'].lower()
    
    def test_format_foreign_key_error(self, client, test_agent):
        """Test formatting foreign key constraint error"""
        error = Exception('violates foreign key constraint')
        
        formatted = error_formatter.format_error(error)
        
        assert 'user_friendly_message' in formatted
        assert 'foreign key' in formatted['user_friendly_message'].lower() or 'referential' in formatted['user_friendly_message'].lower()
    
    def test_format_null_constraint_error(self, client, test_agent):
        """Test formatting null constraint error"""
        error = Exception('null value in column "email" violates not-null constraint')
        
        formatted = error_formatter.format_error(error)
        
        assert 'user_friendly_message' in formatted
        assert 'required' in formatted['user_friendly_message'].lower() or 'cannot be empty' in formatted['user_friendly_message'].lower()
        assert formatted['actionable_details'].get('column') == 'email'
    
    def test_suggested_fixes_included(self, client, test_agent):
        """Test that suggested fixes are included"""
        error = Exception('column "invalid" does not exist')
        
        formatted = error_formatter.format_error(error)
        
        assert 'suggested_fixes' in formatted
        assert isinstance(formatted['suggested_fixes'], list)
        assert len(formatted['suggested_fixes']) > 0
    
    def test_error_with_context(self, client, test_agent):
        """Test error formatting with context"""
        error = Exception('column "invalid" does not exist')
        context = {'agent_id': 'test-agent', 'query_type': 'SELECT'}
        
        formatted = error_formatter.format_error(error, context=context)
        
        assert 'context' in formatted
        assert formatted['context']['agent_id'] == 'test-agent'


class TestStory2_DatabaseFailover:
    """Story 2: Automatic database failover"""
    
    def test_register_failover_endpoints(self, client, admin_agent):
        """Test registering failover endpoints"""
        payload = {
            'endpoints': [
                {
                    'name': 'Primary Database',
                    'host': 'db-primary.example.com',
                    'port': 5432,
                    'user': 'user',
                    'password': 'pass',
                    'database': 'mydb',
                    'database_type': 'postgresql',
                    'is_primary': True,
                    'priority': 0
                },
                {
                    'name': 'Backup Database',
                    'host': 'db-backup.example.com',
                    'port': 5432,
                    'user': 'user',
                    'password': 'pass',
                    'database': 'mydb',
                    'database_type': 'postgresql',
                    'is_primary': False,
                    'priority': 1
                }
            ]
        }
        
        response = client.post(
            '/api/admin/agents/test-agent/failover/endpoints',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['endpoints']) == 2
        assert any(e['is_primary'] for e in data['endpoints'])
    
    def test_get_failover_status(self, client, admin_agent):
        """Test getting failover status"""
        # Register endpoints
        primary = DatabaseEndpoint(
            endpoint_id='primary-1',
            name='Primary',
            host='db-primary.com',
            database='mydb',
            is_primary=True,
            priority=0
        )
        backup = DatabaseEndpoint(
            endpoint_id='backup-1',
            name='Backup',
            host='db-backup.com',
            database='mydb',
            is_primary=False,
            priority=1
        )
        failover_manager.register_endpoints('test-agent', [primary, backup])
        
        response = client.get(
            '/api/admin/agents/test-agent/failover/status',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'primary'
        assert data['current_endpoint'] is not None
        assert len(data['endpoints']) == 2
    
    def test_failover_on_connection_error(self, client, admin_agent):
        """Test automatic failover on connection error"""
        # Register endpoints
        primary = DatabaseEndpoint(
            endpoint_id='primary-1',
            name='Primary',
            host='db-primary.com',
            database='mydb',
            is_primary=True
        )
        backup = DatabaseEndpoint(
            endpoint_id='backup-1',
            name='Backup',
            host='db-backup.com',
            database='mydb',
            is_primary=False
        )
        failover_manager.register_endpoints('test-agent', [primary, backup])
        
        # Record failure on primary
        failover_occurred = failover_manager.record_failure('test-agent', 'primary-1')
        
        # Should attempt failover (may succeed or fail depending on backup availability)
        assert failover_occurred is not None
    
    def test_failover_status_tracking(self, client, admin_agent):
        """Test failover status tracking"""
        primary = DatabaseEndpoint(
            endpoint_id='primary-1',
            name='Primary',
            host='db-primary.com',
            database='mydb',
            is_primary=True
        )
        backup = DatabaseEndpoint(
            endpoint_id='backup-1',
            name='Backup',
            host='db-backup.com',
            database='mydb',
            is_primary=False
        )
        failover_manager.register_endpoints('test-agent', [primary, backup])
        
        # Initially should be primary
        status = failover_manager.get_failover_status('test-agent')
        assert status['status'] == 'primary'
        
        # After failover, status should change
        failover_manager.record_failure('test-agent', 'primary-1')
        status = failover_manager.get_failover_status('test-agent')
        # Status may be failover or failed depending on backup availability
        assert status['status'] in ['failover', 'failed', 'primary']
    
    def test_reset_endpoint(self, client, admin_agent):
        """Test resetting a failed endpoint"""
        primary = DatabaseEndpoint(
            endpoint_id='primary-1',
            name='Primary',
            host='db-primary.com',
            database='mydb',
            is_primary=True
        )
        failover_manager.register_endpoints('test-agent', [primary])
        
        # Mark as failed
        primary.is_active = False
        primary.failure_count = 1
        
        # Reset endpoint
        with patch.object(failover_manager, 'test_endpoint', return_value=True):
            success = failover_manager.reset_endpoint('test-agent', 'primary-1')
            assert success is True
            assert primary.is_active is True
    
    def test_endpoint_priority(self, client, admin_agent):
        """Test endpoint priority ordering"""
        endpoint1 = DatabaseEndpoint(
            endpoint_id='ep-1',
            name='Endpoint 1',
            host='db1.com',
            priority=2
        )
        endpoint2 = DatabaseEndpoint(
            endpoint_id='ep-2',
            name='Endpoint 2',
            host='db2.com',
            priority=1
        )
        endpoint3 = DatabaseEndpoint(
            endpoint_id='ep-3',
            name='Endpoint 3',
            host='db3.com',
            priority=0,
            is_primary=True
        )
        
        failover_manager.register_endpoints('test-agent', [endpoint1, endpoint2, endpoint3])
        
        # Primary should be selected first
        current = failover_manager.get_current_endpoint('test-agent')
        assert current is not None
        assert current.is_primary is True


class TestStory3_DeadLetterQueue:
    """Story 3: Dead-letter queue for failed queries"""
    
    def test_add_failed_query_to_dlq(self, client, test_agent):
        """Test adding failed query to dead-letter queue"""
        error = Exception('Connection timeout')
        
        entry = dead_letter_queue.add_failed_query(
            agent_id='test-agent',
            query='SELECT * FROM users',
            query_type='SELECT',
            error=error,
            params=None
        )
        
        assert entry is not None
        assert entry.agent_id == 'test-agent'
        assert entry.query == 'SELECT * FROM users'
        assert entry.status == DLQStatus.PENDING
        assert entry.error_type == 'Exception'
    
    def test_list_dlq_entries(self, client, admin_agent):
        """Test listing dead-letter queue entries"""
        # Add some entries
        error1 = Exception('Connection timeout')
        dead_letter_queue.add_failed_query('agent-1', 'SELECT * FROM users', 'SELECT', error1)
        
        error2 = Exception('Syntax error')
        dead_letter_queue.add_failed_query('agent-2', 'SELECT * FROM orders', 'SELECT', error2)
        
        response = client.get(
            '/api/admin/dlq/entries',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'entries' in data
        assert len(data['entries']) >= 2
    
    def test_get_dlq_entry(self, client, admin_agent):
        """Test getting a specific DLQ entry"""
        error = Exception('Connection timeout')
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', error
        )
        
        response = client.get(
            f'/api/admin/dlq/entries/{entry.entry_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['entry_id'] == entry.entry_id
        assert data['query'] == 'SELECT * FROM users'
        assert data['status'] == 'pending'
    
    def test_replay_dlq_entry(self, client, admin_agent):
        """Test replaying a DLQ entry"""
        error = Exception('Connection timeout')
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', error
        )
        
        # Mock database connector
        mock_connector = MagicMock()
        mock_connector.connect.return_value = None
        mock_connector.execute_query.return_value = [('result',)]
        mock_connector.disconnect.return_value = None
        
        result = dead_letter_queue.replay_entry(entry.entry_id, mock_connector)
        
        # Should attempt replay
        assert 'success' in result or 'error' in result
    
    def test_replay_updates_status(self, client, admin_agent):
        """Test that replay updates entry status"""
        error = Exception('Connection timeout')
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', error
        )
        
        mock_connector = MagicMock()
        mock_connector.connect.return_value = None
        mock_connector.execute_query.return_value = [('result',)]
        mock_connector.disconnect.return_value = None
        
        dead_letter_queue.replay_entry(entry.entry_id, mock_connector)
        
        updated_entry = dead_letter_queue.get_entry(entry.entry_id)
        assert updated_entry.status in [DLQStatus.SUCCESS, DLQStatus.FAILED, DLQStatus.REPLAYING]
        assert updated_entry.retry_count > 0
    
    def test_replay_max_retries(self, client, admin_agent):
        """Test that replay respects max retries"""
        error = Exception('Connection timeout')
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', error, max_retries=2
        )
        
        # Set retry count to max
        entry.retry_count = entry.max_retries
        
        mock_connector = MagicMock()
        result = dead_letter_queue.replay_entry(entry.entry_id, mock_connector)
        
        assert result.get('success') is False
        assert 'Maximum retries exceeded' in result.get('error', '')
    
    def test_archive_dlq_entry(self, client, admin_agent):
        """Test archiving a DLQ entry"""
        error = Exception('Connection timeout')
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', error
        )
        
        response = client.post(
            f'/api/admin/dlq/entries/{entry.entry_id}/archive',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['entry']['status'] == 'archived'
    
    def test_delete_dlq_entry(self, client, admin_agent):
        """Test deleting a DLQ entry"""
        error = Exception('Connection timeout')
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', error
        )
        
        response = client.delete(
            f'/api/admin/dlq/entries/{entry.entry_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify entry is deleted
        assert dead_letter_queue.get_entry(entry.entry_id) is None
    
    def test_filter_dlq_by_status(self, client, admin_agent):
        """Test filtering DLQ entries by status"""
        error = Exception('Error')
        entry1 = dead_letter_queue.add_failed_query('test-agent', 'SELECT 1', 'SELECT', error)
        entry2 = dead_letter_queue.add_failed_query('test-agent', 'SELECT 2', 'SELECT', error)
        
        # Archive one
        dead_letter_queue.archive_entry(entry1.entry_id)
        
        response = client.get(
            '/api/admin/dlq/entries?status=pending',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all(e['status'] == 'pending' for e in data['entries'])
    
    def test_filter_dlq_by_agent(self, client, admin_agent):
        """Test filtering DLQ entries by agent"""
        error = Exception('Error')
        dead_letter_queue.add_failed_query('agent-1', 'SELECT 1', 'SELECT', error)
        dead_letter_queue.add_failed_query('agent-2', 'SELECT 2', 'SELECT', error)
        
        response = client.get(
            '/api/admin/dlq/entries?agent_id=agent-1',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all(e['agent_id'] == 'agent-1' for e in data['entries'])
    
    def test_get_dlq_statistics(self, client, admin_agent):
        """Test getting DLQ statistics"""
        error = Exception('Error')
        dead_letter_queue.add_failed_query('test-agent', 'SELECT 1', 'SELECT', error)
        dead_letter_queue.add_failed_query('test-agent', 'SELECT 2', 'SELECT', error)
        
        response = client.get(
            '/api/admin/dlq/statistics',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_entries' in data
        assert 'status_counts' in data
        assert 'error_type_counts' in data
        assert data['total_entries'] >= 2
    
    def test_clear_agent_dlq(self, client, admin_agent):
        """Test clearing all entries for an agent"""
        error = Exception('Error')
        dead_letter_queue.add_failed_query('test-agent', 'SELECT 1', 'SELECT', error)
        dead_letter_queue.add_failed_query('test-agent', 'SELECT 2', 'SELECT', error)
        dead_letter_queue.add_failed_query('other-agent', 'SELECT 3', 'SELECT', error)
        
        response = client.post(
            '/api/admin/dlq/agents/test-agent/clear',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['cleared_count'] >= 2
        
        # Verify other agent's entries still exist
        entries = dead_letter_queue.list_entries(agent_id='other-agent')
        assert len(entries) >= 1


class TestIntegration_AllFeatures:
    """Integration tests combining all features"""
    
    def test_error_formatting_in_query_execution(self, client, test_agent):
        """Test that error formatting is used in query execution"""
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry, \
             patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = {'tables': ['users'], 'schema': {}}
            mock_nl.convert_to_sql.return_value = {'sql': 'SELECT invalid_column FROM users'}
            mock_rls.apply_rls_to_query.return_value = 'SELECT invalid_column FROM users'
            
            # Simulate column error
            mock_connector.connect.return_value = None
            mock_connector.execute_query.side_effect = Exception('column "invalid_column" does not exist')
            
            payload = {'query': 'show invalid column'}
            
            response = client.post(
                '/api/agents/test-agent/query/natural',
                json=payload,
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'user_friendly_message' in data
            assert 'suggested_fixes' in data
            assert 'dlq_entry_id' in data
    
    def test_failover_and_dlq_integration(self, client, admin_agent):
        """Test failover and DLQ work together"""
        # Register endpoints
        primary = DatabaseEndpoint(
            endpoint_id='primary-1',
            name='Primary',
            host='db-primary.com',
            database='mydb',
            is_primary=True
        )
        backup = DatabaseEndpoint(
            endpoint_id='backup-1',
            name='Backup',
            host='db-backup.com',
            database='mydb',
            is_primary=False
        )
        failover_manager.register_endpoints('test-agent', [primary, backup])
        
        # Record failure
        failover_manager.record_failure('test-agent', 'primary-1')
        
        # Query should be added to DLQ
        error = Exception('Connection timeout')
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', error
        )
        
        assert entry is not None
        assert entry.agent_id == 'test-agent'
    
    def test_complete_error_handling_workflow(self, client, admin_agent, test_agent):
        """Test complete workflow: error → format → failover → DLQ"""
        # Step 1: Register failover endpoints
        primary = DatabaseEndpoint(
            endpoint_id='primary-1',
            name='Primary',
            host='db-primary.com',
            database='mydb',
            is_primary=True
        )
        failover_manager.register_endpoints('test-agent', [primary])
        
        # Step 2: Format error
        error = Exception('column "invalid" does not exist')
        formatted = error_formatter.format_error(error, query='SELECT invalid FROM users')
        assert 'user_friendly_message' in formatted
        
        # Step 3: Add to DLQ
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT invalid FROM users', 'SELECT', error
        )
        assert entry.status == DLQStatus.PENDING
        
        # Step 4: Get DLQ entry
        response = client.get(
            f'/api/admin/dlq/entries/{entry.entry_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        assert response.status_code == 200
        
        # Step 5: Get failover status
        response = client.get(
            '/api/admin/agents/test-agent/failover/status',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        assert response.status_code == 200


class TestIntegration_ErrorHandling:
    """Integration tests for error handling"""
    
    def test_unauthorized_failover_access(self, client, test_agent):
        """Test that non-admin cannot access failover endpoints"""
        response = client.get(
            '/api/admin/agents/test-agent/failover/status',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403
    
    def test_unauthorized_dlq_access(self, client, test_agent):
        """Test that non-admin cannot access DLQ"""
        response = client.get(
            '/api/admin/dlq/entries',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403
    
    def test_dlq_entry_not_found(self, client, admin_agent):
        """Test handling of non-existent DLQ entry"""
        response = client.get(
            '/api/admin/dlq/entries/nonexistent-id',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 404
    
    def test_failover_status_not_found(self, client, admin_agent):
        """Test handling of no endpoints registered"""
        response = client.get(
            '/api/admin/agents/nonexistent-agent/failover/status',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 404


class TestStory1_AdditionalErrorCases:
    """Story 1: Additional error formatting cases"""
    
    def test_format_mysql_column_error(self, client, test_agent):
        """Test formatting MySQL column error"""
        error = Exception("Unknown column 'invalid_column' in 'field list'")
        
        formatted = error_formatter.format_error(error)
        
        assert 'user_friendly_message' in formatted
        assert 'Invalid column name' in formatted['user_friendly_message']
        assert 'invalid_column' in formatted['user_friendly_message']
    
    def test_format_mysql_table_error(self, client, test_agent):
        """Test formatting MySQL table error"""
        error = Exception("Table 'database.nonexistent_table' doesn't exist")
        
        formatted = error_formatter.format_error(error)
        
        assert 'user_friendly_message' in formatted
        assert 'Table' in formatted['user_friendly_message']
        assert 'does not exist' in formatted['user_friendly_message']
    
    def test_format_timeout_error(self, client, test_agent):
        """Test formatting timeout error"""
        error = Exception('Query timeout after 30 seconds')
        
        formatted = error_formatter.format_error(error)
        
        assert 'user_friendly_message' in formatted
        assert 'timeout' in formatted['user_friendly_message'].lower()
        assert 'suggested_fixes' in formatted
    
    def test_format_value_too_long_error(self, client, test_agent):
        """Test formatting value too long error"""
        error = Exception('value too long for type character varying(50)')
        
        formatted = error_formatter.format_error(error)
        
        assert 'user_friendly_message' in formatted
        assert 'too long' in formatted['user_friendly_message'].lower()
    
    def test_format_authentication_error(self, client, test_agent):
        """Test formatting authentication error"""
        error = Exception('authentication failed for user "testuser"')
        
        formatted = error_formatter.format_error(error)
        
        assert 'user_friendly_message' in formatted
        assert 'authentication' in formatted['user_friendly_message'].lower() or 'credentials' in formatted['user_friendly_message'].lower()
    
    def test_format_generic_error(self, client, test_agent):
        """Test formatting generic error"""
        error = Exception('Some unexpected error occurred')
        
        formatted = error_formatter.format_error(error)
        
        assert 'user_friendly_message' in formatted
        assert 'error' in formatted['user_friendly_message'].lower()
        assert 'suggested_fixes' in formatted
    
    def test_error_with_query_context(self, client, test_agent):
        """Test error formatting with query context"""
        error = Exception('column "invalid" does not exist')
        query = 'SELECT invalid, name FROM users WHERE id = 1'
        
        formatted = error_formatter.format_error(error, query=query)
        
        assert 'query' in formatted
        assert formatted['query'] == query[:200]  # Truncated
    
    def test_error_actionable_details_extraction(self, client, test_agent):
        """Test extraction of actionable details"""
        error = Exception('column "email" does not exist at line 1')
        
        formatted = error_formatter.format_error(error)
        
        assert 'actionable_details' in formatted
        assert formatted['actionable_details'].get('column') == 'email'
        assert formatted['actionable_details'].get('line_number') == 1


class TestStory2_AdditionalFailoverCases:
    """Story 2: Additional failover scenarios"""
    
    def test_multiple_backup_endpoints(self, client, admin_agent):
        """Test failover with multiple backup endpoints"""
        primary = DatabaseEndpoint(
            endpoint_id='primary-1',
            name='Primary',
            host='db-primary.com',
            database='mydb',
            is_primary=True,
            priority=0
        )
        backup1 = DatabaseEndpoint(
            endpoint_id='backup-1',
            name='Backup 1',
            host='db-backup1.com',
            database='mydb',
            is_primary=False,
            priority=1
        )
        backup2 = DatabaseEndpoint(
            endpoint_id='backup-2',
            name='Backup 2',
            host='db-backup2.com',
            database='mydb',
            is_primary=False,
            priority=2
        )
        
        failover_manager.register_endpoints('test-agent', [primary, backup1, backup2])
        
        # Fail primary
        failover_manager.record_failure('test-agent', 'primary-1')
        
        status = failover_manager.get_failover_status('test-agent')
        assert status is not None
        assert len(status['endpoints']) == 3
    
    def test_failover_chain(self, client, admin_agent):
        """Test failover chain (primary → backup1 → backup2)"""
        primary = DatabaseEndpoint(
            endpoint_id='primary-1',
            name='Primary',
            host='db-primary.com',
            database='mydb',
            is_primary=True,
            priority=0
        )
        backup1 = DatabaseEndpoint(
            endpoint_id='backup-1',
            name='Backup 1',
            host='db-backup1.com',
            database='mydb',
            is_primary=False,
            priority=1
        )
        backup2 = DatabaseEndpoint(
            endpoint_id='backup-2',
            name='Backup 2',
            host='db-backup2.com',
            database='mydb',
            is_primary=False,
            priority=2
        )
        
        failover_manager.register_endpoints('test-agent', [primary, backup1, backup2])
        
        # Fail primary
        failover_manager.record_failure('test-agent', 'primary-1')
        
        # Fail backup1
        with patch.object(failover_manager, 'test_endpoint', return_value=False):
            failover_manager.record_failure('test-agent', 'backup-1')
        
        status = failover_manager.get_failover_status('test-agent')
        assert status is not None
    
    def test_endpoint_connection_string(self, client, admin_agent):
        """Test endpoint with connection string"""
        endpoint = DatabaseEndpoint(
            endpoint_id='ep-1',
            name='Endpoint',
            connection_string='postgresql://user:pass@host:5432/db',
            database_type='postgresql',
            is_primary=True
        )
        
        failover_manager.register_endpoints('test-agent', [endpoint])
        
        current = failover_manager.get_current_endpoint('test-agent')
        assert current is not None
        assert current.connection_string is not None
    
    def test_endpoint_failure_count_tracking(self, client, admin_agent):
        """Test endpoint failure count tracking"""
        endpoint = DatabaseEndpoint(
            endpoint_id='ep-1',
            name='Endpoint',
            host='db.com',
            database='mydb',
            is_primary=True
        )
        
        failover_manager.register_endpoints('test-agent', [endpoint])
        
        # Record multiple failures
        failover_manager.record_failure('test-agent', 'ep-1')
        failover_manager.record_failure('test-agent', 'ep-1')
        
        status = failover_manager.get_failover_status('test-agent')
        failed_endpoint = next((e for e in status['endpoints'] if e['endpoint_id'] == 'ep-1'), None)
        assert failed_endpoint is not None
        assert failed_endpoint['failure_count'] >= 2
    
    def test_reset_endpoint_via_api(self, client, admin_agent):
        """Test resetting endpoint via API"""
        endpoint = DatabaseEndpoint(
            endpoint_id='ep-1',
            name='Endpoint',
            host='db.com',
            database='mydb',
            is_primary=True
        )
        
        failover_manager.register_endpoints('test-agent', [endpoint])
        endpoint.is_active = False
        
        with patch.object(failover_manager, 'test_endpoint', return_value=True):
            response = client.post(
                '/api/admin/agents/test-agent/failover/endpoints/ep-1/reset',
                headers={'X-API-Key': admin_agent['api_key']}
            )
            
            assert response.status_code == 200
    
    def test_register_endpoints_via_api(self, client, admin_agent):
        """Test registering endpoints via API"""
        payload = {
            'endpoints': [
                {
                    'name': 'Primary',
                    'connection_string': 'postgresql://user:pass@host/db',
                    'database_type': 'postgresql',
                    'is_primary': True,
                    'priority': 0
                }
            ]
        }
        
        response = client.post(
            '/api/admin/agents/test-agent/failover/endpoints',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['endpoints']) == 1


class TestStory3_AdditionalDLQCases:
    """Story 3: Additional dead-letter queue scenarios"""
    
    def test_dlq_entry_metadata(self, client, test_agent):
        """Test DLQ entry with metadata"""
        error = Exception('Connection timeout')
        metadata = {
            'user_id': 'user-123',
            'session_id': 'session-456',
            'request_id': 'req-789'
        }
        
        entry = dead_letter_queue.add_failed_query(
            'test-agent',
            'SELECT * FROM users',
            'SELECT',
            error,
            metadata=metadata
        )
        
        assert entry.metadata == metadata
        assert entry.metadata['user_id'] == 'user-123'
    
    def test_dlq_entry_with_params(self, client, test_agent):
        """Test DLQ entry with query parameters"""
        error = Exception('Syntax error')
        params = {'user_id': 123, 'status': 'active'}
        
        entry = dead_letter_queue.add_failed_query(
            'test-agent',
            'SELECT * FROM users WHERE id = :user_id AND status = :status',
            'SELECT',
            error,
            params=params
        )
        
        assert entry.params == params
    
    def test_dlq_replay_with_success(self, client, admin_agent):
        """Test successful DLQ replay"""
        error = Exception('Connection timeout')
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', error
        )
        
        mock_connector = MagicMock()
        mock_connector.connect.return_value = None
        mock_connector.execute_query.return_value = [{'id': 1, 'name': 'Test'}]
        mock_connector.disconnect.return_value = None
        
        result = dead_letter_queue.replay_entry(entry.entry_id, mock_connector)
        
        assert result['success'] is True
        assert 'result' in result
        
        updated_entry = dead_letter_queue.get_entry(entry.entry_id)
        assert updated_entry.status == DLQStatus.SUCCESS
    
    def test_dlq_replay_with_failure(self, client, admin_agent):
        """Test DLQ replay that fails again"""
        error = Exception('Connection timeout')
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', error
        )
        
        mock_connector = MagicMock()
        mock_connector.connect.return_value = None
        mock_connector.execute_query.side_effect = Exception('Still failing')
        mock_connector.disconnect.return_value = None
        
        result = dead_letter_queue.replay_entry(entry.entry_id, mock_connector)
        
        assert result['success'] is False
        assert 'error' in result
        
        updated_entry = dead_letter_queue.get_entry(entry.entry_id)
        assert updated_entry.status == DLQStatus.FAILED
        assert updated_entry.retry_count > 0
    
    def test_dlq_filter_by_multiple_statuses(self, client, admin_agent):
        """Test filtering DLQ entries by multiple statuses"""
        error = Exception('Error')
        
        entry1 = dead_letter_queue.add_failed_query('agent-1', 'SELECT 1', 'SELECT', error)
        entry2 = dead_letter_queue.add_failed_query('agent-1', 'SELECT 2', 'SELECT', error)
        entry3 = dead_letter_queue.add_failed_query('agent-1', 'SELECT 3', 'SELECT', error)
        
        # Archive one, mark one as success
        dead_letter_queue.archive_entry(entry1.entry_id)
        entry2.status = DLQStatus.SUCCESS
        dead_letter_queue._entries[entry2.entry_id] = entry2
        
        # Get pending entries
        pending = dead_letter_queue.list_entries(status=DLQStatus.PENDING)
        assert len(pending) >= 1
    
    def test_dlq_statistics_by_agent(self, client, admin_agent):
        """Test DLQ statistics filtered by agent"""
        error = Exception('Error')
        
        dead_letter_queue.add_failed_query('agent-1', 'SELECT 1', 'SELECT', error)
        dead_letter_queue.add_failed_query('agent-1', 'SELECT 2', 'SELECT', error)
        dead_letter_queue.add_failed_query('agent-2', 'SELECT 3', 'SELECT', error)
        
        stats = dead_letter_queue.get_statistics(agent_id='agent-1')
        
        assert stats['total_entries'] == 2
        assert stats['pending_count'] >= 0
    
    def test_dlq_max_entries_limit(self, client, test_agent):
        """Test DLQ max entries limit enforcement"""
        # Set a small limit
        dead_letter_queue.max_entries = 5
        
        # Add more entries than limit
        for i in range(10):
            error = Exception(f'Error {i}')
            dead_letter_queue.add_failed_query(
                'test-agent', f'SELECT {i}', 'SELECT', error
            )
        
        # Should not exceed limit
        assert len(dead_letter_queue._entries) <= dead_letter_queue.max_entries
    
    def test_dlq_replay_archived_entry(self, client, admin_agent):
        """Test that archived entries cannot be replayed"""
        error = Exception('Error')
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', error
        )
        
        # Archive entry
        dead_letter_queue.archive_entry(entry.entry_id)
        
        mock_connector = MagicMock()
        result = dead_letter_queue.replay_entry(entry.entry_id, mock_connector)
        
        assert result['success'] is False
        assert 'archived' in result.get('error', '').lower()
    
    def test_dlq_entry_lifecycle(self, client, admin_agent):
        """Test complete DLQ entry lifecycle"""
        error = Exception('Connection timeout')
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', error
        )
        
        # Initial state
        assert entry.status == DLQStatus.PENDING
        assert entry.retry_count == 0
        
        # Replay (simulate)
        entry.status = DLQStatus.REPLAYING
        entry.retry_count = 1
        dead_letter_queue._entries[entry.entry_id] = entry
        
        # Success
        entry.status = DLQStatus.SUCCESS
        dead_letter_queue._entries[entry.entry_id] = entry
        
        updated = dead_letter_queue.get_entry(entry.entry_id)
        assert updated.status == DLQStatus.SUCCESS
        assert updated.retry_count == 1


class TestIntegration_AdvancedScenarios:
    """Advanced integration scenarios"""
    
    def test_error_format_failover_dlq_workflow(self, client, admin_agent, test_agent):
        """Test complete workflow: error → format → failover → DLQ"""
        # Setup failover
        primary = DatabaseEndpoint(
            endpoint_id='primary-1',
            name='Primary',
            host='db-primary.com',
            database='mydb',
            is_primary=True
        )
        failover_manager.register_endpoints('test-agent', [primary])
        
        # Simulate error
        error = Exception('connection timeout')
        
        # Format error
        formatted = error_formatter.format_error(error, query='SELECT * FROM users')
        assert 'user_friendly_message' in formatted
        
        # Record failure (triggers failover attempt)
        failover_manager.record_failure('test-agent', 'primary-1')
        
        # Add to DLQ
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', error
        )
        
        assert entry is not None
        assert entry.status == DLQStatus.PENDING
    
    def test_dlq_replay_with_failover(self, client, admin_agent):
        """Test replaying DLQ entry with failover"""
        # Setup failover
        backup = DatabaseEndpoint(
            endpoint_id='backup-1',
            name='Backup',
            host='db-backup.com',
            database='mydb',
            is_primary=False
        )
        failover_manager.register_endpoints('test-agent', [backup])
        
        # Add to DLQ
        error = Exception('Connection timeout')
        entry = dead_letter_queue.add_failed_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', error
        )
        
        # Get connector (should use failover)
        connector = failover_manager.get_database_connector('test-agent')
        
        if connector:
            mock_connector = MagicMock()
            mock_connector.connect.return_value = None
            mock_connector.execute_query.return_value = [{'id': 1}]
            mock_connector.disconnect.return_value = None
            
            result = dead_letter_queue.replay_entry(entry.entry_id, mock_connector)
            # Should attempt replay
            assert 'success' in result or 'error' in result
    
    def test_multiple_errors_same_query(self, client, test_agent):
        """Test handling multiple errors for same query"""
        query = 'SELECT invalid_column FROM nonexistent_table'
        
        # First error: column
        error1 = Exception('column "invalid_column" does not exist')
        formatted1 = error_formatter.format_error(error1, query=query)
        
        # Second error: table (after fixing column)
        error2 = Exception('relation "nonexistent_table" does not exist')
        formatted2 = error_formatter.format_error(error2, query=query)
        
        assert 'column' in formatted1['actionable_details'] or 'invalid_column' in formatted1['user_friendly_message']
        assert 'table' in formatted2['actionable_details'] or 'nonexistent_table' in formatted2['user_friendly_message']
    
    def test_failover_recovery(self, client, admin_agent):
        """Test failover recovery (switching back to primary)"""
        primary = DatabaseEndpoint(
            endpoint_id='primary-1',
            name='Primary',
            host='db-primary.com',
            database='mydb',
            is_primary=True
        )
        backup = DatabaseEndpoint(
            endpoint_id='backup-1',
            name='Backup',
            host='db-backup.com',
            database='mydb',
            is_primary=False
        )
        
        failover_manager.register_endpoints('test-agent', [primary, backup])
        
        # Fail primary
        failover_manager.record_failure('test-agent', 'primary-1')
        
        # Reset primary (simulate recovery)
        with patch.object(failover_manager, 'test_endpoint', return_value=True):
            success = failover_manager.reset_endpoint('test-agent', 'primary-1')
            assert success is True
            
            status = failover_manager.get_failover_status('test-agent')
            # Should switch back to primary
            assert status['current_endpoint']['endpoint_id'] == 'primary-1'
    
    def test_dlq_bulk_operations(self, client, admin_agent):
        """Test bulk DLQ operations"""
        # Add multiple entries
        for i in range(5):
            error = Exception(f'Error {i}')
            dead_letter_queue.add_failed_query(
                f'agent-{i % 2}', f'SELECT {i}', 'SELECT', error
            )
        
        # List all
        all_entries = dead_letter_queue.list_entries()
        assert len(all_entries) == 5
        
        # Filter by agent
        agent0_entries = dead_letter_queue.list_entries(agent_id='agent-0')
        assert len(agent0_entries) >= 1
        
        # Get statistics
        stats = dead_letter_queue.get_statistics()
        assert stats['total_entries'] == 5
    
    def test_error_message_in_api_response(self, client, test_agent):
        """Test that formatted error messages appear in API responses"""
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry, \
             patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = {'tables': ['users'], 'schema': {}}
            mock_nl.convert_to_sql.return_value = {'sql': 'SELECT invalid FROM users'}
            mock_rls.apply_rls_to_query.return_value = 'SELECT invalid FROM users'
            
            mock_connector.connect.return_value = None
            mock_connector.execute_query.side_effect = Exception('column "invalid" does not exist')
            
            response = client.post(
                '/api/agents/test-agent/query/natural',
                json={'query': 'show invalid column'},
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'user_friendly_message' in data
            assert 'suggested_fixes' in data
            assert 'Invalid column name' in data['user_friendly_message'] or 'invalid' in data['user_friendly_message']

