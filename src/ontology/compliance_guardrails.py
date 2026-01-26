"""
Ontology Compliance Guardrails (JAG-003)

Prevents impossible relationships like:
- "Antibiotic treats Virus" (antibiotics don't treat viruses)
- "Software Bug caused by Medication" (medication can't cause software bugs)
- "Vehicle treats Disease" (vehicles can't treat diseases)

Implements real-time compliance checking during edge creation with severity levels.
"""

import json
import os
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ViolationSeverity(str, Enum):
    """Severity levels for compliance violations"""
    CRITICAL = "CRITICAL"  # Impossible relationships (e.g., Medication → SoftwareBug)
    HIGH = "HIGH"  # Highly unlikely (e.g., Vehicle → Disease)
    MEDIUM = "MEDIUM"  # Unusual but possible (e.g., Person → Building)
    LOW = "LOW"  # Edge case (e.g., Organization → Location)


@dataclass
class ComplianceViolation:
    """Represents a compliance violation"""
    source_type: str
    target_type: str
    relationship_type: str
    severity: ViolationSeverity
    reason: str
    timestamp: str
    overridden: bool = False
    override_reason: Optional[str] = None
    override_by: Optional[str] = None
    override_timestamp: Optional[str] = None


@dataclass
class ComplianceResult:
    """Result of compliance check"""
    is_compliant: bool
    violations: List[ComplianceViolation] = field(default_factory=list)
    compliance_score: float = 1.0  # 1.0 = fully compliant, 0.0 = fully non-compliant
    total_relationships: int = 0
    violation_count: int = 0


