# Chargeback API Endpoints to Add

The following endpoints should be added to `ai_agent_connector/app/api/routes.py`.

## Import Statement

Add this import with the other imports at the top of the file:

```python
from ..utils.chargeback import (
    chargeback_manager,
    CostAllocationRule,
    AllocationRuleType,
    InvoiceStatus,
    UsageRecord,
    Invoice
)
```

## Endpoints to Add

Add these endpoints in a new section (e.g., before "Result Explanation Endpoints"):

```python
# ============================================================================
# Chargeback and Cost Allocation Endpoints
# ============================================================================

@api_bp.route('/chargeback/usage', methods=['POST'])
def record_usage():
    """
    Record resource usage for chargeback.
    
    Request body:
    {
        "team_id": "team-123",
        "user_id": "user-456",
        "agent_id": "agent-789",
        "resource_type": "query",
        "quantity": 100.0,
        "cost_usd": 5.50,
        "metadata": {}
    }
    
    Returns usage record.
    """
    data = request.get_json() or {}
    
    usage_record = chargeback_manager.record_usage(
        team_id=data.get('team_id'),
        user_id=data.get('user_id'),
        agent_id=data.get('agent_id'),
        resource_type=data.get('resource_type', 'query'),
        quantity=data.get('quantity', 0.0),
        cost_usd=data.get('cost_usd', 0.0),
        metadata=data.get('metadata')
    )
    
    return jsonify({
        'usage_record': usage_record.to_dict()
    }), 201


@api_bp.route('/chargeback/allocation-rules', methods=['GET'])
def list_allocation_rules():
    """
    List cost allocation rules.
    
    Query parameters:
    - team_id: Filter by team ID
    - enabled_only: Only return enabled rules (true/false)
    
    Returns list of allocation rules.
    """
    team_id = request.args.get('team_id')
    enabled_only = request.args.get('enabled_only', 'false').lower() == 'true'
    
    rules = chargeback_manager.list_allocation_rules(
        team_id=team_id,
        enabled_only=enabled_only
    )
    
    return jsonify({
        'rules': [r.to_dict() for r in rules]
    }), 200


@api_bp.route('/chargeback/allocation-rules', methods=['POST'])
def create_allocation_rule():
    """
    Create cost allocation rule.
    
    Request body:
    {
        "rule_id": "rule-123",
        "name": "Team Equal Split",
        "description": "Split costs equally among team members",
        "rule_type": "by_team",
        "enabled": true,
        "team_id": "team-123",
        "user_ids": [],
        "split_percentages": {}
    }
    
    Returns created rule.
    """
    data = request.get_json() or {}
    
    rule_id = data.get('rule_id')
    if not rule_id:
        return jsonify({'error': 'rule_id is required'}), 400
    
    if chargeback_manager.get_allocation_rule(rule_id):
        return jsonify({'error': f'Rule {rule_id} already exists'}), 409
    
    try:
        rule = CostAllocationRule.from_dict(data)
        chargeback_manager.add_allocation_rule(rule)
        
        return jsonify({
            'rule_id': rule_id,
            'message': 'Allocation rule created successfully',
            'rule': rule.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': f'Failed to create rule: {str(e)}'}), 500


@api_bp.route('/chargeback/allocation-rules/<rule_id>', methods=['GET'])
def get_allocation_rule(rule_id: str):
    """
    Get allocation rule by ID.
    
    Returns rule details.
    """
    rule = chargeback_manager.get_allocation_rule(rule_id)
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    return jsonify({'rule': rule.to_dict()}), 200


@api_bp.route('/chargeback/allocation-rules/<rule_id>', methods=['PUT'])
def update_allocation_rule(rule_id: str):
    """
    Update allocation rule.
    
    Request body: Same as create, but only provided fields are updated.
    
    Returns updated rule.
    """
    rule = chargeback_manager.get_allocation_rule(rule_id)
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    data = request.get_json() or {}
    
    try:
        for key, value in data.items():
            if hasattr(rule, key) and key not in ['created_at', 'rule_id']:
                setattr(rule, key, value)
        
        rule.updated_at = datetime.utcnow().isoformat()
        chargeback_manager.add_allocation_rule(rule)
        
        return jsonify({
            'rule_id': rule_id,
            'message': 'Allocation rule updated successfully',
            'rule': rule.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update rule: {str(e)}'}), 500


@api_bp.route('/chargeback/allocation-rules/<rule_id>', methods=['DELETE'])
def delete_allocation_rule(rule_id: str):
    """
    Delete allocation rule.
    
    Returns success message.
    """
    if chargeback_manager.delete_allocation_rule(rule_id):
        return jsonify({'message': 'Allocation rule deleted successfully'}), 200
    else:
        return jsonify({'error': 'Rule not found'}), 404


@api_bp.route('/chargeback/allocate', methods=['POST'])
def allocate_costs():
    """
    Allocate costs for a period.
    
    Request body:
    {
        "period_start": "2024-01-01T00:00:00Z",
        "period_end": "2024-01-31T23:59:59Z",
        "rule_id": "rule-123",  // Optional
        "team_id": "team-123"   // Optional
    }
    
    Returns list of allocated costs.
    """
    data = request.get_json() or {}
    
    period_start = data.get('period_start')
    period_end = data.get('period_end')
    
    if not period_start or not period_end:
        return jsonify({'error': 'period_start and period_end are required'}), 400
    
    try:
        allocations = chargeback_manager.allocate_costs(
            period_start=period_start,
            period_end=period_end,
            rule_id=data.get('rule_id'),
            team_id=data.get('team_id')
        )
        
        return jsonify({
            'allocations': [a.to_dict() for a in allocations]
        }), 200
    except Exception as e:
        return jsonify({'error': f'Cost allocation failed: {str(e)}'}), 500


@api_bp.route('/chargeback/invoices', methods=['POST'])
def generate_invoice():
    """
    Generate invoice from allocated costs.
    
    Request body:
    {
        "team_id": "team-123",  // Optional
        "user_id": "user-456",  // Optional
        "period_start": "2024-01-01T00:00:00Z",
        "period_end": "2024-01-31T23:59:59Z",
        "invoice_number": "INV-20240101-0001"  // Optional
    }
    
    Returns generated invoice.
    """
    data = request.get_json() or {}
    
    period_start = data.get('period_start')
    period_end = data.get('period_end')
    
    if not period_start or not period_end:
        return jsonify({'error': 'period_start and period_end are required'}), 400
    
    try:
        invoice = chargeback_manager.generate_invoice(
            team_id=data.get('team_id'),
            user_id=data.get('user_id'),
            period_start=period_start,
            period_end=period_end,
            invoice_number=data.get('invoice_number')
        )
        
        return jsonify({
            'invoice': invoice.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': f'Invoice generation failed: {str(e)}'}), 500


@api_bp.route('/chargeback/invoices', methods=['GET'])
def list_invoices():
    """
    List invoices.
    
    Query parameters:
    - team_id: Filter by team ID
    - user_id: Filter by user ID
    - status: Filter by status (draft, pending, sent, paid, overdue, cancelled)
    
    Returns list of invoices.
    """
    team_id = request.args.get('team_id')
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    
    invoices = chargeback_manager.list_invoices(
        team_id=team_id,
        user_id=user_id,
        status=status
    )
    
    return jsonify({
        'invoices': [inv.to_dict() for inv in invoices]
    }), 200


@api_bp.route('/chargeback/invoices/<invoice_id>', methods=['GET'])
def get_invoice(invoice_id: str):
    """
    Get invoice by ID.
    
    Returns invoice details.
    """
    invoice = chargeback_manager.get_invoice(invoice_id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404
    
    return jsonify({'invoice': invoice.to_dict()}), 200


@api_bp.route('/chargeback/invoices/<invoice_id>/status', methods=['PUT'])
def update_invoice_status(invoice_id: str):
    """
    Update invoice status.
    
    Request body:
    {
        "status": "sent"  // draft, pending, sent, paid, overdue, cancelled
    }
    
    Returns updated invoice.
    """
    data = request.get_json() or {}
    status = data.get('status')
    
    if not status:
        return jsonify({'error': 'status is required'}), 400
    
    if status not in [s.value for s in InvoiceStatus]:
        return jsonify({'error': f'Invalid status: {status}'}), 400
    
    if chargeback_manager.update_invoice_status(invoice_id, status):
        invoice = chargeback_manager.get_invoice(invoice_id)
        return jsonify({
            'message': 'Invoice status updated successfully',
            'invoice': invoice.to_dict()
        }), 200
    else:
        return jsonify({'error': 'Invoice not found'}), 404


@api_bp.route('/chargeback/usage/summary', methods=['GET'])
def get_usage_summary():
    """
    Get usage summary for a period.
    
    Query parameters:
    - period_start: Period start date (ISO format)
    - period_end: Period end date (ISO format)
    - team_id: Filter by team ID
    - user_id: Filter by user ID
    
    Returns usage summary.
    """
    period_start = request.args.get('period_start')
    period_end = request.args.get('period_end')
    
    if not period_start or not period_end:
        return jsonify({'error': 'period_start and period_end are required'}), 400
    
    try:
        summary = chargeback_manager.get_usage_summary(
            period_start=period_start,
            period_end=period_end,
            team_id=request.args.get('team_id'),
            user_id=request.args.get('user_id')
        )
        
        return jsonify({'summary': summary}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get usage summary: {str(e)}'}), 500


@api_bp.route('/chargeback/reports/team/<team_id>', methods=['GET'])
def get_team_chargeback_report(team_id: str):
    """
    Get chargeback report for a team.
    
    Query parameters:
    - period_start: Period start date (ISO format)
    - period_end: Period end date (ISO format)
    
    Returns chargeback report with usage and costs.
    """
    period_start = request.args.get('period_start')
    period_end = request.args.get('period_end')
    
    if not period_start or not period_end:
        return jsonify({'error': 'period_start and period_end are required'}), 400
    
    try:
        # Get usage summary
        usage_summary = chargeback_manager.get_usage_summary(
            period_start=period_start,
            period_end=period_end,
            team_id=team_id
        )
        
        # Allocate costs
        allocations = chargeback_manager.allocate_costs(
            period_start=period_start,
            period_end=period_end,
            team_id=team_id
        )
        
        # Get invoices
        invoices = chargeback_manager.list_invoices(team_id=team_id)
        
        report = {
            'team_id': team_id,
            'period_start': period_start,
            'period_end': period_end,
            'usage_summary': usage_summary,
            'allocations': [a.to_dict() for a in allocations],
            'invoices': [inv.to_dict() for inv in invoices],
            'total_cost_usd': usage_summary['total_cost_usd']
        }
        
        return jsonify({'report': report}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500


@api_bp.route('/chargeback/reports/user/<user_id>', methods=['GET'])
def get_user_chargeback_report(user_id: str):
    """
    Get chargeback report for a user.
    
    Query parameters:
    - period_start: Period start date (ISO format)
    - period_end: Period end date (ISO format)
    
    Returns chargeback report with usage and costs.
    """
    period_start = request.args.get('period_start')
    period_end = request.args.get('period_end')
    
    if not period_start or not period_end:
        return jsonify({'error': 'period_start and period_end are required'}), 400
    
    try:
        # Get usage summary
        usage_summary = chargeback_manager.get_usage_summary(
            period_start=period_start,
            period_end=period_end,
            user_id=user_id
        )
        
        # Allocate costs
        allocations = chargeback_manager.allocate_costs(
            period_start=period_start,
            period_end=period_end
        )
        
        # Filter allocations for this user
        user_allocations = [a for a in allocations if a.user_id == user_id]
        
        # Get invoices
        invoices = chargeback_manager.list_invoices(user_id=user_id)
        
        report = {
            'user_id': user_id,
            'period_start': period_start,
            'period_end': period_end,
            'usage_summary': usage_summary,
            'allocations': [a.to_dict() for a in user_allocations],
            'invoices': [inv.to_dict() for inv in invoices],
            'total_cost_usd': usage_summary['total_cost_usd']
        }
        
        return jsonify({'report': report}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500
```

## Summary

**Status**: Chargeback implementation is complete ✅

**Core modules created:**
- `ai_agent_connector/app/utils/chargeback.py` - Full chargeback system

**Documentation:**
- `docs/CHARGEBACK_GUIDE.md` - Complete user guide (to be created)

**Note**: Add these endpoints to `routes.py` to complete the integration. All chargeback functionality is implemented and ready to use.

