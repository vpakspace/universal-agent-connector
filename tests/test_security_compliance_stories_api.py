"""
API endpoint tests for Security and Compliance Stories
Tests the REST API endpoints for all five security/compliance stories
Following the pattern of test_admin_database_stories_api.py
"""

import pytest
from unittest.mock import MagicMock, patch
from main import create_app
from ai_agent_connector.app.api.routes import (
    agent_registry, access_control, rls_manager, column_masker,
    query_validator, approval_manager, audit_exporter, audit_logger
)
from ai_agent_connector.app.permissions import Permission
from ai_agent_connector.app.utils.encryption import reset_encryptor
from ai_agent_connector.app.utils.row_level_security import RLSRule, RLSRuleType
from ai_agent_connector.app.utils.column_masking import MaskingRule, MaskingType
from ai_agent_connector.app.utils.query_validator import ComplexityLimits, RiskLevel, ValidationResult
from ai_agent_connector.app.utils.query_approval import QueryApproval, ApprovalStatus
from ai_agent_connector.app.utils.audit_logger import ActionType


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    # Clear security managers
    rls_manager._rules.clear()
    rls_manager._global_rules.clear()
    column_masker._rules.clear()
    column_masker._global_rules.clear()
    query_validator._limits.clear()
    approval_manager._approvals.clear()
    approval_manager._agent_approvals.clear()
    audit_logger.clear_logs()
    yield
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    rls_manager._rules.clear()
    rls_manager._global_rules.clear()
    column_masker._rules.clear()
    column_masker._global_rules.clear()
    query_validator._limits.clear()
    approval_manager._approvals.clear()
    approval_manager._agent_approvals.clear()
    audit_logger.clear_logs()


@pytest.fixture
def client():
    """Create test client"""
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def admin_agent():
    """Create an admin agent for testing"""
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
    return {'agent_id': 'test-agent', 'api_key': result['api_key']}


