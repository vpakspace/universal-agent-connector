"""
Cost Tracking System for AI Provider Calls
Tracks costs per provider, model, and call for optimization and budgeting
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json
from ..utils.helpers import get_timestamp


@dataclass
class CostRecord:
    """Record of a single AI provider call cost"""
    call_id: str
    timestamp: str
    provider: str  # 'openai', 'anthropic', 'custom'
    model: str
    agent_id: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    operation_type: str = "query"  # 'query', 'nl_to_sql', 'suggestion', etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'call_id': self.call_id,
            'timestamp': self.timestamp,
            'provider': self.provider,
            'model': self.model,
            'agent_id': self.agent_id,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'cost_usd': self.cost_usd,
            'operation_type': self.operation_type,
            'metadata': self.metadata
        }


class PricingData:
    """Pricing information for different AI providers and models"""
    
    # OpenAI pricing (per 1M tokens) - as of 2024
    OPENAI_PRICING = {
        # GPT-4 models
        'gpt-4': {'prompt': 30.0, 'completion': 60.0},
        'gpt-4-turbo': {'prompt': 10.0, 'completion': 30.0},
        'gpt-4o': {'prompt': 5.0, 'completion': 15.0},
        'gpt-4o-mini': {'prompt': 0.15, 'completion': 0.6},
        'gpt-4-32k': {'prompt': 60.0, 'completion': 120.0},
        # GPT-3.5 models
        'gpt-3.5-turbo': {'prompt': 0.5, 'completion': 1.5},
        'gpt-3.5-turbo-16k': {'prompt': 3.0, 'completion': 4.0},
        # Default fallback
        'default': {'prompt': 0.5, 'completion': 1.5}
    }
    
    # Anthropic pricing (per 1M tokens) - as of 2024
    ANTHROPIC_PRICING = {
        'claude-3-5-sonnet-20241022': {'input': 3.0, 'output': 15.0},
        'claude-3-opus-20240229': {'input': 15.0, 'output': 75.0},
        'claude-3-sonnet-20240229': {'input': 3.0, 'output': 15.0},
        'claude-3-haiku-20240307': {'input': 0.25, 'output': 1.25},
        'claude-2.1': {'input': 8.0, 'output': 24.0},
        'claude-2.0': {'input': 8.0, 'output': 24.0},
        'claude-instant-1.2': {'input': 0.8, 'output': 2.4},
        # Default fallback
        'default': {'input': 3.0, 'output': 15.0}
    }
    
    @classmethod
    def get_openai_cost(cls, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for OpenAI model"""
        pricing = cls.OPENAI_PRICING.get(model, cls.OPENAI_PRICING['default'])
        prompt_cost = (prompt_tokens / 1_000_000) * pricing['prompt']
        completion_cost = (completion_tokens / 1_000_000) * pricing['completion']
        return prompt_cost + completion_cost
    
    @classmethod
    def get_anthropic_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for Anthropic model"""
        pricing = cls.ANTHROPIC_PRICING.get(model, cls.ANTHROPIC_PRICING['default'])
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']
        return input_cost + output_cost
    
    @classmethod
    def get_custom_cost(cls, model: str, tokens: int, custom_pricing: Optional[Dict[str, float]] = None) -> float:
        """Calculate cost for custom provider"""
        if custom_pricing:
            prompt_price = custom_pricing.get('prompt_per_1m', 0.0)
            completion_price = custom_pricing.get('completion_per_1m', 0.0)
            # For custom, assume 50/50 split if not specified
            prompt_tokens = tokens // 2
            completion_tokens = tokens - prompt_tokens
            return (prompt_tokens / 1_000_000) * prompt_price + (completion_tokens / 1_000_000) * completion_price
        # Default: $0.50 per 1M tokens if no pricing provided
        return (tokens / 1_000_000) * 0.5


@dataclass
class BudgetAlert:
    """Budget alert configuration"""
    alert_id: str
    name: str
    threshold_usd: float
    period: str  # 'daily', 'weekly', 'monthly', 'total'
    enabled: bool = True
    notification_emails: List[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    last_triggered: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'alert_id': self.alert_id,
            'name': self.name,
            'threshold_usd': self.threshold_usd,
            'period': self.period,
            'enabled': self.enabled,
            'notification_emails': self.notification_emails,
            'webhook_url': self.webhook_url,
            'last_triggered': self.last_triggered
        }


class CostTracker:
    """
    Tracks costs for AI provider calls
    Provides real-time dashboard data, export reports, and budget alerts
    """
    
    def __init__(self):
        """Initialize cost tracker"""
        # In-memory storage (can be extended to database)
        self._cost_records: List[CostRecord] = []
        self._budget_alerts: Dict[str, BudgetAlert] = {}
        self._custom_pricing: Dict[str, Dict[str, float]] = {}  # provider_model -> pricing
    
    def track_call(
        self,
        provider: str,
        model: str,
        usage: Dict[str, Any],
        agent_id: Optional[str] = None,
        operation_type: str = "query",
        call_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostRecord:
        """
        Track a single AI provider call and calculate cost
        
        Args:
            provider: Provider name ('openai', 'anthropic', 'custom')
            model: Model name
            usage: Usage dictionary with token information
            agent_id: Optional agent identifier
            operation_type: Type of operation ('query', 'nl_to_sql', 'suggestion', etc.)
            call_id: Optional call identifier
            metadata: Optional metadata dictionary
            
        Returns:
            CostRecord: Created cost record
        """
        import uuid
        call_id = call_id or str(uuid.uuid4())
        timestamp = get_timestamp()
        
        # Extract token counts based on provider
        if provider == 'openai':
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
            cost = PricingData.get_openai_cost(model, prompt_tokens, completion_tokens)
        elif provider == 'anthropic':
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            prompt_tokens = input_tokens
            completion_tokens = output_tokens
            total_tokens = input_tokens + output_tokens
            cost = PricingData.get_anthropic_cost(model, input_tokens, output_tokens)
        else:  # custom
            prompt_tokens = usage.get('prompt_tokens', usage.get('input_tokens', 0))
            completion_tokens = usage.get('completion_tokens', usage.get('output_tokens', 0))
            total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
            custom_pricing = self._custom_pricing.get(f"{provider}_{model}")
            cost = PricingData.get_custom_cost(model, total_tokens, custom_pricing)
        
        # Create cost record
        record = CostRecord(
            call_id=call_id,
            timestamp=timestamp,
            provider=provider,
            model=model,
            agent_id=agent_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            operation_type=operation_type,
            metadata=metadata or {}
        )
        
        self._cost_records.append(record)
        
        # Check budget alerts
        self._check_budget_alerts(record)
        
        return record
    
    def _check_budget_alerts(self, record: CostRecord) -> None:
        """Check if any budget alerts should be triggered"""
        current_total = self.get_total_cost()
        
        for alert in self._budget_alerts.values():
            if not alert.enabled:
                continue
            
            # Calculate period cost
            if alert.period == 'daily':
                period_cost = self.get_cost_for_period(hours=24)
            elif alert.period == 'weekly':
                period_cost = self.get_cost_for_period(days=7)
            elif alert.period == 'monthly':
                period_cost = self.get_cost_for_period(days=30)
            else:  # total
                period_cost = current_total
            
            # Check threshold
            if period_cost >= alert.threshold_usd:
                # Trigger alert if not recently triggered (avoid spam)
                if not alert.last_triggered or self._should_trigger_alert(alert):
                    self._trigger_alert(alert, period_cost)
                    alert.last_triggered = get_timestamp()
    
    def _should_trigger_alert(self, alert: BudgetAlert) -> bool:
        """Check if alert should be triggered (avoid spam)"""
        if not alert.last_triggered:
            return True
        
        # Don't trigger again within 1 hour
        from datetime import datetime
        last_triggered = datetime.fromisoformat(alert.last_triggered.replace('Z', '+00:00'))
        now = datetime.now(last_triggered.tzinfo)
        return (now - last_triggered).total_seconds() > 3600
    
    def _trigger_alert(self, alert: BudgetAlert, current_cost: float) -> None:
        """Trigger a budget alert"""
        # In a real implementation, this would send emails/webhooks
        # For now, we just log it (can be extended)
        print(f"BUDGET ALERT: {alert.name} - ${current_cost:.2f} exceeded threshold ${alert.threshold_usd:.2f}")
    
    def get_total_cost(self) -> float:
        """Get total cost across all calls"""
        return sum(record.cost_usd for record in self._cost_records)
    
    def get_cost_for_period(self, days: int = None, hours: int = None) -> float:
        """Get cost for a specific time period"""
        if not self._cost_records:
            return 0.0
        
        from datetime import datetime, timedelta
        now = datetime.now()
        
        if hours:
            cutoff = now - timedelta(hours=hours)
        elif days:
            cutoff = now - timedelta(days=days)
        else:
            return self.get_total_cost()
        
        cutoff_str = cutoff.isoformat()
        return sum(
            record.cost_usd for record in self._cost_records
            if record.timestamp >= cutoff_str
        )
    
    def get_dashboard_data(
        self,
        agent_id: Optional[str] = None,
        provider: Optional[str] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get real-time dashboard data
        
        Args:
            agent_id: Optional filter by agent
            provider: Optional filter by provider
            period_days: Number of days to include
            
        Returns:
            Dictionary with dashboard metrics
        """
        # Filter records
        filtered_records = self._cost_records
        if agent_id:
            filtered_records = [r for r in filtered_records if r.agent_id == agent_id]
        if provider:
            filtered_records = [r for r in filtered_records if r.provider == provider]
        
        # Time filter
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=period_days)
        cutoff_str = cutoff.isoformat()
        filtered_records = [r for r in filtered_records if r.timestamp >= cutoff_str]
        
        # Calculate metrics
        total_cost = sum(r.cost_usd for r in filtered_records)
        total_calls = len(filtered_records)
        total_tokens = sum(r.total_tokens for r in filtered_records)
        
        # Cost by provider
        cost_by_provider = defaultdict(float)
        for record in filtered_records:
            cost_by_provider[record.provider] += record.cost_usd
        
        # Cost by model
        cost_by_model = defaultdict(float)
        for record in filtered_records:
            cost_by_model[f"{record.provider}/{record.model}"] += record.cost_usd
        
        # Cost by operation type
        cost_by_operation = defaultdict(float)
        for record in filtered_records:
            cost_by_operation[record.operation_type] += record.cost_usd
        
        # Daily cost trend (last 30 days)
        daily_costs = defaultdict(float)
        for record in filtered_records:
            date = record.timestamp[:10]  # YYYY-MM-DD
            daily_costs[date] += record.cost_usd
        
        # Top agents by cost
        agent_costs = defaultdict(float)
        for record in filtered_records:
            if record.agent_id:
                agent_costs[record.agent_id] += record.cost_usd
        
        return {
            'total_cost': round(total_cost, 4),
            'total_calls': total_calls,
            'total_tokens': total_tokens,
            'average_cost_per_call': round(total_cost / total_calls, 6) if total_calls > 0 else 0.0,
            'cost_by_provider': dict(cost_by_provider),
            'cost_by_model': dict(cost_by_model),
            'cost_by_operation': dict(cost_by_operation),
            'daily_costs': dict(daily_costs),
            'top_agents': dict(sorted(agent_costs.items(), key=lambda x: x[1], reverse=True)[:10]),
            'period_days': period_days
        }
    
    def export_report(
        self,
        format: str = 'json',
        agent_id: Optional[str] = None,
        provider: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Export cost report
        
        Args:
            format: Export format ('json', 'csv')
            agent_id: Optional filter by agent
            provider: Optional filter by provider
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            Exported report as string
        """
        # Filter records
        filtered_records = self._cost_records
        if agent_id:
            filtered_records = [r for r in filtered_records if r.agent_id == agent_id]
        if provider:
            filtered_records = [r for r in filtered_records if r.provider == provider]
        if start_date:
            filtered_records = [r for r in filtered_records if r.timestamp >= start_date]
        if end_date:
            filtered_records = [r for r in filtered_records if r.timestamp <= end_date]
        
        if format == 'json':
            return json.dumps({
                'records': [r.to_dict() for r in filtered_records],
                'summary': {
                    'total_cost': sum(r.cost_usd for r in filtered_records),
                    'total_calls': len(filtered_records),
                    'total_tokens': sum(r.total_tokens for r in filtered_records)
                }
            }, indent=2)
        
        elif format == 'csv':
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Call ID', 'Timestamp', 'Provider', 'Model', 'Agent ID',
                'Prompt Tokens', 'Completion Tokens', 'Total Tokens',
                'Cost (USD)', 'Operation Type'
            ])
            
            # Rows
            for record in filtered_records:
                writer.writerow([
                    record.call_id,
                    record.timestamp,
                    record.provider,
                    record.model,
                    record.agent_id or '',
                    record.prompt_tokens,
                    record.completion_tokens,
                    record.total_tokens,
                    f"{record.cost_usd:.6f}",
                    record.operation_type
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def add_budget_alert(
        self,
        name: str,
        threshold_usd: float,
        period: str,
        notification_emails: Optional[List[str]] = None,
        webhook_url: Optional[str] = None
    ) -> BudgetAlert:
        """Add a budget alert"""
        import uuid
        alert_id = str(uuid.uuid4())
        
        alert = BudgetAlert(
            alert_id=alert_id,
            name=name,
            threshold_usd=threshold_usd,
            period=period,
            notification_emails=notification_emails or [],
            webhook_url=webhook_url
        )
        
        self._budget_alerts[alert_id] = alert
        return alert
    
    def get_budget_alerts(self) -> List[BudgetAlert]:
        """Get all budget alerts"""
        return list(self._budget_alerts.values())
    
    def update_budget_alert(
        self,
        alert_id: str,
        **updates
    ) -> Optional[BudgetAlert]:
        """Update a budget alert"""
        if alert_id not in self._budget_alerts:
            return None
        
        alert = self._budget_alerts[alert_id]
        for key, value in updates.items():
            if hasattr(alert, key):
                setattr(alert, key, value)
        
        return alert
    
    def delete_budget_alert(self, alert_id: str) -> bool:
        """Delete a budget alert"""
        if alert_id in self._budget_alerts:
            del self._budget_alerts[alert_id]
            return True
        return False
    
    def set_custom_pricing(
        self,
        provider: str,
        model: str,
        prompt_per_1m: float,
        completion_per_1m: float
    ) -> None:
        """Set custom pricing for a provider/model"""
        key = f"{provider}_{model}"
        self._custom_pricing[key] = {
            'prompt_per_1m': prompt_per_1m,
            'completion_per_1m': completion_per_1m
        }
    
    def get_custom_pricing(self, provider: str, model: str) -> Optional[Dict[str, float]]:
        """Get custom pricing for a provider/model"""
        key = f"{provider}_{model}"
        return self._custom_pricing.get(key)

    def get_statistics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        agent_id: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get cost statistics for a date range

        Args:
            start_date: Optional start date (YYYY-MM-DD or ISO format)
            end_date: Optional end date (YYYY-MM-DD or ISO format)
            agent_id: Optional filter by agent
            provider: Optional filter by provider

        Returns:
            Dictionary with cost statistics
        """
        # Filter records
        filtered_records = self._cost_records

        if agent_id:
            filtered_records = [r for r in filtered_records if r.agent_id == agent_id]
        if provider:
            filtered_records = [r for r in filtered_records if r.provider == provider]
        if start_date:
            filtered_records = [r for r in filtered_records if r.timestamp >= start_date]
        if end_date:
            filtered_records = [r for r in filtered_records if r.timestamp <= end_date]

        # Calculate statistics
        total_cost = sum(r.cost_usd for r in filtered_records)
        total_calls = len(filtered_records)
        total_tokens = sum(r.total_tokens for r in filtered_records)

        # Cost by provider
        cost_by_provider = defaultdict(float)
        calls_by_provider = defaultdict(int)
        for record in filtered_records:
            cost_by_provider[record.provider] += record.cost_usd
            calls_by_provider[record.provider] += 1

        # Cost by model
        cost_by_model = defaultdict(float)
        for record in filtered_records:
            key = f"{record.provider}/{record.model}"
            cost_by_model[key] += record.cost_usd

        # Cost by operation type
        cost_by_operation = defaultdict(float)
        for record in filtered_records:
            cost_by_operation[record.operation_type] += record.cost_usd

        # Daily breakdown
        daily_costs = defaultdict(lambda: {'cost': 0.0, 'calls': 0, 'tokens': 0})
        for record in filtered_records:
            date = record.timestamp[:10]  # YYYY-MM-DD
            daily_costs[date]['cost'] += record.cost_usd
            daily_costs[date]['calls'] += 1
            daily_costs[date]['tokens'] += record.total_tokens

        return {
            'total_cost_usd': round(total_cost, 4),
            'total_calls': total_calls,
            'total_tokens': total_tokens,
            'average_cost_per_call': round(total_cost / total_calls, 6) if total_calls > 0 else 0.0,
            'average_tokens_per_call': round(total_tokens / total_calls, 2) if total_calls > 0 else 0.0,
            'cost_by_provider': dict(cost_by_provider),
            'calls_by_provider': dict(calls_by_provider),
            'cost_by_model': dict(cost_by_model),
            'cost_by_operation': dict(cost_by_operation),
            'daily_breakdown': {k: dict(v) for k, v in daily_costs.items()},
            'date_range': {
                'start': start_date,
                'end': end_date
            }
        }
