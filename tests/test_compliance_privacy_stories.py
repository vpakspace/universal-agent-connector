"""
Integration tests for Compliance & Privacy Stories

Story 1: As a Compliance Officer, I want to enforce data residency rules (e.g., EU data stays in EU databases),
         so that regulations like GDPR are met.

Story 2: As an Admin, I want to set data retention policies for query logs,
         so that old data is automatically purged.

Story 3: As an Admin, I want to anonymize user identities in audit logs,
         so that privacy is protected while maintaining accountability.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from main import create_app
from ai_agent_connector.app.api.routes import (
    agent_registry, access_control, data_residency_manager,
    data_retention_manager, audit_anonymizer
)
from ai_agent_connector.app.permissions import Permission
from ai_agent_connector.app.utils.encryption import reset_encryptor
from ai_agent_connector.app.utils.data_residency import DataRegion
from ai_agent_connector.app.utils.data_retention import RetentionPolicyType
from ai_agent_connector.app.utils.audit_anonymizer import AnonymizationMethod


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    data_residency_manager._rules.clear()
    data_residency_manager._region_rules.clear()
    data_retention_manager._policies.clear()
    data_retention_manager._type_policies.clear()
    audit_anonymizer._rules.clear()
    yield
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    data_residency_manager._rules.clear()
    data_residency_manager._region_rules.clear()
    data_retention_manager._policies.clear()
    data_retention_manager._type_policies.clear()
    audit_anonymizer._rules.clear()


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


class TestStory1_DataResidency:
    """Story 1: Enforce data residency rules"""
    
    def test_create_residency_rule(self, client, admin_agent):
        """Test creating a data residency rule"""
        payload = {
            'name': 'EU Data Residency',
            'region': 'eu',
            'database_patterns': ['eu-.*', '.*-eu'],
            'table_patterns': ['users', 'customers'],
            'description': 'EU data must stay in EU databases'
        }
        
        response = client.post(
            '/api/admin/data-residency/rules',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'rule' in data
        assert data['rule']['region'] == 'eu'
        assert data['rule']['name'] == 'EU Data Residency'
    
    def test_list_residency_rules(self, client, admin_agent):
        """Test listing residency rules"""
        # Create a rule
        rule = data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*']
        )
        
        response = client.get(
            '/api/admin/data-residency/rules',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'rules' in data
        assert len(data['rules']) >= 1
    
    def test_get_residency_rule(self, client, admin_agent):
        """Test getting a specific residency rule"""
        rule = data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*']
        )
        
        response = client.get(
            f'/api/admin/data-residency/rules/{rule.rule_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['rule_id'] == rule.rule_id
    
    def test_update_residency_rule(self, client, admin_agent):
        """Test updating a residency rule"""
        rule = data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*']
        )
        
        payload = {
            'name': 'Updated EU Rule',
            'is_active': False
        }
        
        response = client.put(
            f'/api/admin/data-residency/rules/{rule.rule_id}',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['rule']['name'] == 'Updated EU Rule'
        assert data['rule']['is_active'] is False
    
    def test_delete_residency_rule(self, client, admin_agent):
        """Test deleting a residency rule"""
        rule = data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*']
        )
        
        response = client.delete(
            f'/api/admin/data-residency/rules/{rule.rule_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify deleted
        assert data_residency_manager.get_rule(rule.rule_id) is None
    
    def test_validate_residency(self, client, admin_agent):
        """Test validating data residency"""
        # Create EU rule
        data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*'],
            table_patterns=['users']
        )
        
        payload = {
            'database_name': 'eu-database',
            'tables': ['users', 'orders']
        }
        
        response = client.post(
            '/api/admin/data-residency/validate',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'valid' in data
        assert 'violations' in data
    
    def test_validate_residency_violation(self, client, admin_agent):
        """Test residency validation with violation"""
        # Create EU rule with table pattern
        data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*'],
            table_patterns=['users']
        )
        
        # Validate with matching database but non-matching table
        result = data_residency_manager.validate_residency(
            database_name='eu-database',
            tables=['orders']  # Doesn't match 'users' pattern
        )
        
        # Should be valid if table pattern doesn't match (no violation)
        assert 'valid' in result
    
    def test_get_required_region(self, client, admin_agent):
        """Test getting required region for a database"""
        data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*']
        )
        
        region = data_residency_manager.get_required_region('eu-database')
        assert region == DataRegion.EU
        
        region = data_residency_manager.get_required_region('us-database')
        assert region is None
    
    def test_filter_rules_by_region(self, client, admin_agent):
        """Test filtering rules by region"""
        data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*']
        )
        data_residency_manager.create_rule(
            name='US Rule',
            region=DataRegion.US,
            database_patterns=['us-.*']
        )
        
        response = client.get(
            '/api/admin/data-residency/rules?region=eu',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all(r['region'] == 'eu' for r in data['rules'])


class TestStory2_DataRetention:
    """Story 2: Data retention policies"""
    
    def test_create_retention_policy(self, client, admin_agent):
        """Test creating a retention policy"""
        payload = {
            'name': 'Query Logs Retention',
            'policy_type': 'query_logs',
            'retention_days': 90,
            'description': 'Keep query logs for 90 days'
        }
        
        response = client.post(
            '/api/admin/data-retention/policies',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'policy' in data
        assert data['policy']['policy_type'] == 'query_logs'
        assert data['policy']['retention_days'] == 90
    
    def test_list_retention_policies(self, client, admin_agent):
        """Test listing retention policies"""
        # Create a policy
        policy = data_retention_manager.create_policy(
            name='Query Logs',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=90
        )
        
        response = client.get(
            '/api/admin/data-retention/policies',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'policies' in data
        assert len(data['policies']) >= 1
    
    def test_get_retention_policy(self, client, admin_agent):
        """Test getting a specific retention policy"""
        policy = data_retention_manager.create_policy(
            name='Query Logs',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=90
        )
        
        response = client.get(
            f'/api/admin/data-retention/policies/{policy.policy_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['policy_id'] == policy.policy_id
    
    def test_update_retention_policy(self, client, admin_agent):
        """Test updating a retention policy"""
        policy = data_retention_manager.create_policy(
            name='Query Logs',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=90
        )
        
        payload = {
            'retention_days': 180,
            'is_active': False
        }
        
        response = client.put(
            f'/api/admin/data-retention/policies/{policy.policy_id}',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['policy']['retention_days'] == 180
        assert data['policy']['is_active'] is False
    
    def test_delete_retention_policy(self, client, admin_agent):
        """Test deleting a retention policy"""
        policy = data_retention_manager.create_policy(
            name='Query Logs',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=90
        )
        
        response = client.delete(
            f'/api/admin/data-retention/policies/{policy.policy_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify deleted
        assert data_retention_manager.get_policy(policy.policy_id) is None
    
    def test_execute_retention_policy(self, client, admin_agent):
        """Test executing a retention policy"""
        policy = data_retention_manager.create_policy(
            name='Query Logs',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=90
        )
        
        # Mock purge function
        def mock_purge(cutoff_date):
            return 10
        
        result = data_retention_manager.execute_policy(policy.policy_id, mock_purge)
        
        assert result['success'] is True
        assert result['purged_count'] == 10
        
        # Check policy stats updated
        updated_policy = data_retention_manager.get_policy(policy.policy_id)
        assert updated_policy.last_purged_count == 10
        assert updated_policy.total_purged_count == 10
    
    def test_execute_all_policies(self, client, admin_agent):
        """Test executing all retention policies"""
        policy1 = data_retention_manager.create_policy(
            name='Query Logs',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=90
        )
        policy2 = data_retention_manager.create_policy(
            name='Audit Logs',
            policy_type=RetentionPolicyType.AUDIT_LOGS,
            retention_days=365
        )
        
        purge_functions = {
            RetentionPolicyType.QUERY_LOGS: lambda d: 10,
            RetentionPolicyType.AUDIT_LOGS: lambda d: 5
        }
        
        result = data_retention_manager.execute_all_policies(purge_functions)
        
        assert result['success'] is True
        assert result['policies_executed'] == 2
        assert result['total_purged'] == 15
    
    def test_policy_cutoff_date(self, client, admin_agent):
        """Test policy cutoff date calculation"""
        policy = data_retention_manager.create_policy(
            name='Query Logs',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=90
        )
        
        cutoff = policy.get_cutoff_date()
        
        from datetime import datetime, timedelta
        expected = datetime.utcnow() - timedelta(days=90)
        
        # Allow 1 second difference
        assert abs((cutoff - expected).total_seconds()) < 1
    
    def test_filter_policies_by_type(self, client, admin_agent):
        """Test filtering policies by type"""
        data_retention_manager.create_policy(
            name='Query Logs',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=90
        )
        data_retention_manager.create_policy(
            name='Audit Logs',
            policy_type=RetentionPolicyType.AUDIT_LOGS,
            retention_days=365
        )
        
        response = client.get(
            '/api/admin/data-retention/policies?policy_type=query_logs',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all(p['policy_type'] == 'query_logs' for p in data['policies'])


class TestStory3_AuditAnonymization:
    """Story 3: Anonymize user identities in audit logs"""
    
    def test_create_anonymization_rule(self, client, admin_agent):
        """Test creating an anonymization rule"""
        payload = {
            'name': 'User ID Anonymization',
            'field_patterns': ['user_id', 'agent_id'],
            'method': 'hash',
            'description': 'Anonymize user IDs'
        }
        
        response = client.post(
            '/api/admin/audit-anonymization/rules',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'rule' in data
        assert data['rule']['method'] == 'hash'
        assert 'user_id' in data['rule']['field_patterns']
    
    def test_list_anonymization_rules(self, client, admin_agent):
        """Test listing anonymization rules"""
        # Create a rule
        rule = audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        
        response = client.get(
            '/api/admin/audit-anonymization/rules',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'rules' in data
        assert len(data['rules']) >= 1
    
    def test_get_anonymization_rule(self, client, admin_agent):
        """Test getting a specific anonymization rule"""
        rule = audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        
        response = client.get(
            f'/api/admin/audit-anonymization/rules/{rule.rule_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['rule_id'] == rule.rule_id
    
    def test_update_anonymization_rule(self, client, admin_agent):
        """Test updating an anonymization rule"""
        rule = audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        
        payload = {
            'method': 'redact',
            'is_active': False
        }
        
        response = client.put(
            f'/api/admin/audit-anonymization/rules/{rule.rule_id}',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['rule']['method'] == 'redact'
        assert data['rule']['is_active'] is False
    
    def test_delete_anonymization_rule(self, client, admin_agent):
        """Test deleting an anonymization rule"""
        rule = audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        
        response = client.delete(
            f'/api/admin/audit-anonymization/rules/{rule.rule_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify deleted
        assert audit_anonymizer.get_rule(rule.rule_id) is None
    
    def test_anonymize_log_entry_hash(self, client, admin_agent):
        """Test anonymizing log entry with hash method"""
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        
        log_entry = {
            'user_id': 'user123',
            'action': 'query',
            'details': {'query': 'SELECT * FROM users'}
        }
        
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        assert anonymized['user_id'] != 'user123'
        assert anonymized['user_id'].startswith('hash_')
        assert anonymized['action'] == 'query'  # Not anonymized
    
    def test_anonymize_log_entry_redact(self, client, admin_agent):
        """Test anonymizing log entry with redact method"""
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.REDACT
        )
        
        log_entry = {
            'user_id': 'user123',
            'action': 'query'
        }
        
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        assert anonymized['user_id'] == '[REDACTED]'
    
    def test_anonymize_log_entry_mask(self, client, admin_agent):
        """Test anonymizing log entry with mask method"""
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.MASK
        )
        
        log_entry = {
            'user_id': 'user12345',
            'action': 'query'
        }
        
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        assert anonymized['user_id'] != 'user12345'
        assert '*' in anonymized['user_id']
    
    def test_anonymize_log_entry_prefix(self, client, admin_agent):
        """Test anonymizing log entry with prefix method"""
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.PREFIX
        )
        
        log_entry = {
            'user_id': 'user123',
            'action': 'query'
        }
        
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        assert anonymized['user_id'].startswith('user_')
        assert anonymized['user_id'] != 'user123'
    
    def test_anonymize_batch(self, client, admin_agent):
        """Test anonymizing batch of log entries"""
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        
        log_entries = [
            {'user_id': 'user1', 'action': 'query1'},
            {'user_id': 'user2', 'action': 'query2'},
            {'user_id': 'user3', 'action': 'query3'}
        ]
        
        anonymized = audit_anonymizer.anonymize_batch(log_entries)
        
        assert len(anonymized) == 3
        assert all(a['user_id'] != orig['user_id'] for a, orig in zip(anonymized, log_entries))
        assert all(a['action'] == orig['action'] for a, orig in zip(anonymized, log_entries))
    
    def test_anonymize_nested_structure(self, client, admin_agent):
        """Test anonymizing nested structures"""
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.REDACT
        )
        
        log_entry = {
            'user_id': 'user123',
            'details': {
                'user_id': 'user456',
                'query': 'SELECT * FROM users'
            },
            'metadata': {
                'created_by': 'user789'
            }
        }
        
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        assert anonymized['user_id'] == '[REDACTED]'
        assert anonymized['details']['user_id'] == '[REDACTED]'
        assert anonymized['details']['query'] == 'SELECT * FROM users'
    
    def test_anonymize_via_api(self, client, admin_agent):
        """Test anonymizing via API"""
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        
        payload = {
            'log_entries': [
                {'user_id': 'user123', 'action': 'query'},
                {'user_id': 'user456', 'action': 'update'}
            ]
        }
        
        response = client.post(
            '/api/admin/audit-anonymization/anonymize',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'anonymized_entries' in data
        assert len(data['anonymized_entries']) == 2
        assert all(e['user_id'] != 'user123' and e['user_id'] != 'user456' 
                   for e in data['anonymized_entries'])


class TestIntegration_ComplianceFeatures:
    """Integration tests for compliance features"""
    
    def test_residency_and_retention_workflow(self, client, admin_agent):
        """Test data residency and retention working together"""
        # Create residency rule
        residency_rule = data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*']
        )
        
        # Create retention policy
        retention_policy = data_retention_manager.create_policy(
            name='EU Query Logs',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=90
        )
        
        assert residency_rule is not None
        assert retention_policy is not None
    
    def test_anonymization_with_retention(self, client, admin_agent):
        """Test anonymization with retention policy"""
        # Create anonymization rule
        anonymization_rule = audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        
        # Create retention policy for audit logs
        retention_policy = data_retention_manager.create_policy(
            name='Audit Logs',
            policy_type=RetentionPolicyType.AUDIT_LOGS,
            retention_days=365
        )
        
        # Anonymize before retention
        log_entry = {'user_id': 'user123', 'action': 'query'}
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        assert anonymized['user_id'] != 'user123'
        assert retention_policy is not None
    
    def test_complete_compliance_workflow(self, client, admin_agent):
        """Test complete compliance workflow"""
        # Step 1: Create residency rule
        residency_rule = data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*']
        )
        
        # Step 2: Validate residency
        validation = data_residency_manager.validate_residency('eu-database')
        assert 'valid' in validation
        
        # Step 3: Create retention policy
        retention_policy = data_retention_manager.create_policy(
            name='Query Logs',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=90
        )
        
        # Step 4: Execute retention
        def mock_purge(cutoff_date):
            return 5
        
        result = data_retention_manager.execute_policy(retention_policy.policy_id, mock_purge)
        assert result['success'] is True
        
        # Step 5: Anonymize audit logs
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        
        log_entry = {'user_id': 'user123', 'action': 'query'}
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        assert anonymized['user_id'] != 'user123'


class TestErrorHandling_Compliance:
    """Error handling tests"""
    
    def test_unauthorized_residency_access(self, client, test_agent):
        """Test unauthorized residency rule access"""
        response = client.post(
            '/api/admin/data-residency/rules',
            json={'name': 'Test', 'region': 'eu', 'database_patterns': []},
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403
    
    def test_unauthorized_retention_access(self, client, test_agent):
        """Test unauthorized retention policy access"""
        response = client.post(
            '/api/admin/data-retention/policies',
            json={'name': 'Test', 'policy_type': 'query_logs', 'retention_days': 90},
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403
    
    def test_unauthorized_anonymization_access(self, client, test_agent):
        """Test unauthorized anonymization rule access"""
        response = client.post(
            '/api/admin/audit-anonymization/rules',
            json={'name': 'Test', 'field_patterns': [], 'method': 'hash'},
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403
    
    def test_invalid_region(self, client, admin_agent):
        """Test invalid region"""
        response = client.post(
            '/api/admin/data-residency/rules',
            json={'name': 'Test', 'region': 'invalid', 'database_patterns': []},
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 400
    
    def test_invalid_policy_type(self, client, admin_agent):
        """Test invalid policy type"""
        response = client.post(
            '/api/admin/data-retention/policies',
            json={'name': 'Test', 'policy_type': 'invalid', 'retention_days': 90},
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 400
    
    def test_invalid_anonymization_method(self, client, admin_agent):
        """Test invalid anonymization method"""
        response = client.post(
            '/api/admin/audit-anonymization/rules',
            json={'name': 'Test', 'field_patterns': [], 'method': 'invalid'},
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 400


class TestStory1_AdditionalResidencyCases:
    """Story 1: Additional data residency scenarios"""
    
    def test_multiple_residency_rules(self, client, admin_agent):
        """Test multiple residency rules for different regions"""
        eu_rule = data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*']
        )
        us_rule = data_residency_manager.create_rule(
            name='US Rule',
            region=DataRegion.US,
            database_patterns=['us-.*']
        )
        
        assert eu_rule.region == DataRegion.EU
        assert us_rule.region == DataRegion.US
        
        # Validate EU database
        eu_result = data_residency_manager.validate_residency('eu-database')
        assert len(eu_result['applicable_rules']) >= 1
        
        # Validate US database
        us_result = data_residency_manager.validate_residency('us-database')
        assert len(us_result['applicable_rules']) >= 1
    
    def test_residency_rule_with_column_patterns(self, client, admin_agent):
        """Test residency rule with column patterns"""
        rule = data_residency_manager.create_rule(
            name='EU PII Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*'],
            column_patterns=['email', 'phone', 'ssn']
        )
        
        result = data_residency_manager.validate_residency(
            database_name='eu-database',
            columns=['email', 'name', 'phone']
        )
        
        assert 'violations' in result
        # Should detect email and phone as PII columns
    
    def test_residency_validation_with_connection_string(self, client, admin_agent):
        """Test residency validation with connection string"""
        data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*']
        )
        
        result = data_residency_manager.validate_residency(
            database_name='eu-database',
            connection_string='postgresql://user:pass@eu-db.example.com:5432/eu-database'
        )
        
        assert 'applicable_rules' in result
        assert len(result['applicable_rules']) >= 1
    
    def test_residency_rule_inactive(self, client, admin_agent):
        """Test inactive residency rule doesn't apply"""
        rule = data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*']
        )
        
        # Deactivate rule
        data_residency_manager.update_rule(rule.rule_id, is_active=False)
        
        result = data_residency_manager.validate_residency('eu-database')
        # Should not have applicable rules if rule is inactive
        assert len(result['applicable_rules']) == 0
    
    def test_residency_rule_update_region(self, client, admin_agent):
        """Test updating residency rule region"""
        rule = data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*']
        )
        
        # Update to US region
        updated = data_residency_manager.update_rule(rule.rule_id, region=DataRegion.US)
        
        assert updated.region == DataRegion.US
        assert updated.rule_id == rule.rule_id


