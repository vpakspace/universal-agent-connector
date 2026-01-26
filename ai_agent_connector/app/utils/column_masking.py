"""
Column masking system for protecting sensitive data (PII)
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
import hashlib


class MaskingType(Enum):
    """Types of column masking"""
    FULL = "full"  # Replace with fixed value (e.g., "***")
    PARTIAL = "partial"  # Show partial value (e.g., "****1234" for credit card)
    HASH = "hash"  # Hash the value
    NULL = "null"  # Replace with NULL
    CUSTOM = "custom"  # Custom masking function


@dataclass
class MaskingRule:
    """Column masking rule"""
    rule_id: str
    agent_id: Optional[str]  # None for global rules
    table_name: str  # Can include schema: "schema.table"
    column_name: str
    masking_type: MaskingType
    mask_value: Optional[str] = "***"  # Value to use for FULL masking
    show_first: Optional[int] = None  # For PARTIAL: show first N chars
    show_last: Optional[int] = None  # For PARTIAL: show last N chars
    hash_algorithm: str = "sha256"  # For HASH masking
    custom_function: Optional[str] = None  # For CUSTOM masking (function name)
    enabled: bool = True
    description: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'rule_id': self.rule_id,
            'agent_id': self.agent_id,
            'table_name': self.table_name,
            'column_name': self.column_name,
            'masking_type': self.masking_type.value,
            'mask_value': self.mask_value,
            'show_first': self.show_first,
            'show_last': self.show_last,
            'hash_algorithm': self.hash_algorithm,
            'custom_function': self.custom_function,
            'enabled': self.enabled,
            'description': self.description,
            'created_at': self.created_at,
            'created_by': self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaskingRule':
        """Create from dictionary"""
        return cls(
            rule_id=data['rule_id'],
            agent_id=data.get('agent_id'),
            table_name=data['table_name'],
            column_name=data['column_name'],
            masking_type=MaskingType(data.get('masking_type', 'full')),
            mask_value=data.get('mask_value', '***'),
            show_first=data.get('show_first'),
            show_last=data.get('show_last'),
            hash_algorithm=data.get('hash_algorithm', 'sha256'),
            custom_function=data.get('custom_function'),
            enabled=data.get('enabled', True),
            description=data.get('description'),
            created_at=data.get('created_at'),
            created_by=data.get('created_by')
        )


class ColumnMasker:
    """
    Column masking manager.
    Masks sensitive columns in query results.
    """
    
    def __init__(self):
        """Initialize column masker"""
        # agent_id -> table_name -> column_name -> MaskingRule
        self._rules: Dict[str, Dict[str, Dict[str, MaskingRule]]] = {}
        # Global rules (apply to all agents)
        self._global_rules: Dict[str, Dict[str, MaskingRule]] = {}
        # Predefined PII patterns
        self._pii_patterns = {
            'ssn': r'^\d{3}-\d{2}-\d{4}$',
            'credit_card': r'^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^\+?[\d\s\-\(\)]{10,}$'
        }
    
    def add_rule(self, rule: MaskingRule) -> None:
        """
        Add a masking rule.
        
        Args:
            rule: Masking rule to add
        """
        if rule.agent_id:
            # Agent-specific rule
            if rule.agent_id not in self._rules:
                self._rules[rule.agent_id] = {}
            if rule.table_name not in self._rules[rule.agent_id]:
                self._rules[rule.agent_id][rule.table_name] = {}
            
            self._rules[rule.agent_id][rule.table_name][rule.column_name] = rule
        else:
            # Global rule
            if rule.table_name not in self._global_rules:
                self._global_rules[rule.table_name] = {}
            
            self._global_rules[rule.table_name][rule.column_name] = rule
    
    def remove_rule(
        self,
        agent_id: Optional[str],
        table_name: str,
        column_name: str
    ) -> bool:
        """
        Remove a masking rule.
        
        Args:
            agent_id: Agent ID (None for global rules)
            table_name: Table name
            column_name: Column name
            
        Returns:
            bool: True if rule was removed, False if not found
        """
        if agent_id:
            if (agent_id in self._rules and
                table_name in self._rules[agent_id] and
                column_name in self._rules[agent_id][table_name]):
                del self._rules[agent_id][table_name][column_name]
                return True
        else:
            if (table_name in self._global_rules and
                column_name in self._global_rules[table_name]):
                del self._global_rules[table_name][column_name]
                return True
        
        return False
    
    def get_rule(
        self,
        agent_id: Optional[str],
        table_name: str,
        column_name: str
    ) -> Optional[MaskingRule]:
        """
        Get masking rule for a column.
        
        Args:
            agent_id: Agent ID (None for global rules)
            table_name: Table name
            column_name: Column name
            
        Returns:
            MaskingRule or None if not found
        """
        # Check agent-specific rules first
        if agent_id and agent_id in self._rules:
            if table_name in self._rules[agent_id]:
                if column_name in self._rules[agent_id][table_name]:
                    rule = self._rules[agent_id][table_name][column_name]
                    if rule.enabled:
                        return rule
        
        # Check global rules
        if table_name in self._global_rules:
            if column_name in self._global_rules[table_name]:
                rule = self._global_rules[table_name][column_name]
                if rule.enabled:
                    return rule
        
        return None
    
    def mask_value(self, value: Any, rule: MaskingRule) -> Any:
        """
        Mask a value according to a rule.
        
        Args:
            value: Value to mask
            rule: Masking rule
            
        Returns:
            Masked value
        """
        if value is None:
            return None
        
        value_str = str(value)
        
        if rule.masking_type == MaskingType.FULL:
            return rule.mask_value
        
        elif rule.masking_type == MaskingType.PARTIAL:
            if rule.show_first and rule.show_last:
                if len(value_str) <= rule.show_first + rule.show_last:
                    return rule.mask_value
                return value_str[:rule.show_first] + rule.mask_value + value_str[-rule.show_last:]
            elif rule.show_first:
                if len(value_str) <= rule.show_first:
                    return rule.mask_value
                return value_str[:rule.show_first] + rule.mask_value
            elif rule.show_last:
                if len(value_str) <= rule.show_last:
                    return rule.mask_value
                return rule.mask_value + value_str[-rule.show_last:]
            else:
                return rule.mask_value
        
        elif rule.masking_type == MaskingType.HASH:
            if rule.hash_algorithm == "sha256":
                return hashlib.sha256(value_str.encode()).hexdigest()[:16]  # First 16 chars
            elif rule.hash_algorithm == "md5":
                return hashlib.md5(value_str.encode()).hexdigest()[:16]
            else:
                return hashlib.sha256(value_str.encode()).hexdigest()[:16]
        
        elif rule.masking_type == MaskingType.NULL:
            return None
        
        elif rule.masking_type == MaskingType.CUSTOM:
            # Custom function would be called here
            # For now, return masked value
            return rule.mask_value
        
        return value
    
    def mask_result_row(
        self,
        agent_id: Optional[str],
        table_name: str,
        row: Dict[str, Any],
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Mask sensitive columns in a result row.
        
        Args:
            agent_id: Agent ID
            table_name: Table name
            row: Result row as dictionary
            columns: Optional list of column names (if None, uses row keys)
            
        Returns:
            Dictionary with masked values
        """
        if columns is None:
            columns = list(row.keys())
        
        masked_row = row.copy()
        
        for column in columns:
            rule = self.get_rule(agent_id, table_name, column)
            if rule:
                masked_row[column] = self.mask_value(row.get(column), rule)
        
        return masked_row
    
    def mask_result_set(
        self,
        agent_id: Optional[str],
        table_name: str,
        results: List[Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Mask sensitive columns in a result set.
        
        Args:
            agent_id: Agent ID
            table_name: Table name
            results: List of result rows as dictionaries
            columns: Optional list of column names
            
        Returns:
            List of dictionaries with masked values
        """
        return [
            self.mask_result_row(agent_id, table_name, row, columns)
            for row in results
        ]
    
    def detect_pii_column(self, column_name: str, sample_values: List[str]) -> Optional[str]:
        """
        Detect if a column contains PII based on patterns.
        
        Args:
            column_name: Column name
            sample_values: Sample values from the column
            
        Returns:
            PII type if detected, None otherwise
        """
        column_lower = column_name.lower()
        
        # Check column name patterns
        if any(keyword in column_lower for keyword in ['ssn', 'social_security', 'social-security']):
            return 'ssn'
        if any(keyword in column_lower for keyword in ['credit_card', 'creditcard', 'card_number', 'cardnumber']):
            return 'credit_card'
        if any(keyword in column_lower for keyword in ['email', 'e-mail']):
            return 'email'
        if any(keyword in column_lower for keyword in ['phone', 'telephone', 'mobile']):
            return 'phone'
        
        # Check value patterns
        for pii_type, pattern in self._pii_patterns.items():
            matches = sum(1 for v in sample_values[:10] if v and re.match(pattern, str(v)))
            if matches >= len(sample_values[:10]) * 0.8:  # 80% match rate
                return pii_type
        
        return None
    
    def remove_agent_rules(self, agent_id: str) -> None:
        """Remove all rules for an agent"""
        self._rules.pop(agent_id, None)
    
    def list_all_rules(self) -> Dict[str, Any]:
        """List all rules (for admin purposes)"""
        return {
            'agent_rules': {
                agent_id: {
                    table: list(rules.values())
                    for table, rules in tables.items()
                }
                for agent_id, tables in self._rules.items()
            },
            'global_rules': {
                table: list(rules.values())
                for table, rules in self._global_rules.items()
            }
        }

