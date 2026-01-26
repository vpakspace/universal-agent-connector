"""
Integration tests for chargeback API endpoints
"""

import unittest
from unittest.mock import Mock, patch
from flask import Flask
import json
from datetime import datetime, timedelta

from ai_agent_connector.app.api import api_bp
from ai_agent_connector.app.utils.chargeback import (
    chargeback_manager,
    CostAllocationRule,
    AllocationRuleType,
    InvoiceStatus
)


class TestChargebackAPI(unittest.TestCase):
    """Test cases for chargeback API endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Clear chargeback manager state
        chargeback_manager.usage_records.clear()
        chargeback_manager.allocation_rules.clear()
        chargeback_manager.allocated_costs.clear()
        chargeback_manager.invoices.clear()
        chargeback_manager._invoice_counter = 0
    
    def test_record_usage(self):
        """Test recording usage"""
        response = self.client.post(
            '/api/chargeback/usage',
            json={
                'team_id': 'team-123',
                'user_id': 'user-456',
                'agent_id': 'agent-789',
                'resource_type': 'query',
                'quantity': 100.0,
                'cost_usd': 5.50,
                'metadata': {'query_id': 'q123'}
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('usage_record', data)
        
        usage_record = data['usage_record']
        self.assertEqual(usage_record['team_id'], 'team-123')
        self.assertEqual(usage_record['user_id'], 'user-456')
        self.assertEqual(usage_record['quantity'], 100.0)
        self.assertEqual(usage_record['cost_usd'], 5.50)
        self.assertIn('usage_id', usage_record)
    
    def test_record_usage_minimal(self):
        """Test recording usage with minimal data"""
        response = self.client.post(
            '/api/chargeback/usage',
            json={
                'cost_usd': 10.0
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('usage_record', data)
        self.assertEqual(data['usage_record']['cost_usd'], 10.0)
    
    def test_list_allocation_rules(self):
        """Test listing allocation rules"""
        # Create some rules
        rule1 = CostAllocationRule(
            rule_id='rule-1',
            name='Rule 1',
            description='Test',
            rule_type=AllocationRuleType.BY_USAGE.value,
            enabled=True
        )
        rule2 = CostAllocationRule(
            rule_id='rule-2',
            name='Rule 2',
            description='Test',
            rule_type=AllocationRuleType.BY_TEAM.value,
            team_id='team-123',
            enabled=False
        )
        chargeback_manager.add_allocation_rule(rule1)
        chargeback_manager.add_allocation_rule(rule2)
        
        response = self.client.get('/api/chargeback/allocation-rules')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('rules', data)
        self.assertEqual(len(data['rules']), 2)
    
    def test_list_allocation_rules_filter_by_team(self):
        """Test listing allocation rules filtered by team"""
        rule1 = CostAllocationRule(
            rule_id='rule-1',
            name='Rule 1',
            description='Test',
            rule_type=AllocationRuleType.BY_TEAM.value,
            team_id='team-123',
            enabled=True
        )
        rule2 = CostAllocationRule(
            rule_id='rule-2',
            name='Rule 2',
            description='Test',
            rule_type=AllocationRuleType.BY_TEAM.value,
            team_id='team-456',
            enabled=True
        )
        chargeback_manager.add_allocation_rule(rule1)
        chargeback_manager.add_allocation_rule(rule2)
        
        response = self.client.get('/api/chargeback/allocation-rules?team_id=team-123')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['rules']), 1)
        self.assertEqual(data['rules'][0]['rule_id'], 'rule-1')
    
    def test_list_allocation_rules_enabled_only(self):
        """Test listing only enabled allocation rules"""
        rule1 = CostAllocationRule(
            rule_id='rule-1',
            name='Rule 1',
            description='Test',
            rule_type=AllocationRuleType.BY_USAGE.value,
            enabled=True
        )
        rule2 = CostAllocationRule(
            rule_id='rule-2',
            name='Rule 2',
            description='Test',
            rule_type=AllocationRuleType.BY_USAGE.value,
            enabled=False
        )
        chargeback_manager.add_allocation_rule(rule1)
        chargeback_manager.add_allocation_rule(rule2)
        
        response = self.client.get('/api/chargeback/allocation-rules?enabled_only=true')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['rules']), 1)
        self.assertEqual(data['rules'][0]['rule_id'], 'rule-1')
    
    def test_create_allocation_rule(self):
        """Test creating allocation rule"""
        response = self.client.post(
            '/api/chargeback/allocation-rules',
            json={
                'rule_id': 'rule-123',
                'name': 'Team Equal Split',
                'description': 'Split costs equally among team members',
                'rule_type': 'by_team',
                'enabled': True,
                'team_id': 'team-123'
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['rule_id'], 'rule-123')
        self.assertIn('message', data)
        
        # Verify rule was created
        rule = chargeback_manager.get_allocation_rule('rule-123')
        self.assertIsNotNone(rule)
        self.assertEqual(rule.name, 'Team Equal Split')
    
    def test_create_allocation_rule_fixed_split(self):
        """Test creating fixed split allocation rule"""
        response = self.client.post(
            '/api/chargeback/allocation-rules',
            json={
                'rule_id': 'rule-fixed',
                'name': 'Fixed Split',
                'description': '60/40 split',
                'rule_type': 'fixed_split',
                'enabled': True,
                'split_percentages': {'team-1': 60.0, 'team-2': 40.0},
                'allocation_metadata': {'entity_type': 'team'}
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['rule_id'], 'rule-fixed')
    
    def test_create_allocation_rule_missing_required_fields(self):
        """Test creating allocation rule without required fields"""
        response = self.client.post(
            '/api/chargeback/allocation-rules',
            json={
                'name': 'Test Rule'
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_allocation_rule(self):
        """Test getting allocation rule by ID"""
        rule = CostAllocationRule(
            rule_id='rule-123',
            name='Test Rule',
            description='Test',
            rule_type=AllocationRuleType.BY_USAGE.value
        )
        chargeback_manager.add_allocation_rule(rule)
        
        response = self.client.get('/api/chargeback/allocation-rules/rule-123')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('rule', data)
        self.assertEqual(data['rule']['rule_id'], 'rule-123')
    
    def test_get_allocation_rule_not_found(self):
        """Test getting non-existent allocation rule"""
        response = self.client.get('/api/chargeback/allocation-rules/non-existent')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_update_allocation_rule(self):
        """Test updating allocation rule"""
        rule = CostAllocationRule(
            rule_id='rule-123',
            name='Original Name',
            description='Test',
            rule_type=AllocationRuleType.BY_USAGE.value,
            enabled=True
        )
        chargeback_manager.add_allocation_rule(rule)
        
        response = self.client.put(
            '/api/chargeback/allocation-rules/rule-123',
            json={
                'name': 'Updated Name',
                'enabled': False
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['rule']['name'], 'Updated Name')
        self.assertEqual(data['rule']['enabled'], False)
    
    def test_delete_allocation_rule(self):
        """Test deleting allocation rule"""
        rule = CostAllocationRule(
            rule_id='rule-123',
            name='Test',
            description='Test',
            rule_type=AllocationRuleType.BY_USAGE.value
        )
        chargeback_manager.add_allocation_rule(rule)
        
        response = self.client.delete('/api/chargeback/allocation-rules/rule-123')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        
        # Verify rule was deleted
        rule = chargeback_manager.get_allocation_rule('rule-123')
        self.assertIsNone(rule)
    
    def test_allocate_costs(self):
        """Test allocating costs"""
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        # Create usage records
        chargeback_manager.record_usage(team_id='team-1', user_id='user-1', cost_usd=10.0)
        chargeback_manager.record_usage(team_id='team-1', user_id='user-2', cost_usd=20.0)
        
        response = self.client.post(
            '/api/chargeback/allocate',
            json={
                'period_start': period_start,
                'period_end': period_end
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('allocations', data)
        self.assertEqual(len(data['allocations']), 2)
    
    def test_allocate_costs_with_rule(self):
        """Test allocating costs with specific rule"""
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        # Create rule
        rule = CostAllocationRule(
            rule_id='rule-1',
            name='Team Split',
            description='Test',
            rule_type=AllocationRuleType.BY_TEAM.value,
            team_id='team-1',
            enabled=True
        )
        chargeback_manager.add_allocation_rule(rule)
        
        # Create usage
        chargeback_manager.record_usage(team_id='team-1', user_id='user-1', cost_usd=10.0)
        chargeback_manager.record_usage(team_id='team-1', user_id='user-2', cost_usd=20.0)
        
        response = self.client.post(
            '/api/chargeback/allocate',
            json={
                'period_start': period_start,
                'period_end': period_end,
                'rule_id': 'rule-1'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('allocations', data)
        self.assertGreater(len(data['allocations']), 0)
    
    def test_allocate_costs_missing_period(self):
        """Test allocating costs without period"""
        response = self.client.post(
            '/api/chargeback/allocate',
            json={}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_generate_invoice(self):
        """Test generating invoice"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        # Create usage
        chargeback_manager.record_usage(team_id='team-1', user_id='user-1', cost_usd=10.0)
        chargeback_manager.record_usage(team_id='team-1', user_id='user-1', cost_usd=20.0)
        
        response = self.client.post(
            '/api/chargeback/invoices',
            json={
                'team_id': 'team-1',
                'user_id': 'user-1',
                'period_start': period_start,
                'period_end': period_end
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('invoice', data)
        self.assertEqual(data['invoice']['team_id'], 'team-1')
        self.assertEqual(data['invoice']['user_id'], 'user-1')
        self.assertIn('invoice_id', data['invoice'])
        self.assertIn('invoice_number', data['invoice'])
    
    def test_list_invoices(self):
        """Test listing invoices"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        # Create invoices
        chargeback_manager.generate_invoice(
            team_id='team-1',
            period_start=period_start,
            period_end=period_end
        )
        chargeback_manager.generate_invoice(
            team_id='team-2',
            period_start=period_start,
            period_end=period_end
        )
        
        response = self.client.get('/api/chargeback/invoices')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('invoices', data)
        self.assertEqual(len(data['invoices']), 2)
    
    def test_list_invoices_filter_by_team(self):
        """Test listing invoices filtered by team"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        invoice1 = chargeback_manager.generate_invoice(
            team_id='team-1',
            period_start=period_start,
            period_end=period_end
        )
        invoice2 = chargeback_manager.generate_invoice(
            team_id='team-2',
            period_start=period_start,
            period_end=period_end
        )
        
        response = self.client.get('/api/chargeback/invoices?team_id=team-1')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['invoices']), 1)
        self.assertEqual(data['invoices'][0]['invoice_id'], invoice1.invoice_id)
    
    def test_list_invoices_filter_by_status(self):
        """Test listing invoices filtered by status"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        invoice1 = chargeback_manager.generate_invoice(
            period_start=period_start,
            period_end=period_end
        )
        invoice2 = chargeback_manager.generate_invoice(
            period_start=period_start,
            period_end=period_end
        )
        chargeback_manager.update_invoice_status(invoice2.invoice_id, InvoiceStatus.PAID.value)
        
        response = self.client.get('/api/chargeback/invoices?status=draft')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['invoices']), 1)
        self.assertEqual(data['invoices'][0]['invoice_id'], invoice1.invoice_id)
    
    def test_get_invoice(self):
        """Test getting invoice by ID"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        invoice = chargeback_manager.generate_invoice(
            period_start=period_start,
            period_end=period_end
        )
        
        response = self.client.get(f'/api/chargeback/invoices/{invoice.invoice_id}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('invoice', data)
        self.assertEqual(data['invoice']['invoice_id'], invoice.invoice_id)
    
    def test_get_invoice_not_found(self):
        """Test getting non-existent invoice"""
        response = self.client.get('/api/chargeback/invoices/non-existent')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_update_invoice_status(self):
        """Test updating invoice status"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        invoice = chargeback_manager.generate_invoice(
            period_start=period_start,
            period_end=period_end
        )
        
        response = self.client.put(
            f'/api/chargeback/invoices/{invoice.invoice_id}/status',
            json={
                'status': 'sent'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['invoice']['status'], 'sent')
    
    def test_update_invoice_status_invalid(self):
        """Test updating invoice status with invalid status"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        invoice = chargeback_manager.generate_invoice(
            period_start=period_start,
            period_end=period_end
        )
        
        response = self.client.put(
            f'/api/chargeback/invoices/{invoice.invoice_id}/status',
            json={
                'status': 'invalid_status'
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_usage_summary(self):
        """Test getting usage summary"""
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        chargeback_manager.record_usage(
            team_id='team-1',
            user_id='user-1',
            resource_type='query',
            quantity=100.0,
            cost_usd=10.0,
            agent_id='agent-1'
        )
        chargeback_manager.record_usage(
            team_id='team-1',
            user_id='user-2',
            resource_type='storage',
            quantity=200.0,
            cost_usd=20.0
        )
        
        response = self.client.get(
            f'/api/chargeback/usage/summary?period_start={period_start}&period_end={period_end}&team_id=team-1'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('summary', data)
        self.assertEqual(data['summary']['team_id'], 'team-1')
        self.assertEqual(data['summary']['total_cost_usd'], 30.0)
        self.assertIn('by_resource_type', data['summary'])
        self.assertIn('by_agent', data['summary'])
    
    def test_get_usage_summary_missing_period(self):
        """Test getting usage summary without period"""
        response = self.client.get('/api/chargeback/usage/summary')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_usage_summary_filter_by_user(self):
        """Test getting usage summary filtered by user"""
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        chargeback_manager.record_usage(user_id='user-1', cost_usd=10.0)
        chargeback_manager.record_usage(user_id='user-2', cost_usd=20.0)
        
        response = self.client.get(
            f'/api/chargeback/usage/summary?period_start={period_start}&period_end={period_end}&user_id=user-1'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['summary']['user_id'], 'user-1')
        self.assertEqual(data['summary']['total_cost_usd'], 10.0)


if __name__ == '__main__':
    unittest.main()