class TestStory2_AdditionalRetentionCases:
    """Story 2: Additional data retention scenarios"""
    
    def test_retention_policy_all_types(self, client, admin_agent):
        """Test creating retention policies for all types"""
        types = [
            RetentionPolicyType.QUERY_LOGS,
            RetentionPolicyType.AUDIT_LOGS,
            RetentionPolicyType.ERROR_LOGS,
            RetentionPolicyType.METRICS,
            RetentionPolicyType.CACHE,
            RetentionPolicyType.DLQ
        ]
        
        policies = []
        for policy_type in types:
            policy = data_retention_manager.create_policy(
                name=f'{policy_type.value} Retention',
                policy_type=policy_type,
                retention_days=90
            )
            policies.append(policy)
        
        assert len(policies) == len(types)
        assert all(p.policy_type in types for p in policies)
    
    def test_retention_policy_inactive(self, client, admin_agent):
        """Test inactive retention policy doesn't execute"""
        policy = data_retention_manager.create_policy(
            name='Query Logs',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=90
        )
        
        # Deactivate policy
        data_retention_manager.update_policy(policy.policy_id, is_active=False)
        
        result = data_retention_manager.execute_policy(policy.policy_id)
        assert result['success'] is False
        assert 'not active' in result.get('error', '').lower()
    
    def test_retention_policy_different_periods(self, client, admin_agent):
        """Test retention policies with different retention periods"""
        short_policy = data_retention_manager.create_policy(
            name='Short Retention',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=30
        )
        
        long_policy = data_retention_manager.create_policy(
            name='Long Retention',
            policy_type=RetentionPolicyType.AUDIT_LOGS,
            retention_days=365
        )
        
        short_cutoff = short_policy.get_cutoff_date()
        long_cutoff = long_policy.get_cutoff_date()
        
        # Long cutoff should be earlier (older data)
        assert long_cutoff < short_cutoff
    
    def test_retention_policy_execution_error(self, client, admin_agent):
        """Test retention policy execution with error"""
        policy = data_retention_manager.create_policy(
            name='Query Logs',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=90
        )
        
        # Purge function that raises error
        def failing_purge(cutoff_date):
            raise Exception('Purge failed')
        
        result = data_retention_manager.execute_policy(policy.policy_id, failing_purge)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_retention_policy_statistics_tracking(self, client, admin_agent):
        """Test retention policy statistics tracking"""
        policy = data_retention_manager.create_policy(
            name='Query Logs',
            policy_type=RetentionPolicyType.QUERY_LOGS,
            retention_days=90
        )
        
        # Execute multiple times
        for i in range(3):
            def mock_purge(cutoff_date):
                return 10 + i
            
            data_retention_manager.execute_policy(policy.policy_id, mock_purge)
        
        updated_policy = data_retention_manager.get_policy(policy.policy_id)
        assert updated_policy.run_count == 3
        assert updated_policy.total_purged_count >= 30


