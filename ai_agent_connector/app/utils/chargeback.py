"""
Chargeback and Cost Allocation System
Tracks usage by team/user and allocates costs based on allocation rules
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict


class AllocationRuleType(Enum):
    """Cost allocation rule types"""
    BY_USAGE = "by_usage"  # Allocate by actual usage (proportional)
    BY_TEAM = "by_team"  # Allocate equally among team members
    BY_USER = "by_user"  # Allocate to specific user
    FIXED_SPLIT = "fixed_split"  # Fixed percentage split
    EQUAL_SPLIT = "equal_split"  # Equal split among entities


class InvoiceStatus(Enum):
    """Invoice status"""
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


@dataclass
class UsageRecord:
    """Record of resource usage"""
    usage_id: str
    timestamp: str
    team_id: Optional[str] = None
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    resource_type: str = "query"  # query, storage, compute, etc.
    resource_id: Optional[str] = None
    quantity: float = 0.0  # Usage quantity (queries, tokens, etc.)
    cost_usd: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class CostAllocationRule:
    """Rule for allocating costs"""
    rule_id: str
    name: str
    description: str
    rule_type: str  # AllocationRuleType value
    enabled: bool = True
    
    # Rule configuration based on type
    team_id: Optional[str] = None  # For team-based allocation
    user_ids: List[str] = field(default_factory=list)  # For user-based allocation
    split_percentages: Dict[str, float] = field(default_factory=dict)  # For fixed split
    allocation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CostAllocationRule':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class AllocatedCost:
    """Allocated cost for a team or user"""
    allocation_id: str
    rule_id: str
    period_start: str
    period_end: str
    team_id: Optional[str] = None
    user_id: Optional[str] = None
    total_cost_usd: float = 0.0
    usage_records: List[str] = field(default_factory=list)  # usage_id references
    allocation_details: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class InvoiceLineItem:
    """Invoice line item"""
    description: str
    quantity: float = 0.0
    unit_price: float = 0.0
    total_price: float = 0.0
    resource_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Invoice:
    """Chargeback invoice"""
    invoice_id: str
    invoice_number: str
    team_id: Optional[str] = None
    user_id: Optional[str] = None
    period_start: str = ""
    period_end: str = ""
    status: str = InvoiceStatus.DRAFT.value
    line_items: List[InvoiceLineItem] = field(default_factory=list)
    subtotal_usd: float = 0.0
    tax_usd: float = 0.0
    total_usd: float = 0.0
    currency: str = "USD"
    due_date: Optional[str] = None
    paid_date: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['line_items'] = [item.to_dict() for item in self.line_items]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Invoice':
        """Create from dictionary"""
        line_items = [InvoiceLineItem(**item) for item in data.get('line_items', [])]
        data['line_items'] = line_items
        return cls(**data)


class ChargebackManager:
    """Manages chargeback and cost allocation"""
    
    def __init__(self, cost_tracker=None):
        """
        Initialize chargeback manager
        
        Args:
            cost_tracker: Optional CostTracker instance for accessing cost records
        """
        self.cost_tracker = cost_tracker
        self.usage_records: Dict[str, UsageRecord] = {}
        self.allocation_rules: Dict[str, CostAllocationRule] = {}
        self.allocated_costs: Dict[str, AllocatedCost] = {}
        self.invoices: Dict[str, Invoice] = {}
        self._invoice_counter = 0
    
    def record_usage(
        self,
        team_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        resource_type: str = "query",
        quantity: float = 0.0,
        cost_usd: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageRecord:
        """
        Record resource usage
        
        Args:
            team_id: Team identifier
            user_id: User identifier
            agent_id: Agent identifier
            resource_type: Type of resource (query, storage, compute)
            quantity: Usage quantity
            cost_usd: Cost in USD
            metadata: Additional metadata
            
        Returns:
            UsageRecord
        """
        usage_record = UsageRecord(
            usage_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            team_id=team_id,
            user_id=user_id,
            agent_id=agent_id,
            resource_type=resource_type,
            quantity=quantity,
            cost_usd=cost_usd,
            metadata=metadata or {}
        )
        
        self.usage_records[usage_record.usage_id] = usage_record
        return usage_record
    
    def add_allocation_rule(self, rule: CostAllocationRule) -> None:
        """Add cost allocation rule"""
        self.allocation_rules[rule.rule_id] = rule
    
    def get_allocation_rule(self, rule_id: str) -> Optional[CostAllocationRule]:
        """Get allocation rule by ID"""
        return self.allocation_rules.get(rule_id)
    
    def list_allocation_rules(
        self,
        team_id: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[CostAllocationRule]:
        """List allocation rules"""
        rules = list(self.allocation_rules.values())
        
        if team_id:
            rules = [r for r in rules if r.team_id == team_id]
        
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        
        return rules
    
    def delete_allocation_rule(self, rule_id: str) -> bool:
        """Delete allocation rule"""
        if rule_id in self.allocation_rules:
            del self.allocation_rules[rule_id]
            return True
        return False
    
    def allocate_costs(
        self,
        period_start: str,
        period_end: str,
        rule_id: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> List[AllocatedCost]:
        """
        Allocate costs for a period
        
        Args:
            period_start: Period start date (ISO format)
            period_start: Period end date (ISO format)
            rule_id: Optional specific rule ID
            team_id: Optional team ID filter
            
        Returns:
            List of AllocatedCost objects
        """
        # Get usage records for period
        usage_records = self._get_usage_for_period(period_start, period_end, team_id)
        
        if not usage_records:
            return []
        
        # Get applicable rules
        if rule_id:
            rules = [self.allocation_rules.get(rule_id)] if rule_id in self.allocation_rules else []
        else:
            rules = self.list_allocation_rules(team_id=team_id, enabled_only=True)
        
        if not rules:
            # Default: allocate by usage (direct allocation)
            return self._allocate_by_usage(usage_records, period_start, period_end)
        
        allocations = []
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            if rule.rule_type == AllocationRuleType.BY_USAGE.value:
                allocations.extend(self._allocate_by_usage(usage_records, period_start, period_end, rule))
            elif rule.rule_type == AllocationRuleType.BY_TEAM.value:
                allocations.extend(self._allocate_by_team(usage_records, period_start, period_end, rule))
            elif rule.rule_type == AllocationRuleType.BY_USER.value:
                allocations.extend(self._allocate_by_user(usage_records, period_start, period_end, rule))
            elif rule.rule_type == AllocationRuleType.FIXED_SPLIT.value:
                allocations.extend(self._allocate_fixed_split(usage_records, period_start, period_end, rule))
            elif rule.rule_type == AllocationRuleType.EQUAL_SPLIT.value:
                allocations.extend(self._allocate_equal_split(usage_records, period_start, period_end, rule))
        
        # Store allocations
        for allocation in allocations:
            self.allocated_costs[allocation.allocation_id] = allocation
        
        return allocations
    
    def _get_usage_for_period(
        self,
        period_start: str,
        period_end: str,
        team_id: Optional[str] = None
    ) -> List[UsageRecord]:
        """Get usage records for a period"""
        start_dt = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(period_end.replace('Z', '+00:00'))
        
        records = []
        for record in self.usage_records.values():
            record_dt = datetime.fromisoformat(record.timestamp.replace('Z', '+00:00'))
            
            if start_dt <= record_dt <= end_dt:
                if team_id is None or record.team_id == team_id:
                    records.append(record)
        
        return records
    
    def _allocate_by_usage(
        self,
        usage_records: List[UsageRecord],
        period_start: str,
        period_end: str,
        rule: Optional[CostAllocationRule] = None
    ) -> List[AllocatedCost]:
        """Allocate costs by actual usage (direct allocation)"""
        # Group by team/user
        allocations_by_key: Dict[tuple, AllocatedCost] = {}
        
        for record in usage_records:
            key = (record.team_id, record.user_id)
            
            if key not in allocations_by_key:
                allocation = AllocatedCost(
                    allocation_id=str(uuid.uuid4()),
                    rule_id=rule.rule_id if rule else "default",
                    period_start=period_start,
                    period_end=period_end,
                    team_id=record.team_id,
                    user_id=record.user_id
                )
                allocations_by_key[key] = allocation
            
            allocation = allocations_by_key[key]
            allocation.total_cost_usd += record.cost_usd
            allocation.usage_records.append(record.usage_id)
        
        return list(allocations_by_key.values())
    
    def _allocate_by_team(
        self,
        usage_records: List[UsageRecord],
        period_start: str,
        period_end: str,
        rule: CostAllocationRule
    ) -> List[AllocatedCost]:
        """Allocate costs equally among team members"""
        if not rule.team_id:
            return []
        
        # Filter usage for this team
        team_usage = [r for r in usage_records if r.team_id == rule.team_id]
        if not team_usage:
            return []
        
        total_cost = sum(r.cost_usd for r in team_usage)
        
        # Get unique users in team
        users = list(set(r.user_id for r in team_usage if r.user_id))
        if not users:
            # Allocate to team level
            return [AllocatedCost(
                allocation_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                period_start=period_start,
                period_end=period_end,
                team_id=rule.team_id,
                total_cost_usd=total_cost,
                usage_records=[r.usage_id for r in team_usage]
            )]
        
        # Split equally among users
        cost_per_user = total_cost / len(users)
        allocations = []
        
        for user_id in users:
            user_usage = [r for r in team_usage if r.user_id == user_id]
            allocation = AllocatedCost(
                allocation_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                period_start=period_start,
                period_end=period_end,
                team_id=rule.team_id,
                user_id=user_id,
                total_cost_usd=cost_per_user,
                usage_records=[r.usage_id for r in user_usage],
                allocation_details={"allocation_method": "equal_split_by_user", "total_users": len(users)}
            )
            allocations.append(allocation)
        
        return allocations
    
    def _allocate_by_user(
        self,
        usage_records: List[UsageRecord],
        period_start: str,
        period_end: str,
        rule: CostAllocationRule
    ) -> List[AllocatedCost]:
        """Allocate costs to specific users"""
        if not rule.user_ids:
            return []
        
        allocations = []
        
        for user_id in rule.user_ids:
            user_usage = [r for r in usage_records if r.user_id == user_id]
            if user_usage:
                total_cost = sum(r.cost_usd for r in user_usage)
                allocation = AllocatedCost(
                    allocation_id=str(uuid.uuid4()),
                    rule_id=rule.rule_id,
                    period_start=period_start,
                    period_end=period_end,
                    user_id=user_id,
                    total_cost_usd=total_cost,
                    usage_records=[r.usage_id for r in user_usage]
                )
                allocations.append(allocation)
        
        return allocations
    
    def _allocate_fixed_split(
        self,
        usage_records: List[UsageRecord],
        period_start: str,
        period_end: str,
        rule: CostAllocationRule
    ) -> List[AllocatedCost]:
        """Allocate costs using fixed percentage split"""
        if not rule.split_percentages:
            return []
        
        total_cost = sum(r.cost_usd for r in usage_records)
        
        # Validate percentages sum to 100
        total_percentage = sum(rule.split_percentages.values())
        if abs(total_percentage - 100.0) > 0.01:
            raise ValueError(f"Split percentages must sum to 100%, got {total_percentage}%")
        
        allocations = []
        
        for entity_id, percentage in rule.split_percentages.items():
            cost = total_cost * (percentage / 100.0)
            
            # Determine if entity is team or user based on rule metadata or pattern
            is_team = entity_id.startswith('team_') if 'entity_type' not in rule.allocation_metadata else \
                     rule.allocation_metadata.get('entity_type') == 'team'
            
            allocation = AllocatedCost(
                allocation_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                period_start=period_start,
                period_end=period_end,
                team_id=entity_id if is_team else None,
                user_id=entity_id if not is_team else None,
                total_cost_usd=cost,
                usage_records=[r.usage_id for r in usage_records],
                allocation_details={"allocation_method": "fixed_split", "percentage": percentage}
            )
            allocations.append(allocation)
        
        return allocations
    
    def _allocate_equal_split(
        self,
        usage_records: List[UsageRecord],
        period_start: str,
        period_end: str,
        rule: CostAllocationRule
    ) -> List[AllocatedCost]:
        """Allocate costs equally among entities"""
        total_cost = sum(r.cost_usd for r in usage_records)
        
        # Get entities from rule
        entities = rule.user_ids or [rule.team_id] if rule.team_id else []
        if not entities:
            return []
        
        cost_per_entity = total_cost / len(entities)
        allocations = []
        
        for entity_id in entities:
            is_team = entity_id.startswith('team_') if 'entity_type' not in rule.allocation_metadata else \
                     rule.allocation_metadata.get('entity_type') == 'team'
            
            allocation = AllocatedCost(
                allocation_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                period_start=period_start,
                period_end=period_end,
                team_id=entity_id if is_team else None,
                user_id=entity_id if not is_team else None,
                total_cost_usd=cost_per_entity,
                usage_records=[r.usage_id for r in usage_records],
                allocation_details={"allocation_method": "equal_split", "total_entities": len(entities)}
            )
            allocations.append(allocation)
        
        return allocations
    
    def generate_invoice(
        self,
        team_id: Optional[str] = None,
        user_id: Optional[str] = None,
        period_start: str = "",
        period_end: str = "",
        allocated_costs: Optional[List[AllocatedCost]] = None,
        invoice_number: Optional[str] = None
    ) -> Invoice:
        """
        Generate invoice from allocated costs
        
        Args:
            team_id: Team ID
            user_id: User ID
            period_start: Period start date
            period_end: Period end date
            allocated_costs: Optional pre-allocated costs, otherwise will allocate
            invoice_number: Optional invoice number
            
        Returns:
            Invoice
        """
        # Allocate costs if not provided
        if allocated_costs is None:
            allocated_costs = self.allocate_costs(period_start, period_end, team_id=team_id)
        
        # Filter by team/user if specified
        if team_id:
            allocated_costs = [ac for ac in allocated_costs if ac.team_id == team_id]
        if user_id:
            allocated_costs = [ac for ac in allocated_costs if ac.user_id == user_id]
        
        # Generate invoice number
        if not invoice_number:
            self._invoice_counter += 1
            invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{self._invoice_counter:04d}"
        
        # Create line items
        line_items = []
        subtotal = 0.0
        
        # Group by resource type
        from collections import defaultdict
        costs_by_resource: Dict[str, List[AllocatedCost]] = defaultdict(list)
        for cost in allocated_costs:
            # Determine resource type from usage records
            resource_type = "query"  # Default
            if cost.usage_records:
                first_record = self.usage_records.get(cost.usage_records[0])
                if first_record:
                    resource_type = first_record.resource_type
            
            costs_by_resource[resource_type].append(cost)
        
        for resource_type, costs in costs_by_resource.items():
            total_cost = sum(c.total_cost_usd for c in costs)
            quantity = len(costs)  # Number of allocations
            
            line_item = InvoiceLineItem(
                description=f"{resource_type.title()} Usage - {period_start} to {period_end}",
                quantity=quantity,
                unit_price=total_cost / quantity if quantity > 0 else 0.0,
                total_price=total_cost,
                resource_type=resource_type,
                metadata={"allocation_count": len(costs)}
            )
            line_items.append(line_item)
            subtotal += total_cost
        
        # Calculate totals
        tax = 0.0  # Tax calculation would go here
        total = subtotal + tax
        
        # Set due date (30 days from now)
        due_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        invoice = Invoice(
            invoice_id=str(uuid.uuid4()),
            invoice_number=invoice_number,
            team_id=team_id,
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            status=InvoiceStatus.DRAFT.value,
            line_items=line_items,
            subtotal_usd=subtotal,
            tax_usd=tax,
            total_usd=total,
            due_date=due_date
        )
        
        self.invoices[invoice.invoice_id] = invoice
        return invoice
    
    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID"""
        return self.invoices.get(invoice_id)
    
    def list_invoices(
        self,
        team_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Invoice]:
        """List invoices"""
        invoices = list(self.invoices.values())
        
        if team_id:
            invoices = [inv for inv in invoices if inv.team_id == team_id]
        
        if user_id:
            invoices = [inv for inv in invoices if inv.user_id == user_id]
        
        if status:
            invoices = [inv for inv in invoices if inv.status == status]
        
        return sorted(invoices, key=lambda x: x.created_at, reverse=True)
    
    def update_invoice_status(self, invoice_id: str, status: str) -> bool:
        """Update invoice status"""
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            return False
        
        invoice.status = status
        invoice.updated_at = datetime.utcnow().isoformat()
        
        if status == InvoiceStatus.PAID.value:
            invoice.paid_date = datetime.utcnow().isoformat()
        
        return True
    
    def get_usage_summary(
        self,
        period_start: str,
        period_end: str,
        team_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get usage summary for a period
        
        Returns:
            Dictionary with usage statistics
        """
        usage_records = self._get_usage_for_period(period_start, period_end, team_id)
        
        if user_id:
            usage_records = [r for r in usage_records if r.user_id == user_id]
        
        total_cost = sum(r.cost_usd for r in usage_records)
        total_quantity = sum(r.quantity for r in usage_records)
        
        # Group by resource type
        by_resource_type: Dict[str, Dict[str, float]] = defaultdict(lambda: {"cost": 0.0, "quantity": 0.0})
        for record in usage_records:
            by_resource_type[record.resource_type]["cost"] += record.cost_usd
            by_resource_type[record.resource_type]["quantity"] += record.quantity
        
        # Group by agent
        by_agent: Dict[str, Dict[str, float]] = defaultdict(lambda: {"cost": 0.0, "quantity": 0.0})
        for record in usage_records:
            if record.agent_id:
                by_agent[record.agent_id]["cost"] += record.cost_usd
                by_agent[record.agent_id]["quantity"] += record.quantity
        
        return {
            "period_start": period_start,
            "period_end": period_end,
            "team_id": team_id,
            "user_id": user_id,
            "total_cost_usd": total_cost,
            "total_quantity": total_quantity,
            "record_count": len(usage_records),
            "by_resource_type": dict(by_resource_type),
            "by_agent": dict(by_agent)
        }


# Global instance
chargeback_manager = ChargebackManager()