class TestStory1_API_RLSRules:
    """Story 1: Row-Level Security (RLS) Rules - API Tests"""
    
    def test_create_rls_rule_success(self, client, admin_agent):
        """Test creating an RLS rule successfully"""
        payload = {
            'agent_id': 'test-agent',
            'table_name': 'users',
            'condition': 'user_id = current_user()',
            'rule_type': 'custom',
            'description': 'Users can only see their own data',
            'enabled': True
        }
        
        response = client.post(
            '/api/admin/rls/rules',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'rule' in data
        assert data['rule']['table_name'] == 'users'
        assert data['rule']['condition'] == 'user_id = current_user()'
        assert data['rule']['enabled'] is True
    
    def test_create_rls_rule_missing_fields(self, client, admin_agent):
        """Test creating RLS rule with missing required fields"""
        payload = {
            'agent_id': 'test-agent'
            # Missing table_name and condition
        }
        
        response = client.post(
            '/api/admin/rls/rules',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 400
    
    def test_list_rls_rules(self, client, admin_agent):
        """Test listing RLS rules"""
        # Create a rule first
        rule = RLSRule(
            rule_id='rule-1',
            agent_id='test-agent',
            table_name='users',
            condition='user_id = current_user()'
        )
        rls_manager.add_rule(rule)
        
        response = client.get(
            '/api/admin/rls/rules?agent_id=test-agent',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'rules' in data
        assert len(data['rules']) >= 1
        assert data['rules'][0]['table_name'] == 'users'
    
    def test_delete_rls_rule(self, client, admin_agent):
        """Test deleting an RLS rule"""
        # Create a rule first
        rule = RLSRule(
            rule_id='rule-to-delete',
            agent_id='test-agent',
            table_name='users',
            condition='user_id = current_user()'
        )
        rls_manager.add_rule(rule)
        
        response = client.delete(
            '/api/admin/rls/rules/rule-to-delete?agent_id=test-agent&table_name=users',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        
        # Verify rule is deleted
        rules = rls_manager.get_rules('test-agent', 'users')
        assert len([r for r in rules if r.rule_id == 'rule-to-delete']) == 0
    
    def test_rls_rule_applies_to_query(self, client, admin_agent):
        """Test that RLS rule modifies query"""
        # Create a rule
        rule = RLSRule(
            rule_id='rule-1',
            agent_id='test-agent',
            table_name='users',
            condition='user_id = current_user()'
        )
        rls_manager.add_rule(rule)
        
        original_query = "SELECT * FROM users"
        modified_query = rls_manager.apply_rls_to_query('test-agent', original_query, 'users')
        
        assert 'WHERE' in modified_query.upper()
        assert 'user_id = current_user()' in modified_query


class TestStory2_API_ColumnMasking:
    """Story 2: Column Masking for PII - API Tests"""
    
    def test_create_masking_rule_full(self, client, admin_agent):
        """Test creating a full masking rule"""
        payload = {
            'agent_id': 'test-agent',
            'table_name': 'users',
            'column_name': 'ssn',
            'masking_type': 'full',
            'mask_value': '***',
            'description': 'Mask SSN completely'
        }
        
        response = client.post(
            '/api/admin/masking/rules',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'rule' in data
        assert data['rule']['column_name'] == 'ssn'
        assert data['rule']['masking_type'] == 'full'
    
    def test_create_masking_rule_partial(self, client, admin_agent):
        """Test creating a partial masking rule"""
        payload = {
            'table_name': 'credit_cards',
            'column_name': 'card_number',
            'masking_type': 'partial',
            'show_first': 0,
            'show_last': 4,
            'mask_value': '****'
        }
        
        response = client.post(
            '/api/admin/masking/rules',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['rule']['masking_type'] == 'partial'
        assert data['rule']['show_last'] == 4
    
    def test_create_masking_rule_hash(self, client, admin_agent):
        """Test creating a hash masking rule"""
        payload = {
            'table_name': 'users',
            'column_name': 'email',
            'masking_type': 'hash',
            'hash_algorithm': 'sha256'
        }
        
        response = client.post(
            '/api/admin/masking/rules',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['rule']['masking_type'] == 'hash'
    
    def test_list_masking_rules(self, client, admin_agent):
        """Test listing masking rules"""
        # Create a rule first
        rule = MaskingRule(
            rule_id='mask-1',
            agent_id='test-agent',
            table_name='users',
            column_name='ssn',
            masking_type=MaskingType.FULL
        )
        column_masker.add_rule(rule)
        
        response = client.get(
            '/api/admin/masking/rules',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'agent_rules' in data or 'global_rules' in data
    
    def test_delete_masking_rule(self, client, admin_agent):
        """Test deleting a masking rule"""
        # Create a rule first
        rule = MaskingRule(
            rule_id='mask-to-delete',
            agent_id='test-agent',
            table_name='users',
            column_name='ssn',
            masking_type=MaskingType.FULL
        )
        column_masker.add_rule(rule)
        
        response = client.delete(
            '/api/admin/masking/rules?agent_id=test-agent&table_name=users&column_name=ssn',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify rule is deleted
        rule_check = column_masker.get_rule('test-agent', 'users', 'ssn')
        assert rule_check is None
    
    def test_mask_result_row(self, client, admin_agent):
        """Test masking a result row"""
        # Create a masking rule
        rule = MaskingRule(
            rule_id='mask-1',
            agent_id='test-agent',
            table_name='users',
            column_name='ssn',
            masking_type=MaskingType.FULL,
            mask_value='***'
        )
        column_masker.add_rule(rule)
        
        # Test masking
        row = {'id': 1, 'name': 'John', 'ssn': '123-45-6789'}
        masked_row = column_masker.mask_result_row('test-agent', 'users', row)
        
        assert masked_row['ssn'] == '***'
        assert masked_row['id'] == 1  # Other columns unchanged
        assert masked_row['name'] == 'John'


class TestStory3_API_QueryComplexityLimits:
    """Story 3: Query Complexity Limits - API Tests"""
    
    def test_set_query_limits(self, client, admin_agent):
        """Test setting query complexity limits"""
        payload = {
            'max_join_depth': 3,
            'max_tables': 5,
            'max_subquery_depth': 2,
            'allow_delete': False,
            'allow_drop': False,
            'max_result_rows': 1000
        }
        
        response = client.post(
            '/api/admin/agents/test-agent/query-limits',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['limits']['max_join_depth'] == 3
        assert data['limits']['allow_delete'] is False
        assert data['limits']['max_result_rows'] == 1000
    
    def test_get_query_limits(self, client, admin_agent):
        """Test getting query complexity limits"""
        # Set limits first
        limits = ComplexityLimits(
            max_join_depth=3,
            max_tables=5,
            allow_delete=False
        )
        query_validator.set_limits('test-agent', limits)
        
        response = client.get(
            '/api/admin/agents/test-agent/query-limits',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['limits']['max_join_depth'] == 3
        assert data['limits']['allow_delete'] is False
    
    def test_validate_query_safe(self, client, admin_agent):
        """Test validating a safe query"""
        payload = {'query': 'SELECT * FROM users LIMIT 10'}
        
        response = client.post(
            '/api/admin/agents/test-agent/validate-query',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'is_valid' in data
        assert 'risk_level' in data
        assert 'complexity_score' in data
    
    def test_validate_query_dangerous(self, client, admin_agent):
        """Test validating a dangerous query"""
        # Set limits to disallow DELETE
        limits = ComplexityLimits(allow_delete=False)
        query_validator.set_limits('test-agent', limits)
        
        payload = {'query': 'DELETE FROM users'}
        
        response = client.post(
            '/api/admin/agents/test-agent/validate-query',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['is_valid'] is False
        assert 'DELETE operations are not allowed' in str(data.get('errors', []))
    
    def test_validate_query_complex(self, client, admin_agent):
        """Test validating a complex query"""
        # Set limits
        limits = ComplexityLimits(max_join_depth=3)
        query_validator.set_limits('test-agent', limits)
        
        payload = {'query': 'SELECT * FROM a JOIN b JOIN c JOIN d JOIN e'}
        
        response = client.post(
            '/api/admin/agents/test-agent/validate-query',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        # Query should be invalid or require approval due to complexity
        assert data['is_valid'] is False or data.get('requires_approval') is True


class TestStory4_API_QueryApproval:
    """Story 4: Manual Query Approval - API Tests"""
    
    def test_list_pending_approvals(self, client, admin_agent):
        """Test listing pending approvals"""
        # Create a pending approval
        from ai_agent_connector.app.utils.query_validator import ValidationResult
        
        validation_result = ValidationResult(
            is_valid=False,
            risk_level=RiskLevel.CRITICAL,
            requires_approval=True
        )
        
        approval = approval_manager.request_approval(
            agent_id='test-agent',
            query='DELETE FROM users',
            query_type='DELETE',
            validation_result=validation_result,
            requested_by='test-agent'
        )
        
        response = client.get(
            '/api/admin/query-approvals',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'approvals' in data
        assert len(data['approvals']) >= 1
        assert data['approvals'][0]['status'] == 'pending'
    
    def test_approve_query(self, client, admin_agent):
        """Test approving a query"""
        # Create a pending approval
        from ai_agent_connector.app.utils.query_validator import ValidationResult
        
        validation_result = ValidationResult(
            is_valid=False,
            risk_level=RiskLevel.CRITICAL,
            requires_approval=True
        )
        
        approval = approval_manager.request_approval(
            agent_id='test-agent',
            query='DELETE FROM users',
            query_type='DELETE',
            validation_result=validation_result,
            requested_by='test-agent'
        )
        
        payload = {'max_executions': 1}
        
        response = client.post(
            f'/api/admin/query-approvals/{approval.approval_id}/approve',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['approval']['status'] == 'approved'
        assert data['approval']['approved_by'] == 'admin-agent'
    
    def test_reject_query(self, client, admin_agent):
        """Test rejecting a query"""
        # Create a pending approval
        from ai_agent_connector.app.utils.query_validator import ValidationResult
        
        validation_result = ValidationResult(
            is_valid=False,
            risk_level=RiskLevel.CRITICAL,
            requires_approval=True
        )
        
        approval = approval_manager.request_approval(
            agent_id='test-agent',
            query='DELETE FROM users',
            query_type='DELETE',
            validation_result=validation_result,
            requested_by='test-agent'
        )
        
        payload = {'reason': 'Query is too risky'}
        
        response = client.post(
            f'/api/admin/query-approvals/{approval.approval_id}/reject',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['approval']['status'] == 'rejected'
        assert data['approval']['rejection_reason'] == 'Query is too risky'
    
    def test_get_approval(self, client, admin_agent):
        """Test getting a specific approval"""
        # Create an approval
        from ai_agent_connector.app.utils.query_validator import ValidationResult
        
        validation_result = ValidationResult(
            is_valid=False,
            risk_level=RiskLevel.CRITICAL,
            requires_approval=True
        )
        
        approval = approval_manager.request_approval(
            agent_id='test-agent',
            query='DELETE FROM users',
            query_type='DELETE',
            validation_result=validation_result,
            requested_by='test-agent'
        )
        
        response = client.get(
            f'/api/admin/query-approvals/{approval.approval_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['approval_id'] == approval.approval_id
        assert data['query'] == 'DELETE FROM users'
        assert data['status'] == 'pending'


class TestStory5_API_AuditLogExport:
    """Story 5: Audit Log Export - API Tests"""
    
    def test_export_audit_logs_csv(self, client, admin_agent):
        """Test exporting audit logs as CSV"""
        # Create some audit logs
        audit_logger.log(
            action_type=ActionType.QUERY_EXECUTION,
            agent_id='test-agent',
            status='success'
        )
        audit_logger.log(
            action_type=ActionType.AGENT_REGISTERED,
            agent_id='test-agent',
            status='success'
        )
        
        response = client.get(
            '/api/admin/audit/export?format=csv',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv'
        assert b'id' in response.data or b'timestamp' in response.data
    
    def test_export_audit_logs_json(self, client, admin_agent):
        """Test exporting audit logs as JSON"""
        # Create some audit logs
        audit_logger.log(
            action_type=ActionType.QUERY_EXECUTION,
            agent_id='test-agent',
            status='success'
        )
        
        response = client.get(
            '/api/admin/audit/export?format=json',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        # Response might be a file download, so check headers
        assert 'attachment' in response.headers.get('Content-Disposition', '') or response.is_json
    
    def test_export_audit_logs_with_filters(self, client, admin_agent):
        """Test exporting audit logs with filters"""
        # Create audit logs for different agents
        audit_logger.log(
            action_type=ActionType.QUERY_EXECUTION,
            agent_id='test-agent',
            status='success'
        )
        audit_logger.log(
            action_type=ActionType.QUERY_EXECUTION,
            agent_id='other-agent',
            status='success'
        )
        
        response = client.get(
            '/api/admin/audit/export?format=csv&agent_id=test-agent',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv'
    
    def test_export_audit_summary_csv(self, client, admin_agent):
        """Test exporting audit summary as CSV"""
        # Create some audit logs
        audit_logger.log(
            action_type=ActionType.QUERY_EXECUTION,
            agent_id='test-agent',
            status='success'
        )
        audit_logger.log(
            action_type=ActionType.QUERY_EXECUTION,
            agent_id='test-agent',
            status='error',
            error_message='Query failed'
        )
        
        response = client.get(
            '/api/admin/audit/export/summary?format=csv',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv'
        assert b'Total Records' in response.data or b'Metric' in response.data
    
    def test_export_audit_summary_json(self, client, admin_agent):
        """Test exporting audit summary as JSON"""
        # Create some audit logs
        audit_logger.log(
            action_type=ActionType.QUERY_EXECUTION,
            agent_id='test-agent',
            status='success'
        )
        
        response = client.get(
            '/api/admin/audit/export/summary?format=json',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
    
    def test_export_invalid_format(self, client, admin_agent):
        """Test exporting with invalid format"""
        response = client.get(
            '/api/admin/audit/export?format=xml',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestIntegration_AllSecurityFeatures:
    """Integration tests combining all security features"""
    
    def test_complete_security_workflow(self, client, admin_agent):
        """Test complete security workflow: RLS + Masking + Validation + Approval"""
        # Step 1: Create RLS rule
        rls_payload = {
            'agent_id': 'test-agent',
            'table_name': 'users',
            'condition': 'user_id = current_user()',
            'rule_type': 'custom'
        }
        response = client.post(
            '/api/admin/rls/rules',
            json=rls_payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        assert response.status_code == 201
        
        # Step 2: Create masking rule
        masking_payload = {
            'agent_id': 'test-agent',
            'table_name': 'users',
            'column_name': 'ssn',
            'masking_type': 'full'
        }
        response = client.post(
            '/api/admin/masking/rules',
            json=masking_payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        assert response.status_code == 201
        
        # Step 3: Set query limits
        limits_payload = {
            'max_join_depth': 3,
            'allow_delete': False
        }
        response = client.post(
            '/api/admin/agents/test-agent/query-limits',
            json=limits_payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        assert response.status_code == 200
        
        # Step 4: Validate dangerous query
        query_payload = {'query': 'DELETE FROM users'}
        response = client.post(
            '/api/admin/agents/test-agent/validate-query',
            json=query_payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['is_valid'] is False or data.get('requires_approval') is True
        
        # Step 5: Request approval (if needed)
        if data.get('requires_approval'):
            from ai_agent_connector.app.utils.query_validator import ValidationResult
            validation_result = ValidationResult(
                is_valid=False,
                risk_level=RiskLevel.CRITICAL,
                requires_approval=True
            )
            approval = approval_manager.request_approval(
                agent_id='test-agent',
                query='DELETE FROM users',
                query_type='DELETE',
                validation_result=validation_result
            )
            assert approval.status == ApprovalStatus.PENDING
            
            # Step 6: Approve query
            response = client.post(
                f'/api/admin/query-approvals/{approval.approval_id}/approve',
                json={'max_executions': 1},
                headers={'X-API-Key': admin_agent['api_key']}
            )
            assert response.status_code == 200
        
        # Step 7: Export audit logs
        response = client.get(
            '/api/admin/audit/export?format=json',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        assert response.status_code == 200