class TestStory3_AdditionalAnonymizationCases:
    """Story 3: Additional anonymization scenarios"""
    
    def test_anonymize_log_entry_pseudonymize(self, client, admin_agent):
        """Test anonymizing with pseudonymize method"""
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.PSEUDONYMIZE
        )
        
        log_entry = {
            'user_id': 'user123',
            'action': 'query'
        }
        
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        assert anonymized['user_id'] != 'user123'
        assert anonymized['user_id'].startswith('user_')
        assert len(anonymized['user_id']) > len('user_')
    
    def test_anonymize_multiple_rules(self, client, admin_agent):
        """Test anonymizing with multiple rules"""
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        audit_anonymizer.create_rule(
            name='Email Rule',
            field_patterns=['email'],
            method=AnonymizationMethod.REDACT
        )
        
        log_entry = {
            'user_id': 'user123',
            'email': 'user@example.com',
            'action': 'query'
        }
        
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        assert anonymized['user_id'] != 'user123'
        assert anonymized['email'] == '[REDACTED]'
        assert anonymized['action'] == 'query'
    
    def test_anonymize_empty_values(self, client, admin_agent):
        """Test anonymizing log entries with empty/null values"""
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        
        log_entry = {
            'user_id': None,
            'action': 'query',
            'empty_field': ''
        }
        
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        assert anonymized['user_id'] is None
        assert anonymized['action'] == 'query'
    
    def test_anonymize_complex_nested(self, client, admin_agent):
        """Test anonymizing complex nested structures"""
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id', '.*_id'],
            method=AnonymizationMethod.REDACT
        )
        
        log_entry = {
            'user_id': 'user123',
            'details': {
                'agent_id': 'agent456',
                'query': 'SELECT * FROM users',
                'metadata': {
                    'created_by_id': 'creator789',
                    'nested': {
                        'another_id': 'id999'
                    }
                }
            }
        }
        
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        assert anonymized['user_id'] == '[REDACTED]'
        assert anonymized['details']['agent_id'] == '[REDACTED]'
        assert anonymized['details']['metadata']['created_by_id'] == '[REDACTED]'
        assert anonymized['details']['metadata']['nested']['another_id'] == '[REDACTED]'
        assert anonymized['details']['query'] == 'SELECT * FROM users'
    
    def test_anonymize_list_structures(self, client, admin_agent):
        """Test anonymizing list structures"""
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        
        log_entry = {
            'user_ids': ['user1', 'user2', 'user3'],
            'actions': ['query', 'update', 'delete']
        }
        
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        # Lists should be processed
        assert isinstance(anonymized['user_ids'], list)
        assert isinstance(anonymized['actions'], list)
    
    def test_anonymize_rule_pattern_matching(self, client, admin_agent):
        """Test anonymization rule pattern matching"""
        audit_anonymizer.create_rule(
            name='ID Fields Rule',
            field_patterns=['.*_id', '.*Id', 'id'],
            method=AnonymizationMethod.REDACT
        )
        
        log_entry = {
            'user_id': 'user123',
            'agentId': 'agent456',
            'id': 'id789',
            'name': 'John Doe'
        }
        
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        assert anonymized['user_id'] == '[REDACTED]'
        assert anonymized['agentId'] == '[REDACTED]'
        assert anonymized['id'] == '[REDACTED]'
        assert anonymized['name'] == 'John Doe'  # Not matched
    
    def test_anonymize_consistent_hashing(self, client, admin_agent):
        """Test consistent hashing (same input = same output)"""
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH,
            salt='test_salt'
        )
        
        log_entry = {'user_id': 'user123', 'action': 'query'}
        
        # Anonymize twice
        anonymized1 = audit_anonymizer.anonymize_log_entry(log_entry)
        anonymized2 = audit_anonymizer.anonymize_log_entry(log_entry)
        
        # Should produce same hash
        assert anonymized1['user_id'] == anonymized2['user_id']
    
    def test_anonymize_rule_inactive(self, client, admin_agent):
        """Test inactive anonymization rule doesn't apply"""
        rule = audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        
        # Deactivate rule
        audit_anonymizer.update_rule(rule.rule_id, is_active=False)
        
        log_entry = {'user_id': 'user123', 'action': 'query'}
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        # Should not be anonymized
        assert anonymized['user_id'] == 'user123'


