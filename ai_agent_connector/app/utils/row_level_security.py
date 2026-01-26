"""
Row-Level Security (RLS) system for filtering data based on conditions
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import re


class RLSRuleType(Enum):
    """Types of RLS rules"""
    EQUALITY = "equality"  # column = value
    INEQUALITY = "inequality"  # column != value
    COMPARISON = "comparison"  # column >, <, >=, <= value
    IN = "in"  # column IN (value1, value2, ...)
    LIKE = "like"  # column LIKE pattern
    CUSTOM = "custom"  # Custom SQL condition


@dataclass
class RLSRule:
    """Row-level security rule"""
    rule_id: str
    agent_id: str
    table_name: str  # Can include schema: "schema.table"
    condition: str  # SQL WHERE condition (e.g., "user_id = current_user()")
    rule_type: RLSRuleType = RLSRuleType.CUSTOM
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
            'condition': self.condition,
            'rule_type': self.rule_type.value,
            'enabled': self.enabled,
            'description': self.description,
            'created_at': self.created_at,
            'created_by': self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RLSRule':
        """Create from dictionary"""
        return cls(
            rule_id=data['rule_id'],
            agent_id=data['agent_id'],
            table_name=data['table_name'],
            condition=data['condition'],
            rule_type=RLSRuleType(data.get('rule_type', 'custom')),
            enabled=data.get('enabled', True),
            description=data.get('description'),
            created_at=data.get('created_at'),
            created_by=data.get('created_by')
        )


class RowLevelSecurity:
    """
    Row-Level Security manager.
    Applies RLS rules to SQL queries to filter data based on conditions.
    """
    
    def __init__(self):
        """Initialize RLS manager"""
        # agent_id -> table_name -> list of RLSRule
        self._rules: Dict[str, Dict[str, List[RLSRule]]] = {}
        # Global rules (apply to all agents)
        self._global_rules: Dict[str, List[RLSRule]] = {}
    
    def add_rule(self, rule: RLSRule) -> None:
        """
        Add an RLS rule.
        
        Args:
            rule: RLS rule to add
        """
        if rule.agent_id not in self._rules:
            self._rules[rule.agent_id] = {}
        
        if rule.table_name not in self._rules[rule.agent_id]:
            self._rules[rule.agent_id][rule.table_name] = []
        
        # Remove existing rule with same ID if present
        self._rules[rule.agent_id][rule.table_name] = [
            r for r in self._rules[rule.agent_id][rule.table_name]
            if r.rule_id != rule.rule_id
        ]
        
        self._rules[rule.agent_id][rule.table_name].append(rule)
    
    def add_global_rule(self, rule: RLSRule) -> None:
        """
        Add a global RLS rule (applies to all agents).
        
        Args:
            rule: RLS rule to add (agent_id is ignored for global rules)
        """
        if rule.table_name not in self._global_rules:
            self._global_rules[rule.table_name] = []
        
        # Remove existing rule with same ID if present
        self._global_rules[rule.table_name] = [
            r for r in self._global_rules[rule.table_name]
            if r.rule_id != rule.rule_id
        ]
        
        self._global_rules[rule.table_name].append(rule)
    
    def remove_rule(self, agent_id: str, table_name: str, rule_id: str) -> bool:
        """
        Remove an RLS rule.
        
        Args:
            agent_id: Agent ID
            table_name: Table name
            rule_id: Rule ID to remove
            
        Returns:
            bool: True if rule was removed, False if not found
        """
        if agent_id not in self._rules:
            return False
        
        if table_name not in self._rules[agent_id]:
            return False
        
        original_count = len(self._rules[agent_id][table_name])
        self._rules[agent_id][table_name] = [
            r for r in self._rules[agent_id][table_name]
            if r.rule_id != rule_id
        ]
        
        return len(self._rules[agent_id][table_name]) < original_count
    
    def get_rules(self, agent_id: str, table_name: Optional[str] = None) -> List[RLSRule]:
        """
        Get RLS rules for an agent and optionally a specific table.
        
        Args:
            agent_id: Agent ID
            table_name: Optional table name to filter by
            
        Returns:
            List of RLS rules
        """
        rules = []
        
        # Get agent-specific rules
        if agent_id in self._rules:
            if table_name:
                rules.extend(self._rules[agent_id].get(table_name, []))
            else:
                for table_rules in self._rules[agent_id].values():
                    rules.extend(table_rules)
        
        # Get global rules
        if table_name:
            rules.extend(self._global_rules.get(table_name, []))
        else:
            for table_rules in self._global_rules.values():
                rules.extend(table_rules)
        
        # Filter to only enabled rules
        return [r for r in rules if r.enabled]
    
    def apply_rls_to_query(
        self,
        agent_id: str,
        query: str,
        table_name: Optional[str] = None
    ) -> str:
        """
        Apply RLS rules to a SQL query.
        
        This method modifies the query to include WHERE conditions from RLS rules.
        For SELECT queries, it adds WHERE clauses. For other queries, it may
        add conditions to restrict the scope.
        
        Args:
            agent_id: Agent ID executing the query
            query: Original SQL query
            table_name: Optional table name (if None, will be extracted from query)
            
        Returns:
            str: Modified query with RLS conditions applied
        """
        if not query or not isinstance(query, str):
            return query
        
        # Extract table name from query if not provided
        if not table_name:
            tables = self._extract_tables_from_query(query)
            if not tables:
                return query  # No tables found, return as-is
            table_name = list(tables)[0]  # Use first table
        
        # Get applicable rules
        rules = self.get_rules(agent_id, table_name)
        
        if not rules:
            return query  # No rules, return original query
        
        # Build WHERE conditions from rules
        conditions = [rule.condition for rule in rules]
        
        if not conditions:
            return query
        
        # Combine conditions with AND
        combined_condition = " AND ".join(f"({c})" for c in conditions)
        
        # Apply RLS to query
        modified_query = self._inject_where_clause(query, combined_condition)
        
        return modified_query
    
    def _extract_tables_from_query(self, query: str) -> set:
        """Extract table names from SQL query"""
        # Simple extraction - can be enhanced with proper SQL parser
        tables = set()
        
        # FROM clause
        from_match = re.search(r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)', query, re.IGNORECASE)
        if from_match:
            tables.add(from_match.group(1).lower())
        
        # JOIN clauses
        join_matches = re.finditer(r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)', query, re.IGNORECASE)
        for match in join_matches:
            tables.add(match.group(1).lower())
        
        return tables
    
    def _inject_where_clause(self, query: str, condition: str) -> str:
        """
        Inject a WHERE clause into a SQL query.
        
        If WHERE already exists, adds condition with AND.
        If WHERE doesn't exist, adds WHERE clause.
        """
        query_upper = query.upper()
        
        # Check if WHERE already exists
        where_pos = query_upper.find(' WHERE ')
        if where_pos != -1:
            # Find the end of WHERE clause (before GROUP BY, ORDER BY, LIMIT, etc.)
            end_keywords = [' GROUP BY ', ' ORDER BY ', ' HAVING ', ' LIMIT ', ' OFFSET ']
            end_pos = len(query)
            
            for keyword in end_keywords:
                keyword_pos = query_upper.find(keyword, where_pos)
                if keyword_pos != -1 and keyword_pos < end_pos:
                    end_pos = keyword_pos
            
            # Insert condition before end
            return (
                query[:end_pos] +
                f" AND ({condition})" +
                query[end_pos:]
            )
        else:
            # Find where to insert WHERE (before GROUP BY, ORDER BY, etc.)
            insert_keywords = [' GROUP BY ', ' ORDER BY ', ' HAVING ', ' LIMIT ', ' OFFSET ']
            insert_pos = len(query)
            
            for keyword in insert_keywords:
                keyword_pos = query_upper.find(keyword)
                if keyword_pos != -1 and keyword_pos < insert_pos:
                    insert_pos = keyword_pos
            
            # Insert WHERE clause
            return (
                query[:insert_pos] +
                f" WHERE ({condition})" +
                query[insert_pos:]
            )
    
    def remove_agent_rules(self, agent_id: str) -> None:
        """Remove all rules for an agent"""
        self._rules.pop(agent_id, None)
    
    def list_all_rules(self) -> Dict[str, Dict[str, List[RLSRule]]]:
        """List all rules (for admin purposes)"""
        return {
            'agent_rules': self._rules,
            'global_rules': self._global_rules
        }