class OntologyValidator:
    """
    Validates relationships against ontology rules.
    
    Prevents impossible relationships and flags violations by severity.
    Supports admin overrides with audit trail.
    """
    
    def __init__(self, rules_path: Optional[str] = None):
        """
        Initialize ontology validator.
        
        Args:
            rules_path: Path to forbidden_relationships.json (default: src/ontology/forbidden_relationships.json)
        """
        if rules_path is None:
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            rules_path = os.path.join(current_dir, "src", "ontology", "forbidden_relationships.json")
        
        self.rules_path = rules_path
        self.rules: Dict[str, Dict[str, List[str]]] = {}
        self.violations: List[ComplianceViolation] = []
        self.overrides: List[ComplianceViolation] = []
        
        self._load_rules()
    
    def _load_rules(self) -> None:
        """Load forbidden relationship rules from JSON file"""
        try:
            if os.path.exists(self.rules_path):
                with open(self.rules_path, 'r', encoding='utf-8') as f:
                    self.rules = json.load(f)
            else:
                # Use default rules if file doesn't exist
                self.rules = self._get_default_rules()
                # Create file with default rules
                os.makedirs(os.path.dirname(self.rules_path), exist_ok=True)
                with open(self.rules_path, 'w', encoding='utf-8') as f:
                    json.dump(self.rules, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to load rules from {self.rules_path}: {e}")
            self.rules = self._get_default_rules()
    
    def _get_default_rules(self) -> Dict[str, Dict[str, List[str]]]:
        """Get default forbidden relationship rules"""
        return {
            "Medication": {
                "allowed_targets": ["Disease", "Symptom", "Patient", "Condition"],
                "forbidden_targets": ["SoftwareBug", "Vehicle", "Building", "Location", "Event"]
            },
            "Antibiotic": {
                "allowed_targets": ["BacterialInfection", "Disease", "Patient"],
                "forbidden_targets": ["Virus", "ViralInfection", "SoftwareBug", "Vehicle"]
            },
            "Vehicle": {
                "allowed_targets": ["Location", "Person", "Route", "Destination"],
                "forbidden_targets": ["Disease", "Symptom", "Medication", "SoftwareBug"]
            },
            "SoftwareBug": {
                "allowed_targets": ["Software", "Code", "System", "Application"],
                "forbidden_targets": ["Medication", "Disease", "Patient", "Vehicle", "Building"]
            },
            "Building": {
                "allowed_targets": ["Location", "Person", "Organization", "Address"],
                "forbidden_targets": ["Disease", "Medication", "SoftwareBug", "Virus"]
            },
            "Person": {
                "allowed_targets": ["Location", "Organization", "Event", "Building"],
                "forbidden_targets": ["SoftwareBug", "Virus", "Code"]
            }
        }
    
    def _determine_severity(
        self,
        source_type: str,
        target_type: str,
        relationship_type: str
    ) -> ViolationSeverity:
        """
        Determine severity of violation.
        
        Args:
            source_type: Source entity type
            target_type: Target entity type
            relationship_type: Relationship type
            
        Returns:
            ViolationSeverity
        """
        # CRITICAL: Medical/physical impossibilities
        critical_patterns = [
            ("Medication", "SoftwareBug"),
            ("Antibiotic", "Virus"),
            ("Vehicle", "Disease"),
            ("Building", "Disease"),
            ("SoftwareBug", "Medication"),
            ("SoftwareBug", "Patient")
        ]
        
        if (source_type, target_type) in critical_patterns:
            return ViolationSeverity.CRITICAL
        
        # HIGH: Highly unlikely but not physically impossible
        high_patterns = [
            ("Vehicle", "Symptom"),
            ("Building", "Medication"),
            ("Person", "SoftwareBug")
        ]
        
        if (source_type, target_type) in high_patterns:
            return ViolationSeverity.HIGH
        
        # MEDIUM: Unusual but possible
        medium_patterns = [
            ("Person", "Building"),
            ("Organization", "Vehicle")
        ]
        
        if (source_type, target_type) in medium_patterns:
            return ViolationSeverity.MEDIUM
        
        # Default to LOW for other violations
        return ViolationSeverity.LOW
    
    def validate_relationship(
        self,
        source_type: str,
        target_type: str,
        relationship_type: str = "RELATED_TO"
    ) -> ComplianceResult:
        """
        Validate a relationship against ontology rules.
        
        This is the main method to call during edge creation.
        
        Args:
            source_type: Type of source entity
            target_type: Type of target entity
            relationship_type: Type of relationship
            
        Returns:
            ComplianceResult with validation status and violations
        """
        violations = []
        
        # Check if source type has rules
        if source_type in self.rules:
            rule = self.rules[source_type]
            
            # Check forbidden targets
            forbidden = rule.get("forbidden_targets", [])
            if target_type in forbidden:
                severity = self._determine_severity(source_type, target_type, relationship_type)
                violation = ComplianceViolation(
                    source_type=source_type,
                    target_type=target_type,
                    relationship_type=relationship_type,
                    severity=severity,
                    reason=f"{source_type} cannot have relationship with {target_type} (forbidden in ontology)",
                    timestamp=datetime.utcnow().isoformat()
                )
                violations.append(violation)
                self.violations.append(violation)
            
            # Check allowed targets (if specified, only these are allowed)
            allowed = rule.get("allowed_targets", [])
            if allowed and target_type not in allowed:
                # Not explicitly allowed - check if it's forbidden
                if target_type not in forbidden:
                    # Not explicitly forbidden either - allow but flag as LOW severity
                    severity = ViolationSeverity.LOW
                    violation = ComplianceViolation(
                        source_type=source_type,
                        target_type=target_type,
                        relationship_type=relationship_type,
                        severity=severity,
                        reason=f"{source_type} → {target_type} not in allowed targets list",
                        timestamp=datetime.utcnow().isoformat()
                    )
                    violations.append(violation)
                    self.violations.append(violation)
        
        is_compliant = len(violations) == 0
        
        return ComplianceResult(
            is_compliant=is_compliant,
            violations=violations,
            compliance_score=1.0 if is_compliant else 0.0,
            total_relationships=1,
            violation_count=len(violations)
        )
    
    def override_violation(
        self,
        violation: ComplianceViolation,
        override_reason: str,
        override_by: str
    ) -> None:
        """
        Override a violation with admin approval.
        
        Args:
            violation: Violation to override
            override_reason: Reason for override
            override_by: Admin user who approved override
        """
        violation.overridden = True
        violation.override_reason = override_reason
        violation.override_by = override_by
        violation.override_timestamp = datetime.utcnow().isoformat()
        
        self.overrides.append(violation)
    
    def validate_batch(
        self,
        relationships: List[Dict[str, str]]
    ) -> ComplianceResult:
        """
        Validate multiple relationships at once.
        
        Args:
            relationships: List of relationship dictionaries with:
                - source_type: Source entity type
                - target_type: Target entity type
                - relationship_type: Relationship type (optional)
        
        Returns:
            ComplianceResult with aggregated results
        """
        all_violations = []
        total = len(relationships)
        
        for rel in relationships:
            result = self.validate_relationship(
                source_type=rel.get("source_type", ""),
                target_type=rel.get("target_type", ""),
                relationship_type=rel.get("relationship_type", "RELATED_TO")
            )
            all_violations.extend(result.violations)
        
        # Calculate compliance score
        violation_count = len([v for v in all_violations if not v.overridden])
        compliance_score = 1.0 - (violation_count / total) if total > 0 else 1.0
        
        return ComplianceResult(
            is_compliant=violation_count == 0,
            violations=all_violations,
            compliance_score=compliance_score,
            total_relationships=total,
            violation_count=violation_count
        )
    
    def get_violations(
        self,
        severity: Optional[ViolationSeverity] = None,
        include_overridden: bool = False
    ) -> List[ComplianceViolation]:
        """
        Get all violations, optionally filtered by severity.
        
        Args:
            severity: Optional severity filter
            include_overridden: Include overridden violations
            
        Returns:
            List of violations
        """
        violations = self.violations
        
        if not include_overridden:
            violations = [v for v in violations if not v.overridden]
        
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        return violations
    
    def get_compliance_score(self) -> float:
        """
        Calculate overall compliance score.
        
        Returns:
            Compliance score: 1 - (violations / total_relationships)
        """
        total = len(self.violations)
        if total == 0:
            return 1.0
        
        non_overridden = len([v for v in self.violations if not v.overridden])
        return 1.0 - (non_overridden / total) if total > 0 else 1.0

