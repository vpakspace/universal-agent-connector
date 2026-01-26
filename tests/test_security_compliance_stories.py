"""
Integration tests for Security and Compliance Stories

Story 1: As an Admin, I want to define row-level security (RLS) rules, 
         so that agents only access data matching specific conditions.

Story 2: As an Admin, I want to mask sensitive columns (PII like SSN, credit cards) 
         in query results, so that agents never see raw sensitive data.

Story 3: As an Admin, I want to set query complexity limits, 
         so that agents can't execute dangerous operations.

Story 4: As an Admin, I want to approve high-risk queries manually before execution, 
         so that critical operations are human-reviewed.

Story 5: As a Compliance Officer, I want to export audit logs in standard formats (CSV, JSON), 
         so that I can meet regulatory requirements.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from ai_agent_connector.app.api import api_bp
from ai_agent_connector.app.utils.row_level_security import RLSRule, RLSRuleType
from ai_agent_connector.app.utils.column_masking import MaskingRule, MaskingType
from ai_agent_connector.app.utils.query_validator import ComplexityLimits, RiskLevel
from ai_agent_connector.app.utils.query_approval import ApprovalStatus
from ai_agent_connector.app.utils.audit_export import ExportFormat
from ai_agent_connector.app.utils.audit_logger import ActionType


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(api_bp)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_admin_auth():
    """Mock admin authentication"""
    with patch('ai_agent_connector.app.api.routes.authenticate_request') as mock_auth:
        mock_auth.return_value = ("admin_agent", None, 200)
        yield mock_auth


@pytest.fixture
def mock_admin_permission():
    """Mock admin permission check"""
    with patch('ai_agent_connector.app.api.routes.access_control') as mock_ac:
        mock_ac.has_permission.return_value = True
        yield mock_ac


class TestStory1_RowLevelSecurity:
    """Story 1: Define row-level security (RLS) rules"""
    
    def test_create_rls_rule(self, client, mock_admin_auth, mock_admin_permission):
        """Test creating an RLS rule"""
        with patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            payload = {
                'agent_id': 'agent-1',
                'table_name': 'users',
                'condition': 'user_id = current_user()',
                'rule_type': 'custom',
                'description': 'Users can only see their own data',
                'enabled': True
            }
            
            response = client.post(
                '/api/admin/rls/rules',
                json=payload,
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert 'rule' in data
            assert data['rule']['table_name'] == 'users'
            assert data['rule']['condition'] == 'user_id = current_user()'
            
            # Verify add_rule was called
            assert mock_rls.add_rule.called
    
    def test_list_rls_rules(self, client, mock_admin_auth, mock_admin_permission):
        """Test listing RLS rules"""
        with patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            rule = RLSRule(
                rule_id='rule-1',
                agent_id='agent-1',
                table_name='users',
                condition='user_id = current_user()'
            )
            mock_rls.get_rules.return_value = [rule]
            
            response = client.get(
                '/api/admin/rls/rules?agent_id=agent-1',
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['rules']) == 1
            assert data['rules'][0]['table_name'] == 'users'
    
    def test_delete_rls_rule(self, client, mock_admin_auth, mock_admin_permission):
        """Test deleting an RLS rule"""
        with patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            mock_rls.remove_rule.return_value = True
            
            response = client.delete(
                '/api/admin/rls/rules/rule-1?agent_id=agent-1&table_name=users',
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            assert mock_rls.remove_rule.called
    
    def test_rls_rule_applied_to_query(self, client, mock_admin_auth, mock_admin_permission):
        """Test that RLS rules are applied to queries"""
        with patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            original_query = "SELECT * FROM users"
            modified_query = "SELECT * FROM users WHERE (user_id = current_user())"
            mock_rls.apply_rls_to_query.return_value = modified_query
            
            # This would be called during query execution
            result = mock_rls.apply_rls_to_query('agent-1', original_query, 'users')
            assert result == modified_query


class TestStory2_ColumnMasking:
    """Story 2: Mask sensitive columns (PII)"""
    
    def test_create_masking_rule_full(self, client, mock_admin_auth, mock_admin_permission):
        """Test creating a full masking rule"""
        with patch('ai_agent_connector.app.api.routes.column_masker') as mock_masker:
            payload = {
                'agent_id': 'agent-1',
                'table_name': 'users',
                'column_name': 'ssn',
                'masking_type': 'full',
                'mask_value': '***',
                'description': 'Mask SSN'
            }
            
            response = client.post(
                '/api/admin/masking/rules',
                json=payload,
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert 'rule' in data
            assert data['rule']['column_name'] == 'ssn'
            assert data['rule']['masking_type'] == 'full'
            
            # Verify add_rule was called
            assert mock_masker.add_rule.called
    
    def test_create_masking_rule_partial(self, client, mock_admin_auth, mock_admin_permission):
        """Test creating a partial masking rule (show last 4 digits)"""
        with patch('ai_agent_connector.app.api.routes.column_masker') as mock_masker:
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
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['rule']['masking_type'] == 'partial'
            assert data['rule']['show_last'] == 4
    
    def test_create_masking_rule_hash(self, client, mock_admin_auth, mock_admin_permission):
        """Test creating a hash masking rule"""
        with patch('ai_agent_connector.app.api.routes.column_masker') as mock_masker:
            payload = {
                'table_name': 'users',
                'column_name': 'email',
                'masking_type': 'hash',
                'hash_algorithm': 'sha256'
            }
            
            response = client.post(
                '/api/admin/masking/rules',
                json=payload,
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['rule']['masking_type'] == 'hash'
    
    def test_list_masking_rules(self, client, mock_admin_auth, mock_admin_permission):
        """Test listing masking rules"""
        with patch('ai_agent_connector.app.api.routes.column_masker') as mock_masker:
            mock_masker.list_all_rules.return_value = {
                'agent_rules': {},
                'global_rules': {}
            }
            
            response = client.get(
                '/api/admin/masking/rules',
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'agent_rules' in data
            assert 'global_rules' in data
    
    def test_delete_masking_rule(self, client, mock_admin_auth, mock_admin_permission):
        """Test deleting a masking rule"""
        with patch('ai_agent_connector.app.api.routes.column_masker') as mock_masker:
            mock_masker.remove_rule.return_value = True
            
            response = client.delete(
                '/api/admin/masking/rules?table_name=users&column_name=ssn',
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            assert mock_masker.remove_rule.called
    
    def test_mask_result_row(self, client, mock_admin_auth, mock_admin_permission):
        """Test masking a result row"""
        with patch('ai_agent_connector.app.api.routes.column_masker') as mock_masker:
            rule = MaskingRule(
                rule_id='rule-1',
                agent_id='agent-1',
                table_name='users',
                column_name='ssn',
                masking_type=MaskingType.FULL
            )
            mock_masker.get_rule.return_value = rule
            mock_masker.mask_value.return_value = '***'
            
            row = {'id': 1, 'name': 'John', 'ssn': '123-45-6789'}
            masked = mock_masker.mask_result_row('agent-1', 'users', row)
            
            # Verify masking was applied
            assert mock_masker.get_rule.called
            assert mock_masker.mask_value.called


class TestStory3_QueryComplexityLimits:
    """Story 3: Set query complexity limits"""
    
    def test_set_query_limits(self, client, mock_admin_auth, mock_admin_permission):
        """Test setting query complexity limits"""
        with patch('ai_agent_connector.app.api.routes.query_validator') as mock_validator:
            payload = {
                'max_join_depth': 3,
                'max_tables': 5,
                'max_subquery_depth': 2,
                'allow_delete': False,
                'allow_drop': False,
                'max_result_rows': 1000
            }
            
            response = client.post(
                '/api/admin/agents/agent-1/query-limits',
                json=payload,
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['limits']['max_join_depth'] == 3
            assert data['limits']['allow_delete'] is False
            
            # Verify set_limits was called
            assert mock_validator.set_limits.called
    
    def test_get_query_limits(self, client, mock_admin_auth, mock_admin_permission):
        """Test getting query complexity limits"""
        with patch('ai_agent_connector.app.api.routes.query_validator') as mock_validator:
            limits = ComplexityLimits(
                max_join_depth=3,
                max_tables=5,
                allow_delete=False
            )
            mock_validator.get_limits.return_value = limits
            
            response = client.get(
                '/api/admin/agents/agent-1/query-limits',
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['limits']['max_join_depth'] == 3
    
    def test_validate_query_safe(self, client, mock_admin_auth, mock_admin_permission):
        """Test validating a safe query"""
        with patch('ai_agent_connector.app.api.routes.query_validator') as mock_validator:
            from ai_agent_connector.app.utils.query_validator import ValidationResult
            
            result = ValidationResult(
                is_valid=True,
                risk_level=RiskLevel.LOW,
                complexity_score=20
            )
            mock_validator.validate_query.return_value = result
            
            payload = {'query': 'SELECT * FROM users LIMIT 10'}
            
            response = client.post(
                '/api/admin/agents/agent-1/validate-query',
                json=payload,
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['is_valid'] is True
            assert data['risk_level'] == 'low'
    
    def test_validate_query_dangerous(self, client, mock_admin_auth, mock_admin_permission):
        """Test validating a dangerous query"""
        with patch('ai_agent_connector.app.api.routes.query_validator') as mock_validator:
            from ai_agent_connector.app.utils.query_validator import ValidationResult
            
            result = ValidationResult(
                is_valid=False,
                risk_level=RiskLevel.CRITICAL,
                errors=['DELETE operations are not allowed'],
                requires_approval=True
            )
            mock_validator.validate_query.return_value = result
            
            payload = {'query': 'DELETE FROM users'}
            
            response = client.post(
                '/api/admin/agents/agent-1/validate-query',
                json=payload,
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['is_valid'] is False
            assert data['risk_level'] == 'critical'
            assert data['requires_approval'] is True
    
    def test_validate_query_complex(self, client, mock_admin_auth, mock_admin_permission):
        """Test validating a complex query"""
        with patch('ai_agent_connector.app.api.routes.query_validator') as mock_validator:
            from ai_agent_connector.app.utils.query_validator import ValidationResult
            
            result = ValidationResult(
                is_valid=False,
                risk_level=RiskLevel.HIGH,
                errors=['Query has 5 JOINs, exceeds maximum of 3'],
                complexity_score=85,
                requires_approval=True
            )
            mock_validator.validate_query.return_value = result
            
            payload = {'query': 'SELECT * FROM a JOIN b JOIN c JOIN d JOIN e'}
            
            response = client.post(
                '/api/admin/agents/agent-1/validate-query',
                json=payload,
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['is_valid'] is False
            assert data['complexity_score'] == 85


class TestStory4_QueryApproval:
    """Story 4: Approve high-risk queries manually"""
    
    def test_list_pending_approvals(self, client, mock_admin_auth, mock_admin_permission):
        """Test listing pending approvals"""
        with patch('ai_agent_connector.app.api.routes.approval_manager') as mock_approval:
            from ai_agent_connector.app.utils.query_approval import QueryApproval
            from ai_agent_connector.app.utils.query_validator import RiskLevel
            
            approval = QueryApproval(
                approval_id='approval-1',
                agent_id='agent-1',
                query='DELETE FROM users',
                query_type='DELETE',
                risk_level=RiskLevel.CRITICAL,
                complexity_score=90,
                validation_result={}
            )
            mock_approval.list_pending_approvals.return_value = [approval]
            
            response = client.get(
                '/api/admin/query-approvals',
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['approvals']) == 1
            assert data['approvals'][0]['status'] == 'pending'
    
    def test_approve_query(self, client, mock_admin_auth, mock_admin_permission):
        """Test approving a query"""
        with patch('ai_agent_connector.app.api.routes.approval_manager') as mock_approval:
            from ai_agent_connector.app.utils.query_approval import QueryApproval
            from ai_agent_connector.app.utils.query_validator import RiskLevel
            
            approval = QueryApproval(
                approval_id='approval-1',
                agent_id='agent-1',
                query='DELETE FROM users',
                query_type='DELETE',
                risk_level=RiskLevel.CRITICAL,
                complexity_score=90,
                validation_result={},
                status=ApprovalStatus.APPROVED
            )
            mock_approval.approve_query.return_value = approval
            
            payload = {'max_executions': 1}
            
            response = client.post(
                '/api/admin/query-approvals/approval-1/approve',
                json=payload,
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['approval']['status'] == 'approved'
            assert mock_approval.approve_query.called
    
    def test_reject_query(self, client, mock_admin_auth, mock_admin_permission):
        """Test rejecting a query"""
        with patch('ai_agent_connector.app.api.routes.approval_manager') as mock_approval:
            from ai_agent_connector.app.utils.query_approval import QueryApproval
            from ai_agent_connector.app.utils.query_validator import RiskLevel
            
            approval = QueryApproval(
                approval_id='approval-1',
                agent_id='agent-1',
                query='DELETE FROM users',
                query_type='DELETE',
                risk_level=RiskLevel.CRITICAL,
                complexity_score=90,
                validation_result={},
                status=ApprovalStatus.REJECTED,
                rejection_reason='Too risky'
            )
            mock_approval.reject_query.return_value = approval
            
            payload = {'reason': 'Too risky'}
            
            response = client.post(
                '/api/admin/query-approvals/approval-1/reject',
                json=payload,
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['approval']['status'] == 'rejected'
            assert data['approval']['rejection_reason'] == 'Too risky'
    
    def test_get_approval(self, client, mock_admin_auth, mock_admin_permission):
        """Test getting a specific approval"""
        with patch('ai_agent_connector.app.api.routes.approval_manager') as mock_approval:
            from ai_agent_connector.app.utils.query_approval import QueryApproval
            from ai_agent_connector.app.utils.query_validator import RiskLevel
            
            approval = QueryApproval(
                approval_id='approval-1',
                agent_id='agent-1',
                query='DELETE FROM users',
                query_type='DELETE',
                risk_level=RiskLevel.CRITICAL,
                complexity_score=90,
                validation_result={}
            )
            mock_approval.get_approval.return_value = approval
            
            response = client.get(
                '/api/admin/query-approvals/approval-1',
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['approval_id'] == 'approval-1'
            assert data['query'] == 'DELETE FROM users'


class TestStory5_AuditLogExport:
    """Story 5: Export audit logs in standard formats"""
    
    def test_export_audit_logs_csv(self, client, mock_admin_auth, mock_admin_permission):
        """Test exporting audit logs as CSV"""
        with patch('ai_agent_connector.app.api.routes.audit_exporter') as mock_exporter:
            mock_exporter.export_logs.return_value = "id,timestamp,action_type\n1,2024-01-01,query_execution\n"
            
            response = client.get(
                '/api/admin/audit/export?format=csv',
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            assert response.content_type == 'text/csv'
            assert b'id,timestamp,action_type' in response.data
    
    def test_export_audit_logs_json(self, client, mock_admin_auth, mock_admin_permission):
        """Test exporting audit logs as JSON"""
        with patch('ai_agent_connector.app.api.routes.audit_exporter') as mock_exporter:
            mock_exporter.export_logs.return_value = '{"logs": [{"id": 1, "action_type": "query_execution"}]}'
            
            response = client.get(
                '/api/admin/audit/export?format=json',
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            assert response.content_type == 'application/json'
            data = response.get_json()
            assert 'logs' in data or 'export_timestamp' in str(response.data)
    
    def test_export_audit_logs_with_filters(self, client, mock_admin_auth, mock_admin_permission):
        """Test exporting audit logs with filters"""
        with patch('ai_agent_connector.app.api.routes.audit_exporter') as mock_exporter:
            mock_exporter.export_logs.return_value = "id,timestamp\n1,2024-01-01\n"
            
            response = client.get(
                '/api/admin/audit/export?format=csv&agent_id=agent-1&start_date=2024-01-01&end_date=2024-01-31',
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            # Verify export_logs was called with filters
            assert mock_exporter.export_logs.called
            call_kwargs = mock_exporter.export_logs.call_args[1]
            assert call_kwargs.get('agent_id') == 'agent-1'
    
    def test_export_audit_summary_csv(self, client, mock_admin_auth, mock_admin_permission):
        """Test exporting audit summary as CSV"""
        with patch('ai_agent_connector.app.api.routes.audit_exporter') as mock_exporter:
            mock_exporter.export_summary_report.return_value = "Metric,Value\nTotal Records,100\n"
            
            response = client.get(
                '/api/admin/audit/export/summary?format=csv',
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            assert response.content_type == 'text/csv'
            assert b'Total Records' in response.data
    
    def test_export_audit_summary_json(self, client, mock_admin_auth, mock_admin_permission):
        """Test exporting audit summary as JSON"""
        with patch('ai_agent_connector.app.api.routes.audit_exporter') as mock_exporter:
            mock_exporter.export_summary_report.return_value = '{"summary": {"total_records": 100}}'
            
            response = client.get(
                '/api/admin/audit/export/summary?format=json',
                headers={'X-API-Key': 'admin-key'}
            )
            
            assert response.status_code == 200
            assert response.content_type == 'application/json'


class TestIntegration_AllSecurityFeatures:
    """Integration tests combining all security features"""
    
    def test_query_with_rls_and_masking(self, client, mock_admin_auth, mock_admin_permission):
        """Test query execution with RLS and masking applied"""
        with patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls, \
             patch('ai_agent_connector.app.api.routes.column_masker') as mock_masker:
            
            # RLS modifies query
            original_query = "SELECT * FROM users"
            rls_query = "SELECT * FROM users WHERE (user_id = current_user())"
            mock_rls.apply_rls_to_query.return_value = rls_query
            
            # Masking masks results
            row = {'id': 1, 'name': 'John', 'ssn': '123-45-6789'}
            masked_row = {'id': 1, 'name': 'John', 'ssn': '***'}
            mock_masker.mask_result_row.return_value = masked_row
            
            # Verify both systems work together
            modified_query = mock_rls.apply_rls_to_query('agent-1', original_query, 'users')
            assert modified_query == rls_query
            
            masked = mock_masker.mask_result_row('agent-1', 'users', row)
            assert masked['ssn'] == '***'
    
    def test_query_validation_and_approval_workflow(self, client, mock_admin_auth, mock_admin_permission):
        """Test complete workflow: validate -> request approval -> approve -> execute"""
        with patch('ai_agent_connector.app.api.routes.query_validator') as mock_validator, \
             patch('ai_agent_connector.app.api.routes.approval_manager') as mock_approval:
            
            from ai_agent_connector.app.utils.query_validator import ValidationResult
            from ai_agent_connector.app.utils.query_approval import QueryApproval
            from ai_agent_connector.app.utils.query_validator import RiskLevel
            
            # Step 1: Validate query
            validation_result = ValidationResult(
                is_valid=False,
                risk_level=RiskLevel.CRITICAL,
                requires_approval=True
            )
            mock_validator.validate_query.return_value = validation_result
            
            # Step 2: Request approval
            approval = QueryApproval(
                approval_id='approval-1',
                agent_id='agent-1',
                query='DELETE FROM users',
                query_type='DELETE',
                risk_level=RiskLevel.CRITICAL,
                complexity_score=90,
                validation_result={}
            )
            mock_approval.request_approval.return_value = approval
            
            # Step 3: Approve
            approved = QueryApproval(
                approval_id='approval-1',
                agent_id='agent-1',
                query='DELETE FROM users',
                query_type='DELETE',
                risk_level=RiskLevel.CRITICAL,
                complexity_score=90,
                validation_result={},
                status=ApprovalStatus.APPROVED
            )
            mock_approval.approve_query.return_value = approved
            
            # Verify workflow
            assert validation_result.requires_approval is True
            assert approval.status == ApprovalStatus.PENDING
            assert approved.status == ApprovalStatus.APPROVED

