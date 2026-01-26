"""
Audit log anonymization
Anonymizes user identities in audit logs while maintaining accountability
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import uuid
import re


class AnonymizationMethod(Enum):
    """Anonymization methods"""
    HASH = "hash"  # Hash with salt
    PREFIX = "prefix"  # Prefix with "user_"
    REDACT = "redact"  # Replace with "[REDACTED]"
    MASK = "mask"  # Mask with asterisks
    PSEUDONYMIZE = "pseudonymize"  # Replace with pseudonym


@dataclass
class AnonymizationRule:
    """An anonymization rule"""
    rule_id: str
    name: str
    field_patterns: List[str]  # Field names or patterns to anonymize
    method: AnonymizationMethod
    salt: Optional[str] = None  # Salt for hashing
    is_active: bool = True
    description: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'field_patterns': self.field_patterns,
            'method': self.method.value,
            'is_active': self.is_active,
            'description': self.description,
            'metadata': self.metadata or {}
        }


class AuditAnonymizer:
    """
    Anonymizes user identities in audit logs.
    """
    
    def __init__(self, default_salt: Optional[str] = None):
        """
        Initialize audit anonymizer.
        
        Args:
            default_salt: Default salt for hashing
        """
        # rule_id -> AnonymizationRule
        self._rules: Dict[str, AnonymizationRule] = {}
        self.default_salt = default_salt or "default_salt_change_in_production"
    
    def create_rule(
        self,
        name: str,
        field_patterns: List[str],
        method: AnonymizationMethod,
        salt: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnonymizationRule:
        """
        Create an anonymization rule.
        
        Args:
            name: Rule name
            field_patterns: Field names or patterns to anonymize
            method: Anonymization method
            salt: Optional salt for hashing
            description: Optional description
            metadata: Optional metadata
            
        Returns:
            AnonymizationRule object
        """
        rule_id = str(uuid.uuid4())
        
        rule = AnonymizationRule(
            rule_id=rule_id,
            name=name,
            field_patterns=field_patterns,
            method=method,
            salt=salt or self.default_salt,
            description=description,
            metadata=metadata or {}
        )
        
        self._rules[rule_id] = rule
        return rule
    
    def get_rule(self, rule_id: str) -> Optional[AnonymizationRule]:
        """Get an anonymization rule"""
        return self._rules.get(rule_id)
    
    def list_rules(self, is_active: Optional[bool] = None) -> List[AnonymizationRule]:
        """
        List anonymization rules.
        
        Args:
            is_active: Filter by active status
            
        Returns:
            List of AnonymizationRule objects
        """
        rules = list(self._rules.values())
        
        if is_active is not None:
            rules = [r for r in rules if r.is_active == is_active]
        
        return rules
    
    def update_rule(
        self,
        rule_id: str,
        name: Optional[str] = None,
        field_patterns: Optional[List[str]] = None,
        method: Optional[AnonymizationMethod] = None,
        is_active: Optional[bool] = None,
        description: Optional[str] = None
    ) -> Optional[AnonymizationRule]:
        """
        Update an anonymization rule.
        
        Args:
            rule_id: Rule ID
            name: New name
            field_patterns: New field patterns
            method: New method
            is_active: Active status
            description: New description
            
        Returns:
            Updated AnonymizationRule or None if not found
        """
        rule = self._rules.get(rule_id)
        if not rule:
            return None
        
        if name is not None:
            rule.name = name
        
        if field_patterns is not None:
            rule.field_patterns = field_patterns
        
        if method is not None:
            rule.method = method
        
        if is_active is not None:
            rule.is_active = is_active
        
        if description is not None:
            rule.description = description
        
        return rule
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete an anonymization rule"""
        if rule_id not in self._rules:
            return False
        
        del self._rules[rule_id]
        return True
    
    def anonymize_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize a log entry.
        
        Args:
            log_entry: Log entry dictionary
            
        Returns:
            Anonymized log entry
        """
        anonymized = log_entry.copy()
        
        # Apply all active rules
        for rule in self._rules.values():
            if not rule.is_active:
                continue
            
            for field_pattern in rule.field_patterns:
                # Check if field exists (exact match or pattern)
                for key in anonymized.keys():
                    if self._matches_pattern(key, field_pattern):
                        anonymized[key] = self._anonymize_value(
                            anonymized[key],
                            rule.method,
                            rule.salt
                        )
                
                # Also check nested fields
                anonymized = self._anonymize_nested(anonymized, field_pattern, rule)
        
        return anonymized
    
    def _matches_pattern(self, field_name: str, pattern: str) -> bool:
        """Check if field name matches pattern"""
        # Exact match
        if field_name.lower() == pattern.lower():
            return True
        
        # Regex match
        try:
            if re.search(pattern, field_name, re.IGNORECASE):
                return True
        except re.error:
            pass
        
        # Partial match (contains)
        if pattern.lower() in field_name.lower():
            return True
        
        return False
    
    def _anonymize_value(
        self,
        value: Any,
        method: AnonymizationMethod,
        salt: str
    ) -> Any:
        """Anonymize a value"""
        if value is None:
            return None
        
        value_str = str(value)
        
        if method == AnonymizationMethod.HASH:
            # Hash with salt
            hash_obj = hashlib.sha256((value_str + salt).encode())
            return f"hash_{hash_obj.hexdigest()[:16]}"
        
        elif method == AnonymizationMethod.PREFIX:
            return f"user_{hashlib.md5((value_str + salt).encode()).hexdigest()[:8]}"
        
        elif method == AnonymizationMethod.REDACT:
            return "[REDACTED]"
        
        elif method == AnonymizationMethod.MASK:
            if len(value_str) <= 4:
                return "****"
            return value_str[:2] + "*" * (len(value_str) - 4) + value_str[-2:]
        
        elif method == AnonymizationMethod.PSEUDONYMIZE:
            # Generate consistent pseudonym
            hash_obj = hashlib.md5((value_str + salt).encode())
            return f"user_{hash_obj.hexdigest()[:12]}"
        
        return value
    
    def _anonymize_nested(
        self,
        obj: Any,
        field_pattern: str,
        rule: AnonymizationRule
    ) -> Any:
        """Anonymize nested structures"""
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if self._matches_pattern(key, field_pattern):
                    result[key] = self._anonymize_value(value, rule.method, rule.salt)
                elif isinstance(value, (dict, list)):
                    result[key] = self._anonymize_nested(value, field_pattern, rule)
                else:
                    result[key] = value
            return result
        
        elif isinstance(obj, list):
            return [
                self._anonymize_nested(item, field_pattern, rule) if isinstance(item, (dict, list))
                else self._anonymize_value(item, rule.method, rule.salt) if self._matches_pattern(str(item), field_pattern)
                else item
                for item in obj
            ]
        
        return obj
    
    def anonymize_batch(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Anonymize a batch of log entries.
        
        Args:
            log_entries: List of log entry dictionaries
            
        Returns:
            List of anonymized log entries
        """
        return [self.anonymize_log_entry(entry) for entry in log_entries]