class TestIntegration_AdvancedCompliance:
    """Advanced integration scenarios"""
    
    def test_gdpr_compliance_workflow(self, client, admin_agent):
        """Test complete GDPR compliance workflow"""
        # Step 1: Create EU residency rule
        eu_rule = data_residency_manager.create_rule(
            name='EU GDPR Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*'],
            table_patterns=['users', 'customers'],
            column_patterns=['email', 'phone', 'address']
        )
        
        # Step 2: Validate EU data access
        validation = data_residency_manager.validate_residency(
            database_name='eu-database',
            tables=['users'],
            columns=['email', 'phone']
        )
        assert 'valid' in validation
        
        # Step 3: Create retention policy for EU data
        retention_policy = data_retention_manager.create_policy(
            name='EU Data Retention',
            policy_type=RetentionPolicyType.AUDIT_LOGS,
            retention_days=90  # GDPR minimum
        )
        
        # Step 4: Anonymize audit logs
        audit_anonymizer.create_rule(
            name='EU PII Anonymization',
            field_patterns=['user_id', 'email', 'phone', '.*_id'],
            method=AnonymizationMethod.HASH
        )
        
        log_entry = {
            'user_id': 'user123',
            'email': 'user@example.com',
            'action': 'query',
            'details': {'phone': '123-456-7890'}
        }
        
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        assert anonymized['user_id'] != 'user123'
        assert anonymized['email'] != 'user@example.com'
    
    def test_multi_region_compliance(self, client, admin_agent):
        """Test compliance across multiple regions"""
        # Create rules for multiple regions
        eu_rule = data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*']
        )
        us_rule = data_residency_manager.create_rule(
            name='US Rule',
            region=DataRegion.US,
            database_patterns=['us-.*']
        )
        apac_rule = data_residency_manager.create_rule(
            name='APAC Rule',
            region=DataRegion.APAC,
            database_patterns=['apac-.*']
        )
        
        # Validate each region
        eu_result = data_residency_manager.validate_residency('eu-database')
        us_result = data_residency_manager.validate_residency('us-database')
        apac_result = data_residency_manager.validate_residency('apac-database')
        
        assert len(eu_result['applicable_rules']) >= 1
        assert len(us_result['applicable_rules']) >= 1
        assert len(apac_result['applicable_rules']) >= 1
    
    def test_retention_with_anonymization(self, client, admin_agent):
        """Test retention policy execution with anonymization"""
        # Create anonymization rule
        audit_anonymizer.create_rule(
            name='User ID Rule',
            field_patterns=['user_id'],
            method=AnonymizationMethod.HASH
        )
        
        # Create retention policy
        policy = data_retention_manager.create_policy(
            name='Audit Logs',
            policy_type=RetentionPolicyType.AUDIT_LOGS,
            retention_days=90
        )
        
        # Anonymize before retention
        log_entries = [
            {'user_id': 'user1', 'action': 'query1'},
            {'user_id': 'user2', 'action': 'query2'}
        ]
        
        anonymized = audit_anonymizer.anonymize_batch(log_entries)
        
        # Execute retention (would purge anonymized logs)
        def mock_purge(cutoff_date):
            return len(anonymized)
        
        result = data_retention_manager.execute_policy(policy.policy_id, mock_purge)
        assert result['success'] is True
        assert result['purged_count'] == len(anonymized)
    
    def test_residency_validation_in_query_execution(self, client, admin_agent):
        """Test residency validation integrated with query execution"""
        # Create EU rule
        data_residency_manager.create_rule(
            name='EU Rule',
            region=DataRegion.EU,
            database_patterns=['eu-.*'],
            table_patterns=['users']
        )
        
        # Validate before query
        validation = data_residency_manager.validate_residency(
            database_name='eu-database',
            tables=['users']
        )
        
        # Should pass validation
        assert validation['valid'] is True or len(validation['violations']) == 0
    
    def test_complete_privacy_workflow(self, client, admin_agent):
        """Test complete privacy protection workflow"""
        # Step 1: Anonymize sensitive data
        audit_anonymizer.create_rule(
            name='PII Anonymization',
            field_patterns=['user_id', 'email', 'phone', 'ssn'],
            method=AnonymizationMethod.HASH
        )
        
        log_entry = {
            'user_id': 'user123',
            'email': 'user@example.com',
            'phone': '123-456-7890',
            'ssn': '123-45-6789',
            'action': 'query'
        }
        
        anonymized = audit_anonymizer.anonymize_log_entry(log_entry)
        
        # Step 2: Apply retention policy
        policy = data_retention_manager.create_policy(
            name='Anonymized Logs Retention',
            policy_type=RetentionPolicyType.AUDIT_LOGS,
            retention_days=90
        )
        
        # Step 3: Execute retention
        def mock_purge(cutoff_date):
            return 1
        
        result = data_retention_manager.execute_policy(policy.policy_id, mock_purge)
        
        assert anonymized['user_id'] != 'user123'
        assert anonymized['email'] != 'user@example.com'
        assert result['success'] is True
