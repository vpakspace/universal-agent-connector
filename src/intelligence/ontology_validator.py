"""
Ontology Health Validator (JAG Universal)

Validates ontology structure before deployment.
Checks for MINE compatibility, disambiguation issues, and connectivity problems.
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from .ontology_adapter import OntologyClass, OntologyProperty, OntologyAxiom


class HealthStatus(str, Enum):
    """Ontology health status"""
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    FAILED = "FAILED"


@dataclass
class HealthIssue:
    """Represents a health issue found in ontology"""
    severity: HealthStatus
    category: str  # e.g., "disambiguation", "connectivity", "mine"
    issue: str
    recommendation: str
    affected_classes: List[str] = field(default_factory=list)


@dataclass
class OntologyHealthReport:
    """Comprehensive health report for ontology"""
    status: HealthStatus
    mine_estimate: float  # Estimated MINE score (0-1)
    issues: List[HealthIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    def is_deployable(self, min_mine: float = 0.75) -> bool:
        """Check if ontology is deployable based on MINE threshold"""
        return (
            self.status != HealthStatus.FAILED and
            self.mine_estimate >= min_mine
        )


class OntologyValidator:
    """
    Validates ontology health before deployment.
    
    Checks for:
    - Missing inverse properties (breaks JAG-004 connectivity)
    - Ambiguous class names (breaks JAG-001 disambiguation)
    - Circular dependencies (causes infinite loops)
    - MINE compatibility (can achieve MINE > 0.75)
    """
    
    def __init__(self, mine_target: float = 0.75):
        """
        Initialize ontology validator.
        
        Args:
            mine_target: Target MINE score (default: 0.75)
        """
        self.mine_target = mine_target
    
    def validate_ontology_health(
        self,
        classes: List[OntologyClass],
        properties: List[OntologyProperty],
        axioms: List[OntologyAxiom]
    ) -> OntologyHealthReport:
        """
        Perform comprehensive health check on ontology.
        
        Args:
            classes: List of ontology classes
            properties: List of ontology properties
            axioms: List of ontology axioms
            
        Returns:
            OntologyHealthReport with health status and recommendations
        """
        issues = []
        recommendations = []
        statistics = {
            "num_classes": len(classes),
            "num_properties": len(properties),
            "num_axioms": len(axioms)
        }
        
        # Check 1: Missing inverse properties (JAG-004 connectivity)
        connectivity_issues = self._check_inverse_properties(properties)
        issues.extend(connectivity_issues)
        
        # Check 2: Ambiguous class names (JAG-001 disambiguation)
        disambiguation_issues = self._check_ambiguous_classes(classes)
        issues.extend(disambiguation_issues)
        
        # Check 3: Circular dependencies
        circular_issues = self._check_circular_dependencies(classes)
        issues.extend(circular_issues)
        
        # Check 4: MINE compatibility estimation
        mine_estimate, mine_issues = self._estimate_mine_score(classes, properties)
        issues.extend(mine_issues)
        
        # Determine overall status
        if any(i.severity == HealthStatus.FAILED for i in issues):
            status = HealthStatus.FAILED
        elif any(i.severity == HealthStatus.CRITICAL for i in issues):
            status = HealthStatus.CRITICAL
        elif any(i.severity == HealthStatus.WARNING for i in issues):
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.HEALTHY
        
        # Generate recommendations
        if mine_estimate < self.mine_target:
            recommendations.append(
                f"MINE score estimate ({mine_estimate:.2f}) is below target ({self.mine_target}). "
                "Add more properties and relationships to improve connectivity."
            )
        
        if connectivity_issues:
            recommendations.append(
                "Add inverse properties to improve graph connectivity (JAG-004)."
            )
        
        if disambiguation_issues:
            recommendations.append(
                "Resolve ambiguous class names to prevent disambiguation conflicts (JAG-001)."
            )
        
        return OntologyHealthReport(
            status=status,
            mine_estimate=mine_estimate,
            issues=issues,
            recommendations=recommendations,
            statistics=statistics
        )
    
    def _check_inverse_properties(self, properties: List[OntologyProperty]) -> List[HealthIssue]:
        """Check for missing inverse properties (affects JAG-004 connectivity)"""
        issues = []
        properties_without_inverse = []
        
        for prop in properties:
            # Check if property should have an inverse but doesn't
            if prop.inverse_property is None:
                # Check if it's an object property (relationships should have inverses)
                if prop.range and not prop.range.startswith('http://www.w3.org/2001/XMLSchema#'):
                    properties_without_inverse.append(prop.uri)
        
        if properties_without_inverse:
            issues.append(HealthIssue(
                severity=HealthStatus.WARNING,
                category="connectivity",
                issue=f"{len(properties_without_inverse)} properties missing inverse properties",
                recommendation="Add inverse properties to improve graph connectivity and enable bidirectional queries",
                affected_classes=properties_without_inverse[:10]  # Limit to first 10
            ))
        
        return issues
    
    def _check_ambiguous_classes(self, classes: List[OntologyClass]) -> List[HealthIssue]:
        """Check for ambiguous class names (affects JAG-001 disambiguation)"""
        issues = []
        
        # Group classes by label
        label_to_classes: Dict[str, List[OntologyClass]] = {}
        for cls in classes:
            label = cls.label or cls.uri.split('#')[-1].split('/')[-1]
            if label not in label_to_classes:
                label_to_classes[label] = []
            label_to_classes[label].append(cls)
        
        # Find ambiguous labels (same label, different URIs)
        ambiguous_labels = {
            label: cls_list
            for label, cls_list in label_to_classes.items()
            if len(cls_list) > 1
        }
        
        if ambiguous_labels:
            for label, cls_list in ambiguous_labels.items():
                if len(cls_list) > 1:
                    # Check if they have incompatible parent classes
                    parent_sets = [set(cls.parent_classes) for cls in cls_list]
                    if len(set(tuple(sorted(ps)) for ps in parent_sets)) > 1:
                        # Different parent classes - potential disambiguation issue
                        issues.append(HealthIssue(
                            severity=HealthStatus.WARNING,
                            category="disambiguation",
                            issue=f"Ambiguous class name '{label}' with {len(cls_list)} different definitions",
                            recommendation=f"Rename classes to be unique or add type hierarchies to resolve ambiguity",
                            affected_classes=[cls.uri for cls in cls_list]
                        ))
        
        return issues
    
    def _check_circular_dependencies(self, classes: List[OntologyClass]) -> List[HealthIssue]:
        """Check for circular dependencies in class hierarchy"""
        issues = []
        
        # Build parent-child map
        class_map = {cls.uri: cls for cls in classes}
        visited = set()
        rec_stack = set()
        
        def has_cycle(class_uri: str) -> bool:
            """Check for cycles in class hierarchy"""
            if class_uri in rec_stack:
                return True
            if class_uri in visited:
                return False
            
            visited.add(class_uri)
            rec_stack.add(class_uri)
            
            if class_uri in class_map:
                cls = class_map[class_uri]
                for parent_uri in cls.parent_classes:
                    if has_cycle(parent_uri):
                        return True
            
            rec_stack.remove(class_uri)
            return False
        
        # Check each class for cycles
        for cls in classes:
            if has_cycle(cls.uri):
                issues.append(HealthIssue(
                    severity=HealthStatus.CRITICAL,
                    category="circular_dependency",
                    issue=f"Circular dependency detected in class hierarchy for '{cls.label or cls.uri}'",
                    recommendation="Remove circular references in class hierarchy",
                    affected_classes=[cls.uri]
                ))
                break  # Report first cycle found
        
        return issues
    
    def _estimate_mine_score(
        self,
        classes: List[OntologyClass],
        properties: List[OntologyProperty]
    ) -> tuple[float, List[HealthIssue]]:
        """
        Estimate MINE score based on ontology structure.
        
        Simplified estimation based on:
        - Number of classes and properties
        - Property connectivity
        - Inverse property coverage
        
        Returns:
            Tuple of (estimated_mine_score, issues)
        """
        issues = []
        
        # Base score from structure richness
        num_classes = len(classes)
        num_properties = len(properties)
        
        # Connectivity score (based on inverse properties)
        properties_with_inverse = sum(1 for p in properties if p.inverse_property)
        inverse_coverage = properties_with_inverse / num_properties if num_properties > 0 else 0.0
        
        # Property-to-class ratio (more properties per class = richer structure)
        props_per_class = num_properties / num_classes if num_classes > 0 else 0.0
        
        # Estimate components (simplified)
        # Information Retention: Based on property richness
        retention_score = min(1.0, props_per_class / 3.0)  # Target: 3 properties per class
        
        # Clustering Quality: Based on class uniqueness
        unique_labels = len(set(cls.label or cls.uri for cls in classes))
        clustering_score = unique_labels / num_classes if num_classes > 0 else 0.0
        
        # Connectivity: Based on inverse property coverage
        connectivity_score = inverse_coverage
        
        # Weighted MINE estimate
        mine_estimate = (0.4 * retention_score) + (0.3 * clustering_score) + (0.3 * connectivity_score)
        
        # Generate issues if below target
        if mine_estimate < self.mine_target:
            issues.append(HealthIssue(
                severity=HealthStatus.WARNING,
                category="mine",
                issue=f"Estimated MINE score ({mine_estimate:.2f}) below target ({self.mine_target})",
                recommendation="Add more properties, relationships, and inverse properties to improve MINE score",
                affected_classes=[]
            ))
        
        if inverse_coverage < 0.5:
            issues.append(HealthIssue(
                severity=HealthStatus.WARNING,
                category="connectivity",
                issue=f"Only {inverse_coverage:.1%} of properties have inverse properties",
                recommendation="Add inverse properties to improve graph connectivity",
                affected_classes=[]
            ))
        
        return mine_estimate, issues


def validate_ontology_health(
    classes: List[OntologyClass],
    properties: List[OntologyProperty],
    axioms: List[OntologyAxiom],
    mine_target: float = 0.75
) -> OntologyHealthReport:
    """
    Convenience function to validate ontology health.
    
    Args:
        classes: List of ontology classes
        properties: List of ontology properties
        axioms: List of ontology axioms
        mine_target: Target MINE score
        
    Returns:
        OntologyHealthReport
    """
    validator = OntologyValidator(mine_target=mine_target)
    return validator.validate_ontology_health(classes, properties, axioms)

