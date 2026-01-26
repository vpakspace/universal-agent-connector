"""
Data residency rules enforcement
Enforces data residency rules (e.g., EU data stays in EU databases) for GDPR compliance
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re


class DataRegion(Enum):
    """Data regions"""
    EU = "eu"
    US = "us"
    APAC = "apac"
    GLOBAL = "global"


@dataclass
class ResidencyRule:
    """A data residency rule"""
    rule_id: str
    name: str
    region: DataRegion
    database_patterns: List[str]  # Regex patterns for database names/connection strings
    table_patterns: List[str]  # Regex patterns for table names
    column_patterns: List[str]  # Regex patterns for column names
    is_active: bool = True
    description: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'region': self.region.value,
            'database_patterns': self.database_patterns,
            'table_patterns': self.table_patterns,
            'column_patterns': self.column_patterns,
            'is_active': self.is_active,
            'description': self.description,
            'metadata': self.metadata or {}
        }


class DataResidencyManager:
    """
    Manages data residency rules and enforces them.
    """
    
    def __init__(self):
        """Initialize data residency manager"""
        # rule_id -> ResidencyRule
        self._rules: Dict[str, ResidencyRule] = {}
        # region -> list of rule_ids
        self._region_rules: Dict[DataRegion, List[str]] = {}
    
    def create_rule(
        self,
        name: str,
        region: DataRegion,
        database_patterns: List[str],
        table_patterns: Optional[List[str]] = None,
        column_patterns: Optional[List[str]] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ResidencyRule:
        """
        Create a data residency rule.
        
        Args:
            name: Rule name
            region: Data region
            database_patterns: Regex patterns for database names
            table_patterns: Optional regex patterns for table names
            column_patterns: Optional regex patterns for column names
            description: Optional description
            metadata: Optional metadata
            
        Returns:
            ResidencyRule object
        """
        import uuid
        rule_id = str(uuid.uuid4())
        
        rule = ResidencyRule(
            rule_id=rule_id,
            name=name,
            region=region,
            database_patterns=database_patterns,
            table_patterns=table_patterns or [],
            column_patterns=column_patterns or [],
            description=description,
            metadata=metadata or {}
        )
        
        self._rules[rule_id] = rule
        
        # Track by region
        if region not in self._region_rules:
            self._region_rules[region] = []
        self._region_rules[region].append(rule_id)
        
        return rule
    
    def get_rule(self, rule_id: str) -> Optional[ResidencyRule]:
        """Get a residency rule"""
        return self._rules.get(rule_id)
    
    def list_rules(
        self,
        region: Optional[DataRegion] = None,
        is_active: Optional[bool] = None
    ) -> List[ResidencyRule]:
        """
        List residency rules.
        
        Args:
            region: Filter by region
            is_active: Filter by active status
            
        Returns:
            List of ResidencyRule objects
        """
        rules = list(self._rules.values())
        
        if region:
            rules = [r for r in rules if r.region == region]
        
        if is_active is not None:
            rules = [r for r in rules if r.is_active == is_active]
        
        return rules
    
    def update_rule(
        self,
        rule_id: str,
        name: Optional[str] = None,
        region: Optional[DataRegion] = None,
        database_patterns: Optional[List[str]] = None,
        table_patterns: Optional[List[str]] = None,
        column_patterns: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
        description: Optional[str] = None
    ) -> Optional[ResidencyRule]:
        """
        Update a residency rule.
        
        Args:
            rule_id: Rule ID
            name: New name
            region: New region
            database_patterns: New database patterns
            table_patterns: New table patterns
            column_patterns: New column patterns
            is_active: Active status
            description: New description
            
        Returns:
            Updated ResidencyRule or None if not found
        """
        rule = self._rules.get(rule_id)
        if not rule:
            return None
        
        if name is not None:
            rule.name = name
        
        if region is not None:
            # Update region tracking
            if rule.region in self._region_rules:
                self._region_rules[rule.region] = [
                    rid for rid in self._region_rules[rule.region] if rid != rule_id
                ]
            
            rule.region = region
            if region not in self._region_rules:
                self._region_rules[region] = []
            self._region_rules[region].append(rule_id)
        
        if database_patterns is not None:
            rule.database_patterns = database_patterns
        
        if table_patterns is not None:
            rule.table_patterns = table_patterns
        
        if column_patterns is not None:
            rule.column_patterns = column_patterns
        
        if is_active is not None:
            rule.is_active = is_active
        
        if description is not None:
            rule.description = description
        
        return rule
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a residency rule"""
        rule = self._rules.get(rule_id)
        if not rule:
            return False
        
        # Remove from region tracking
        if rule.region in self._region_rules:
            self._region_rules[rule.region] = [
                rid for rid in self._region_rules[rule.region] if rid != rule_id
            ]
        
        del self._rules[rule_id]
        return True
    
    def validate_residency(
        self,
        database_name: str,
        connection_string: Optional[str] = None,
        tables: Optional[List[str]] = None,
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate data residency for a query.
        
        Args:
            database_name: Database name
            connection_string: Optional connection string
            tables: Optional list of table names
            columns: Optional list of column names
            
        Returns:
            Dict with validation result
        """
        violations = []
        applicable_rules = []
        
        # Check all active rules
        for rule in self._rules.values():
            if not rule.is_active:
                continue
            
            # Check database patterns
            matches_database = False
            for pattern in rule.database_patterns:
                if re.search(pattern, database_name, re.IGNORECASE):
                    matches_database = True
                    break
                if connection_string and re.search(pattern, connection_string, re.IGNORECASE):
                    matches_database = True
                    break
            
            if not matches_database:
                continue
            
            applicable_rules.append(rule)
            
            # Check table patterns if provided
            if tables and rule.table_patterns:
                for table in tables:
                    for pattern in rule.table_patterns:
                        if re.search(pattern, table, re.IGNORECASE):
                            violations.append({
                                'rule_id': rule.rule_id,
                                'rule_name': rule.name,
                                'region': rule.region.value,
                                'type': 'table',
                                'resource': table,
                                'pattern': pattern
                            })
            
            # Check column patterns if provided
            if columns and rule.column_patterns:
                for column in columns:
                    for pattern in rule.column_patterns:
                        if re.search(pattern, column, re.IGNORECASE):
                            violations.append({
                                'rule_id': rule.rule_id,
                                'rule_name': rule.name,
                                'region': rule.region.value,
                                'type': 'column',
                                'resource': column,
                                'pattern': pattern
                            })
        
        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'applicable_rules': [r.to_dict() for r in applicable_rules]
        }
    
    def get_required_region(
        self,
        database_name: str,
        connection_string: Optional[str] = None
    ) -> Optional[DataRegion]:
        """
        Get required region for a database.
        
        Args:
            database_name: Database name
            connection_string: Optional connection string
            
        Returns:
            Required DataRegion or None
        """
        for rule in self._rules.values():
            if not rule.is_active:
                continue
            
            for pattern in rule.database_patterns:
                if re.search(pattern, database_name, re.IGNORECASE):
                    return rule.region
                if connection_string and re.search(pattern, connection_string, re.IGNORECASE):
                    return rule.region
        
        return None

