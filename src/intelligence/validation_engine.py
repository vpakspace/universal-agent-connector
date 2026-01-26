"""
Generic Validation Engine (JAG Universal)

Dynamically adapts JAG-003 guardrails to any ontology axioms.
Validates operations against OWL restrictions, SHACL shapes, or YAML rules.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from .ontology_adapter import OntologyAxiom, OntologyClass, OntologyProperty


@dataclass
class ValidationResult:
    """Result of operation validation"""
    is_valid: bool
    violations: List[str] = None  # type: ignore
    warnings: List[str] = None  # type: ignore
    suggestions: List[str] = None  # type: ignore
    
    def __post_init__(self):
        if self.violations is None:
            self.violations = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []


class AxiomValidator:
    """
    Validates operations against ontology axioms.
    
    Supports common restriction types:
    - Age constraints (minAge, maxAge)
    - Cardinality (exactly 1, at least 2, etc.)
    - Type restrictions (only accepts X class)
    - Custom business rules
    """
    
    def __init__(self, axioms: List[OntologyAxiom]):
        """
        Initialize validator with axioms.
        
        Args:
            axioms: List of ontology axioms to validate against
        """
        self.axioms = axioms
        self.axiom_index = self._build_axiom_index()
    
    def _build_axiom_index(self) -> Dict[str, List[OntologyAxiom]]:
        """Build index of axioms by subject"""
        index = {}
        for axiom in self.axioms:
            if axiom.subject not in index:
                index[axiom.subject] = []
            index[axiom.subject].append(axiom)
        return index
    
    def validate_constraint(
        self,
        subject: str,
        property_name: str,
        value: Any
    ) -> ValidationResult:
        """
        Validate a property value against constraints.
        
        Args:
            subject: Class or property URI
            property_name: Property name
            value: Value to validate
            
        Returns:
            ValidationResult
        """
        violations = []
        warnings = []
        
        # Get relevant axioms
        relevant_axioms = self.axiom_index.get(subject, [])
        
        for axiom in relevant_axioms:
            # Check age constraints
            if 'age' in property_name.lower() or 'age' in axiom.predicate.lower():
                result = self._validate_age_constraint(axiom, value)
                if not result.is_valid:
                    violations.extend(result.violations)
                warnings.extend(result.warnings)
            
            # Check cardinality
            if 'cardinality' in axiom.predicate.lower() or 'exactly' in axiom.predicate.lower():
                result = self._validate_cardinality(axiom, value)
                if not result.is_valid:
                    violations.extend(result.violations)
            
            # Check type restrictions
            if 'type' in axiom.predicate.lower() or 'only' in axiom.predicate.lower():
                result = self._validate_type_restriction(axiom, value)
                if not result.is_valid:
                    violations.extend(result.violations)
        
        return ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            warnings=warnings
        )
    
    def _validate_age_constraint(
        self,
        axiom: OntologyAxiom,
        value: Any
    ) -> ValidationResult:
        """Validate age constraints"""
        violations = []
        warnings = []
        
        try:
            age = int(value)
            
            # Check minAge
            if 'min' in axiom.predicate.lower() or 'minAge' in axiom.predicate.lower():
                min_age = int(axiom.object) if isinstance(axiom.object, (int, str)) else 0
                if age < min_age:
                    violations.append(f"Age {age} is below minimum {min_age}")
            
            # Check maxAge
            if 'max' in axiom.predicate.lower() or 'maxAge' in axiom.predicate.lower():
                max_age = int(axiom.object) if isinstance(axiom.object, (int, str)) else 999
                if age > max_age:
                    violations.append(f"Age {age} exceeds maximum {max_age}")
        
        except (ValueError, TypeError):
            violations.append(f"Invalid age value: {value}")
        
        return ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            warnings=warnings
        )
    
    def _validate_cardinality(
        self,
        axiom: OntologyAxiom,
        value: Any
    ) -> ValidationResult:
        """Validate cardinality constraints"""
        violations = []
        
        # Check if value is a list/collection
        if isinstance(value, (list, tuple)):
            count = len(value)
        else:
            count = 1 if value is not None else 0
        
        # Parse cardinality from axiom
        if 'exactly' in axiom.predicate.lower():
            exact = int(axiom.object) if isinstance(axiom.object, (int, str)) else 1
            if count != exact:
                violations.append(f"Cardinality must be exactly {exact}, got {count}")
        
        elif 'min' in axiom.predicate.lower():
            min_card = int(axiom.object) if isinstance(axiom.object, (int, str)) else 0
            if count < min_card:
                violations.append(f"Cardinality must be at least {min_card}, got {count}")
        
        elif 'max' in axiom.predicate.lower():
            max_card = int(axiom.object) if isinstance(axiom.object, (int, str)) else 999
            if count > max_card:
                violations.append(f"Cardinality must be at most {max_card}, got {count}")
        
        return ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations
        )
    
    def _validate_type_restriction(
        self,
        axiom: OntologyAxiom,
        value: Any
    ) -> ValidationResult:
        """Validate type restrictions"""
        violations = []
        
        # Check if value matches allowed type
        allowed_type = str(axiom.object)
        value_type = type(value).__name__
        
        # Simple type checking (can be extended)
        if 'only' in axiom.predicate.lower():
            # Only accepts specific type
            if value_type.lower() not in allowed_type.lower():
                violations.append(f"Value must be of type {allowed_type}, got {value_type}")
        
        return ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations
        )


class ValidationEngine:
    """
    Main validation engine that adapts JAG-003 guardrails to any ontology.
    
    Loads axioms from ontology and validates operations before execution.
    """
    
    def __init__(self, axioms: List[OntologyAxiom]):
        """
        Initialize validation engine.
        
        Args:
            axioms: List of ontology axioms
        """
        self.axioms = axioms
        self.validator = AxiomValidator(axioms)
    
    def validate_operation(
        self,
        tool_call: Dict[str, Any],
        ontology_class: str,
        properties: List[OntologyProperty]
    ) -> ValidationResult:
        """
        Validate a tool call operation against ontology axioms.
        
        Args:
            tool_call: Tool call parameters
            ontology_class: Class URI being operated on
            properties: List of properties for this class
            
        Returns:
            ValidationResult
        """
        violations = []
        warnings = []
        suggestions = []
        
        # Validate each parameter against relevant properties
        for prop in properties:
            if prop.domain == ontology_class or ontology_class in (prop.domain or ''):
                prop_name = prop.label or prop.uri.split('#')[-1]
                
                # Check if this property is in the tool call
                if prop_name.lower() in [k.lower() for k in tool_call.keys()]:
                    value = tool_call.get(prop_name, tool_call.get(prop_name.lower()))
                    
                    if value is not None:
                        # Validate against axioms
                        result = self.validator.validate_constraint(
                            ontology_class,
                            prop_name,
                            value
                        )
                        
                        if not result.is_valid:
                            violations.extend(result.violations)
                        warnings.extend(result.warnings)
        
        # Check required properties (cardinality min > 0)
        for prop in properties:
            if prop.domain == ontology_class:
                prop_name = prop.label or prop.uri.split('#')[-1]
                if prop.cardinality and prop.cardinality.get('min', 0) > 0:
                    if prop_name.lower() not in [k.lower() for k in tool_call.keys()]:
                        violations.append(f"Required property '{prop_name}' is missing")
        
        return ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            suggestions=suggestions
        )
    
    @classmethod
    def load_axioms(cls, ontology_data: Dict[str, Any], adapter: Any) -> 'ValidationEngine':
        """
        Load axioms from ontology and create validation engine.
        
        Args:
            ontology_data: Parsed ontology data
            adapter: OntologyAdapter instance
            
        Returns:
            ValidationEngine instance
        """
        axioms = adapter.extract_axioms(ontology_data)
        return cls(axioms)


def validate_operation(
    tool_call: Dict[str, Any],
    ontology_class: str,
    properties: List[OntologyProperty],
    axioms: List[OntologyAxiom]
) -> ValidationResult:
    """
    Convenience function to validate an operation.
    
    Args:
        tool_call: Tool call parameters
        ontology_class: Class URI
        properties: List of properties
        axioms: List of axioms
        
    Returns:
        ValidationResult
    """
    engine = ValidationEngine(axioms)
    return engine.validate_operation(tool_call, ontology_class, properties)

