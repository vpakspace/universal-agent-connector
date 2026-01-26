"""
Unit tests for chargeback and cost allocation system
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from ai_agent_connector.app.utils.chargeback import (
    ChargebackManager,
    UsageRecord,
    CostAllocationRule,
    AllocationRuleType,
    AllocatedCost,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus
)


class TestUsageRecord(unittest.TestCase):
    """Test cases for UsageRecord"""
    
    def test_create_usage_record(self):
        """Test creating a usage record"""
        record = UsageRecord(
            usage_id="usage-123",
            timestamp=datetime.utcnow().isoformat(),
            team_id="team-123",
            user_id="user-456",
            agent_id="agent-789",
            resource_type="query",
            quantity=100.0,
            cost_usd=5.50
        )
        
        self.assertEqual(record.usage_id, "usage-123")
        self.assertEqual(record.team_id, "team-123")
        self.assertEqual(record.user_id, "user-456")
        self.assertEqual(record.quantity, 100.0)
        self.assertEqual(record.cost_usd, 5.50)
    
    def test_usage_record_to_dict(self):
        """Test converting usage record to dictionary"""
        record = UsageRecord(
            usage_id="usage-123",
            timestamp="2024-01-01T00:00:00",
            team_id="team-123",
            quantity=100.0,
            cost_usd=5.50
        )
        
        record_dict = record.to_dict()
        self.assertIn("usage_id", record_dict)
        self.assertIn("team_id", record_dict)
        self.assertEqual(record_dict["cost_usd"], 5.50)
    
    def test_usage_record_with_metadata(self):
        """Test usage record with metadata"""
        metadata = {"query_id": "q123", "database": "prod"}
        record = UsageRecord(
            usage_id="usage-123",
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata
        )
        
        self.assertEqual(record.metadata, metadata)


class TestCostAllocationRule(unittest.TestCase):
    """Test cases for CostAllocationRule"""
    
    def test_create_by_usage_rule(self):
        """Test creating a by-usage allocation rule"""
        rule = CostAllocationRule(
            rule_id="rule-1",
            name="By Usage",
            description="Allocate by actual usage",
            rule_type=AllocationRuleType.BY_USAGE.value
        )
        
        self.assertEqual(rule.rule_id, "rule-1")
        self.assertEqual(rule.rule_type, "by_usage")
        self.assertTrue(rule.enabled)
    
    def test_create_by_team_rule(self):
        """Test creating a by-team allocation rule"""
        rule = CostAllocationRule(
            rule_id="rule-2",
            name="Team Split",
            description="Split equally among team",
            rule_type=AllocationRuleType.BY_TEAM.value,
            team_id="team-123"
        )
        
        self.assertEqual(rule.team_id, "team-123")
        self.assertEqual(rule.rule_type, "by_team")
    
    def test_create_by_user_rule(self):
        """Test creating a by-user allocation rule"""
        rule = CostAllocationRule(
            rule_id="rule-3",
            name="User Allocation",
            description="Allocate to specific users",
            rule_type=AllocationRuleType.BY_USER.value,
            user_ids=["user-1", "user-2"]
        )
        
        self.assertEqual(len(rule.user_ids), 2)
        self.assertIn("user-1", rule.user_ids)
    
    def test_create_fixed_split_rule(self):
        """Test creating a fixed split rule"""
        rule = CostAllocationRule(
            rule_id="rule-4",
            name="Fixed Split",
            description="Fixed percentage split",
            rule_type=AllocationRuleType.FIXED_SPLIT.value,
            split_percentages={"team-1": 60.0, "team-2": 40.0}
        )
        
        self.assertEqual(len(rule.split_percentages), 2)
        self.assertEqual(rule.split_percentages["team-1"], 60.0)
    
    def test_rule_to_dict(self):
        """Test converting rule to dictionary"""
        rule = CostAllocationRule(
            rule_id="rule-1",
            name="Test Rule",
            description="Test",
            rule_type="by_usage"
        )
        
        rule_dict = rule.to_dict()
        self.assertIn("rule_id", rule_dict)
        self.assertIn("rule_type", rule_dict)
        self.assertEqual(rule_dict["name"], "Test Rule")
    
    def test_rule_from_dict(self):
        """Test creating rule from dictionary"""
        data = {
            "rule_id": "rule-1",
            "name": "Test",
            "description": "Test",
            "rule_type": "by_usage",
            "enabled": True,
            "team_id": None,
            "user_ids": [],
            "split_percentages": {},
            "allocation_metadata": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        rule = CostAllocationRule.from_dict(data)
        self.assertEqual(rule.rule_id, "rule-1")
        self.assertEqual(rule.rule_type, "by_usage")


class TestChargebackManager(unittest.TestCase):
    """Test cases for ChargebackManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = ChargebackManager()
    
    def test_record_usage(self):
        """Test recording usage"""
        record = self.manager.record_usage(
            team_id="team-123",
            user_id="user-456",
            resource_type="query",
            quantity=100.0,
            cost_usd=5.50
        )
        
        self.assertIsNotNone(record.usage_id)
        self.assertEqual(record.team_id, "team-123")
        self.assertEqual(record.user_id, "user-456")
        self.assertEqual(record.quantity, 100.0)
        self.assertEqual(record.cost_usd, 5.50)
        
        # Verify it's stored
        stored = self.manager.usage_records.get(record.usage_id)
        self.assertEqual(stored, record)
    
    def test_record_usage_generates_id(self):
        """Test that usage record gets auto-generated ID"""
        record1 = self.manager.record_usage(cost_usd=1.0)
        record2 = self.manager.record_usage(cost_usd=2.0)
        
        self.assertNotEqual(record1.usage_id, record2.usage_id)
        self.assertIsNotNone(record1.usage_id)
        self.assertIsNotNone(record2.usage_id)
    
    def test_add_allocation_rule(self):
        """Test adding allocation rule"""
        rule = CostAllocationRule(
            rule_id="rule-1",
            name="Test Rule",
            description="Test",
            rule_type=AllocationRuleType.BY_USAGE.value
        )
        
        self.manager.add_allocation_rule(rule)
        
        stored = self.manager.get_allocation_rule("rule-1")
        self.assertEqual(stored, rule)
    
    def test_get_allocation_rule(self):
        """Test getting allocation rule"""
        rule = CostAllocationRule(
            rule_id="rule-1",
            name="Test",
            description="Test",
            rule_type="by_usage"
        )
        
        self.manager.add_allocation_rule(rule)
        
        retrieved = self.manager.get_allocation_rule("rule-1")
        self.assertEqual(retrieved, rule)
        
        not_found = self.manager.get_allocation_rule("non-existent")
        self.assertIsNone(not_found)
    
    def test_list_allocation_rules(self):
        """Test listing allocation rules"""
        rule1 = CostAllocationRule(
            rule_id="rule-1",
            name="Rule 1",
            description="Test",
            rule_type="by_usage",
            enabled=True
        )
        rule2 = CostAllocationRule(
            rule_id="rule-2",
            name="Rule 2",
            description="Test",
            rule_type="by_team",
            team_id="team-123",
            enabled=False
        )
        
        self.manager.add_allocation_rule(rule1)
        self.manager.add_allocation_rule(rule2)
        
        all_rules = self.manager.list_allocation_rules()
        self.assertEqual(len(all_rules), 2)
        
        enabled_only = self.manager.list_allocation_rules(enabled_only=True)
        self.assertEqual(len(enabled_only), 1)
        self.assertEqual(enabled_only[0].rule_id, "rule-1")
        
        team_rules = self.manager.list_allocation_rules(team_id="team-123")
        self.assertEqual(len(team_rules), 1)
        self.assertEqual(team_rules[0].rule_id, "rule-2")
    
    def test_delete_allocation_rule(self):
        """Test deleting allocation rule"""
        rule = CostAllocationRule(
            rule_id="rule-1",
            name="Test",
            description="Test",
            rule_type="by_usage"
        )
        
        self.manager.add_allocation_rule(rule)
        self.assertIsNotNone(self.manager.get_allocation_rule("rule-1"))
        
        result = self.manager.delete_allocation_rule("rule-1")
        self.assertTrue(result)
        self.assertIsNone(self.manager.get_allocation_rule("rule-1"))
        
        result = self.manager.delete_allocation_rule("non-existent")
        self.assertFalse(result)
    
    def test_allocate_costs_by_usage(self):
        """Test allocating costs by usage (default)"""
        # Create usage records
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        record1 = self.manager.record_usage(
            team_id="team-1",
            user_id="user-1",
            cost_usd=10.0
        )
        record2 = self.manager.record_usage(
            team_id="team-1",
            user_id="user-2",
            cost_usd=20.0
        )
        record3 = self.manager.record_usage(
            team_id="team-2",
            user_id="user-3",
            cost_usd=30.0
        )
        
        allocations = self.manager.allocate_costs(period_start, period_end)
        
        self.assertEqual(len(allocations), 3)
        
        # Find allocations
        user1_allocation = next((a for a in allocations if a.user_id == "user-1"), None)
        user2_allocation = next((a for a in allocations if a.user_id == "user-2"), None)
        user3_allocation = next((a for a in allocations if a.user_id == "user-3"), None)
        
        self.assertIsNotNone(user1_allocation)
        self.assertEqual(user1_allocation.total_cost_usd, 10.0)
        self.assertIn(record1.usage_id, user1_allocation.usage_records)
        
        self.assertIsNotNone(user2_allocation)
        self.assertEqual(user2_allocation.total_cost_usd, 20.0)
        
        self.assertIsNotNone(user3_allocation)
        self.assertEqual(user3_allocation.total_cost_usd, 30.0)
    
    def test_allocate_costs_by_team(self):
        """Test allocating costs by team (equal split)"""
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        # Create usage for team with 2 users
        record1 = self.manager.record_usage(
            team_id="team-1",
            user_id="user-1",
            cost_usd=10.0
        )
        record2 = self.manager.record_usage(
            team_id="team-1",
            user_id="user-2",
            cost_usd=20.0
        )
        
        # Create allocation rule
        rule = CostAllocationRule(
            rule_id="rule-1",
            name="Team Split",
            description="Split equally",
            rule_type=AllocationRuleType.BY_TEAM.value,
            team_id="team-1",
            enabled=True
        )
        self.manager.add_allocation_rule(rule)
        
        allocations = self.manager.allocate_costs(period_start, period_end, rule_id="rule-1")
        
        self.assertEqual(len(allocations), 2)  # One per user
        
        total_cost = sum(a.total_cost_usd for a in allocations)
        self.assertAlmostEqual(total_cost, 30.0, places=2)
        
        # Each user should get equal share (15.0 each)
        user1_allocation = next((a for a in allocations if a.user_id == "user-1"), None)
        user2_allocation = next((a for a in allocations if a.user_id == "user-2"), None)
        
        self.assertIsNotNone(user1_allocation)
        self.assertIsNotNone(user2_allocation)
        self.assertAlmostEqual(user1_allocation.total_cost_usd, 15.0, places=2)
        self.assertAlmostEqual(user2_allocation.total_cost_usd, 15.0, places=2)
    
    def test_allocate_costs_by_user(self):
        """Test allocating costs by user"""
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        record1 = self.manager.record_usage(
            user_id="user-1",
            cost_usd=10.0
        )
        record2 = self.manager.record_usage(
            user_id="user-2",
            cost_usd=20.0
        )
        
        rule = CostAllocationRule(
            rule_id="rule-1",
            name="User Allocation",
            description="By user",
            rule_type=AllocationRuleType.BY_USER.value,
            user_ids=["user-1", "user-2"],
            enabled=True
        )
        self.manager.add_allocation_rule(rule)
        
        allocations = self.manager.allocate_costs(period_start, period_end, rule_id="rule-1")
        
        self.assertEqual(len(allocations), 2)
        
        user1_allocation = next((a for a in allocations if a.user_id == "user-1"), None)
        user2_allocation = next((a for a in allocations if a.user_id == "user-2"), None)
        
        self.assertEqual(user1_allocation.total_cost_usd, 10.0)
        self.assertEqual(user2_allocation.total_cost_usd, 20.0)
    
    def test_allocate_costs_fixed_split(self):
        """Test allocating costs with fixed split"""
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        self.manager.record_usage(cost_usd=100.0)
        self.manager.record_usage(cost_usd=50.0)
        
        rule = CostAllocationRule(
            rule_id="rule-1",
            name="Fixed Split",
            description="60/40 split",
            rule_type=AllocationRuleType.FIXED_SPLIT.value,
            split_percentages={"team-1": 60.0, "team-2": 40.0},
            allocation_metadata={"entity_type": "team"},
            enabled=True
        )
        self.manager.add_allocation_rule(rule)
        
        allocations = self.manager.allocate_costs(period_start, period_end, rule_id="rule-1")
        
        self.assertEqual(len(allocations), 2)
        
        total_cost = sum(r.cost_usd for r in self.manager.usage_records.values())
        team1_allocation = next((a for a in allocations if a.team_id == "team-1"), None)
        team2_allocation = next((a for a in allocations if a.team_id == "team-2"), None)
        
        self.assertIsNotNone(team1_allocation)
        self.assertIsNotNone(team2_allocation)
        self.assertAlmostEqual(team1_allocation.total_cost_usd, total_cost * 0.6, places=2)
        self.assertAlmostEqual(team2_allocation.total_cost_usd, total_cost * 0.4, places=2)
    
    def test_allocate_costs_fixed_split_invalid_percentage(self):
        """Test that fixed split validates percentage sum"""
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        self.manager.record_usage(cost_usd=100.0)
        
        rule = CostAllocationRule(
            rule_id="rule-1",
            name="Invalid Split",
            description="Invalid percentages",
            rule_type=AllocationRuleType.FIXED_SPLIT.value,
            split_percentages={"team-1": 60.0, "team-2": 50.0},  # Sums to 110%
            allocation_metadata={"entity_type": "team"},
            enabled=True
        )
        self.manager.add_allocation_rule(rule)
        
        with self.assertRaises(ValueError):
            self.manager.allocate_costs(period_start, period_end, rule_id="rule-1")
    
    def test_allocate_costs_equal_split(self):
        """Test allocating costs with equal split"""
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        self.manager.record_usage(cost_usd=100.0)
        self.manager.record_usage(cost_usd=50.0)
        
        rule = CostAllocationRule(
            rule_id="rule-1",
            name="Equal Split",
            description="Equal split",
            rule_type=AllocationRuleType.EQUAL_SPLIT.value,
            user_ids=["user-1", "user-2"],
            enabled=True
        )
        self.manager.add_allocation_rule(rule)
        
        allocations = self.manager.allocate_costs(period_start, period_end, rule_id="rule-1")
        
        self.assertEqual(len(allocations), 2)
        
        total_cost = sum(r.cost_usd for r in self.manager.usage_records.values())
        cost_per_user = total_cost / 2
        
        user1_allocation = next((a for a in allocations if a.user_id == "user-1"), None)
        user2_allocation = next((a for a in allocations if a.user_id == "user-2"), None)
        
        self.assertAlmostEqual(user1_allocation.total_cost_usd, cost_per_user, places=2)
        self.assertAlmostEqual(user2_allocation.total_cost_usd, cost_per_user, places=2)
    
    def test_allocate_costs_empty_period(self):
        """Test allocating costs for period with no usage"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = (datetime.utcnow() - timedelta(days=20)).isoformat()
        
        # Create usage after the period
        self.manager.record_usage(cost_usd=100.0)
        
        allocations = self.manager.allocate_costs(period_start, period_end)
        self.assertEqual(len(allocations), 0)
    
    def test_allocate_costs_filter_by_team(self):
        """Test allocating costs filtered by team"""
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        self.manager.record_usage(team_id="team-1", cost_usd=10.0)
        self.manager.record_usage(team_id="team-2", cost_usd=20.0)
        
        allocations = self.manager.allocate_costs(period_start, period_end, team_id="team-1")
        
        self.assertEqual(len(allocations), 1)
        self.assertEqual(allocations[0].team_id, "team-1")
        self.assertEqual(allocations[0].total_cost_usd, 10.0)
    
    def test_generate_invoice(self):
        """Test generating invoice"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        # Create usage records
        self.manager.record_usage(
            team_id="team-1",
            user_id="user-1",
            resource_type="query",
            cost_usd=10.0
        )
        self.manager.record_usage(
            team_id="team-1",
            user_id="user-1",
            resource_type="query",
            cost_usd=20.0
        )
        
        invoice = self.manager.generate_invoice(
            team_id="team-1",
            user_id="user-1",
            period_start=period_start,
            period_end=period_end
        )
        
        self.assertIsNotNone(invoice.invoice_id)
        self.assertIsNotNone(invoice.invoice_number)
        self.assertEqual(invoice.team_id, "team-1")
        self.assertEqual(invoice.user_id, "user-1")
        self.assertEqual(invoice.status, InvoiceStatus.DRAFT.value)
        self.assertAlmostEqual(invoice.total_usd, 30.0, places=2)
        self.assertEqual(len(invoice.line_items), 1)
    
    def test_generate_invoice_with_allocated_costs(self):
        """Test generating invoice with pre-allocated costs"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        # Pre-allocate costs
        allocations = self.manager.allocate_costs(period_start, period_end)
        
        invoice = self.manager.generate_invoice(
            period_start=period_start,
            period_end=period_end,
            allocated_costs=allocations
        )
        
        self.assertIsNotNone(invoice.invoice_id)
        self.assertEqual(len(invoice.line_items), 1)
    
    def test_get_invoice(self):
        """Test getting invoice by ID"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        invoice = self.manager.generate_invoice(
            period_start=period_start,
            period_end=period_end
        )
        
        retrieved = self.manager.get_invoice(invoice.invoice_id)
        self.assertEqual(retrieved, invoice)
        
        not_found = self.manager.get_invoice("non-existent")
        self.assertIsNone(not_found)
    
    def test_list_invoices(self):
        """Test listing invoices"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        invoice1 = self.manager.generate_invoice(
            team_id="team-1",
            period_start=period_start,
            period_end=period_end
        )
        invoice2 = self.manager.generate_invoice(
            team_id="team-2",
            period_start=period_start,
            period_end=period_end
        )
        
        all_invoices = self.manager.list_invoices()
        self.assertEqual(len(all_invoices), 2)
        
        team_invoices = self.manager.list_invoices(team_id="team-1")
        self.assertEqual(len(team_invoices), 1)
        self.assertEqual(team_invoices[0].invoice_id, invoice1.invoice_id)
    
    def test_list_invoices_filter_by_status(self):
        """Test listing invoices filtered by status"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        invoice1 = self.manager.generate_invoice(
            period_start=period_start,
            period_end=period_end
        )
        invoice2 = self.manager.generate_invoice(
            period_start=period_start,
            period_end=period_end
        )
        
        # Update status of invoice2
        self.manager.update_invoice_status(invoice2.invoice_id, InvoiceStatus.PAID.value)
        
        draft_invoices = self.manager.list_invoices(status=InvoiceStatus.DRAFT.value)
        self.assertEqual(len(draft_invoices), 1)
        self.assertEqual(draft_invoices[0].invoice_id, invoice1.invoice_id)
        
        paid_invoices = self.manager.list_invoices(status=InvoiceStatus.PAID.value)
        self.assertEqual(len(paid_invoices), 1)
        self.assertEqual(paid_invoices[0].invoice_id, invoice2.invoice_id)
    
    def test_update_invoice_status(self):
        """Test updating invoice status"""
        period_start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        invoice = self.manager.generate_invoice(
            period_start=period_start,
            period_end=period_end
        )
        
        result = self.manager.update_invoice_status(invoice.invoice_id, InvoiceStatus.SENT.value)
        self.assertTrue(result)
        
        updated = self.manager.get_invoice(invoice.invoice_id)
        self.assertEqual(updated.status, InvoiceStatus.SENT.value)
        
        # Test updating to PAID sets paid_date
        self.manager.update_invoice_status(invoice.invoice_id, InvoiceStatus.PAID.value)
        updated = self.manager.get_invoice(invoice.invoice_id)
        self.assertEqual(updated.status, InvoiceStatus.PAID.value)
        self.assertIsNotNone(updated.paid_date)
        
        # Test updating non-existent invoice
        result = self.manager.update_invoice_status("non-existent", InvoiceStatus.PAID.value)
        self.assertFalse(result)
    
    def test_get_usage_summary(self):
        """Test getting usage summary"""
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        self.manager.record_usage(
            team_id="team-1",
            user_id="user-1",
            resource_type="query",
            quantity=100.0,
            cost_usd=10.0,
            agent_id="agent-1"
        )
        self.manager.record_usage(
            team_id="team-1",
            user_id="user-1",
            resource_type="query",
            quantity=50.0,
            cost_usd=5.0,
            agent_id="agent-2"
        )
        self.manager.record_usage(
            team_id="team-1",
            user_id="user-2",
            resource_type="storage",
            quantity=200.0,
            cost_usd=20.0
        )
        
        summary = self.manager.get_usage_summary(period_start, period_end, team_id="team-1")
        
        self.assertEqual(summary["team_id"], "team-1")
        self.assertEqual(summary["total_cost_usd"], 35.0)
        self.assertEqual(summary["total_quantity"], 350.0)
        self.assertEqual(summary["record_count"], 3)
        
        # Check by resource type
        self.assertIn("query", summary["by_resource_type"])
        self.assertIn("storage", summary["by_resource_type"])
        self.assertEqual(summary["by_resource_type"]["query"]["cost"], 15.0)
        self.assertEqual(summary["by_resource_type"]["storage"]["cost"], 20.0)
        
        # Check by agent
        self.assertIn("agent-1", summary["by_agent"])
        self.assertIn("agent-2", summary["by_agent"])
        self.assertEqual(summary["by_agent"]["agent-1"]["cost"], 10.0)
        self.assertEqual(summary["by_agent"]["agent-2"]["cost"], 5.0)
    
    def test_get_usage_summary_filter_by_user(self):
        """Test getting usage summary filtered by user"""
        period_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        period_end = datetime.utcnow().isoformat()
        
        self.manager.record_usage(user_id="user-1", cost_usd=10.0)
        self.manager.record_usage(user_id="user-2", cost_usd=20.0)
        
        summary = self.manager.get_usage_summary(
            period_start,
            period_end,
            user_id="user-1"
        )
        
        self.assertEqual(summary["user_id"], "user-1")
        self.assertEqual(summary["total_cost_usd"], 10.0)
        self.assertEqual(summary["record_count"], 1)


