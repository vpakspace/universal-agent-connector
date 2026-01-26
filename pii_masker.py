"""
PII Masking System for MCP Governance
Detects and masks sensitive fields in tool execution results
"""

import re
import json
from typing import Dict, Any, List, Optional, Union
from copy import deepcopy


class PIIMasker:
    """
    PII (Personally Identifiable Information) masker.
    Detects and masks sensitive data like emails, phone numbers, SSNs, credit cards.
    """
    
    # Regex patterns for detecting PII
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})\b')
    SSN_PATTERN = re.compile(r'\b(\d{3})-?(\d{2})-?(\d{4})\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})\b')
    
    def __init__(self):
        """Initialize PII masker"""
        pass
    
    def mask_sensitive_fields(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]], str, Any],
        sensitivity_level: str = "standard"
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], str, Any]:
        """
        Mask sensitive fields in data
        
        Args:
            data: Data to mask (dict, list of dicts, string, or any value)
            sensitivity_level: Sensitivity level ("standard" or "strict")
                              - standard: Keep last 4 digits for phone/SSN
                              - strict: Full masking with asterisks
        
        Returns:
            Masked copy of data
        """
        if isinstance(data, dict):
            return self._mask_dict(data, sensitivity_level)
        elif isinstance(data, list):
            return [self.mask_sensitive_fields(item, sensitivity_level) for item in data]
        elif isinstance(data, str):
            return self._mask_string(data, sensitivity_level)
        else:
            # For other types (int, bool, None, etc.), return as-is
            return data
    
    def _mask_dict(self, data: Dict[str, Any], sensitivity_level: str) -> Dict[str, Any]:
        """Mask sensitive fields in a dictionary"""
        masked = deepcopy(data)
        
        for key, value in masked.items():
            # Check if key suggests sensitive data
            key_lower = key.lower()
            if any(term in key_lower for term in ['email', 'phone', 'ssn', 'social', 'credit', 'card', 'pii']):
                if isinstance(value, str):
                    masked[key] = self._mask_string(value, sensitivity_level)
                elif isinstance(value, (dict, list)):
                    masked[key] = self.mask_sensitive_fields(value, sensitivity_level)
            else:
                # Recursively mask nested structures
                if isinstance(value, (dict, list, str)):
                    masked[key] = self.mask_sensitive_fields(value, sensitivity_level)
        
        return masked
    
    def _mask_string(self, text: str, sensitivity_level: str) -> str:
        """
        Mask sensitive data in a string
        
        Args:
            text: Text to mask
            sensitivity_level: Sensitivity level
        
        Returns:
            Masked text
        """
        if not isinstance(text, str):
            return text
        
        masked = text
        
        # Mask emails: replace with "***@***.com"
        masked = self.EMAIL_PATTERN.sub("***@***.com", masked)
        
        # Mask phone numbers
        if sensitivity_level == "strict":
            masked = self.PHONE_PATTERN.sub("(***) ***-****", masked)
        else:
            # Keep last 4 digits: (***) ***-1234
            def phone_replacer(match):
                groups = match.groups()
                if len(groups) == 3:
                    return f"(***) ***-{groups[2]}"
                return "(***) ***-****"
            masked = self.PHONE_PATTERN.sub(phone_replacer, masked)
        
        # Mask SSNs
        if sensitivity_level == "strict":
            masked = self.SSN_PATTERN.sub("***-**-****", masked)
        else:
            # Keep last 4 digits: ***-**-1234
            def ssn_replacer(match):
                groups = match.groups()
                if len(groups) == 3:
                    return f"***-**-{groups[2]}"
                return "***-**-****"
            masked = self.SSN_PATTERN.sub(ssn_replacer, masked)
        
        # Mask credit cards
        if sensitivity_level == "strict":
            masked = self.CREDIT_CARD_PATTERN.sub("****-****-****-****", masked)
        else:
            # Keep last 4 digits: ****-****-****-1234
            def cc_replacer(match):
                groups = match.groups()
                if len(groups) == 4:
                    return f"****-****-****-{groups[3]}"
                return "****-****-****-****"
            masked = self.CREDIT_CARD_PATTERN.sub(cc_replacer, masked)
        
        return masked
    
    def detect_pii(self, data: Union[Dict[str, Any], str]) -> List[str]:
        """
        Detect what types of PII are present in data
        
        Args:
            data: Data to analyze
        
        Returns:
            List of detected PII types (e.g., ["email", "phone", "ssn"])
        """
        detected = []
        
        if isinstance(data, str):
            text = data
        elif isinstance(data, dict):
            text = json.dumps(data) if data else ""
        else:
            return []
        
        if self.EMAIL_PATTERN.search(text):
            detected.append("email")
        if self.PHONE_PATTERN.search(text):
            detected.append("phone")
        if self.SSN_PATTERN.search(text):
            detected.append("ssn")
        if self.CREDIT_CARD_PATTERN.search(text):
            detected.append("credit_card")
        
        return detected


# Global instance
pii_masker = PIIMasker()


def mask_sensitive_fields(
    data: Union[Dict[str, Any], List[Dict[str, Any]], str, Any],
    sensitivity_level: str = "standard"
) -> Union[Dict[str, Any], List[Dict[str, Any]], str, Any]:
    """
    Convenience function to mask sensitive fields
    
    Args:
        data: Data to mask
        sensitivity_level: Sensitivity level ("standard" or "strict")
    
    Returns:
        Masked copy of data
    """
    return pii_masker.mask_sensitive_fields(data, sensitivity_level)