class TestInvoice(unittest.TestCase):
    """Test cases for Invoice"""
    
    def test_create_invoice(self):
        """Test creating an invoice"""
        line_item = InvoiceLineItem(
            description="Query Usage",
            quantity=100.0,
            unit_price=0.10,
            total_price=10.0,
            resource_type="query"
        )
        
        invoice = Invoice(
            invoice_id="inv-123",
            invoice_number="INV-20240101-0001",
            team_id="team-1",
            period_start="2024-01-01",
            period_end="2024-01-31",
            line_items=[line_item],
            subtotal_usd=10.0,
            tax_usd=1.0,
            total_usd=11.0
        )
        
        self.assertEqual(invoice.invoice_id, "inv-123")
        self.assertEqual(invoice.invoice_number, "INV-20240101-0001")
        self.assertEqual(len(invoice.line_items), 1)
        self.assertEqual(invoice.total_usd, 11.0)
    
    def test_invoice_to_dict(self):
        """Test converting invoice to dictionary"""
        line_item = InvoiceLineItem(
            description="Test",
            quantity=1.0,
            unit_price=10.0,
            total_price=10.0
        )
        
        invoice = Invoice(
            invoice_id="inv-123",
            invoice_number="INV-001",
            line_items=[line_item],
            subtotal_usd=10.0,
            total_usd=10.0
        )
        
        invoice_dict = invoice.to_dict()
        self.assertIn("invoice_id", invoice_dict)
        self.assertIn("line_items", invoice_dict)
        self.assertEqual(len(invoice_dict["line_items"]), 1)
    
    def test_invoice_from_dict(self):
        """Test creating invoice from dictionary"""
        data = {
            "invoice_id": "inv-123",
            "invoice_number": "INV-001",
            "team_id": None,
            "user_id": None,
            "period_start": "",
            "period_end": "",
            "status": "draft",
            "line_items": [
                {
                    "description": "Test",
                    "quantity": 1.0,
                    "unit_price": 10.0,
                    "total_price": 10.0,
                    "resource_type": "",
                    "metadata": {}
                }
            ],
            "subtotal_usd": 10.0,
            "tax_usd": 0.0,
            "total_usd": 10.0,
            "currency": "USD",
            "due_date": None,
            "paid_date": None,
            "metadata": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        invoice = Invoice.from_dict(data)
        self.assertEqual(invoice.invoice_id, "inv-123")
        self.assertEqual(len(invoice.line_items), 1)


if __name__ == '__main__':
    unittest.main()

