"""
Type Compatibility Checker for Entity Disambiguation (JAG-001)

Prevents merging entities with incompatible types (e.g., "Person" + "Organization")
Uses business_ontology.json to define forbidden type merges.
"""

import json
import os
from typing import Dict, List, Set, Optional, Tuple


class TypeCompatibilityError(Exception):
    """Raised when attempting to merge incompatible entity types"""
    
    def __init__(self, entity_name: str, existing_type: str, new_type: str, reason: str):
        self.entity_name = entity_name
        self.existing_type = existing_type
        self.new_type = new_type
        self.reason = reason
        super().__init__(self.__str__())
    
    def __str__(self):
        return (
            f"Cannot merge entity '{self.entity_name}': "
            f"existing type '{self.existing_type}' is incompatible with new type '{self.new_type}'. "
            f"Reason: {self.reason}"
        )


class TypeChecker:
    """
    Checks type compatibility for entity merging based on business ontology.
    
    Uses business_ontology.json to define:
    - Forbidden type merges (e.g., Person + Organization)
    - Compatible type hierarchies
    - Type aliases
    """
    
    # Default forbidden merges (can be overridden by ontology)
    DEFAULT_FORBIDDEN_MERGES = {
        ("Person", "Organization"),
        ("Person", "Location"),
        ("Organization", "Location"),
        ("Product", "Service"),
        ("Animal", "Company"),
        ("Animal", "Brand"),
        ("Company", "Animal"),
        ("Brand", "Animal"),
    }
    
    # Type hierarchies (subtypes can merge with parent types)
    TYPE_HIERARCHIES = {
        "Entity": ["Person", "Organization", "Location", "Product", "Service", "Event"],
        "Business": ["Company", "Brand", "Product", "Service"],
        "Living": ["Person", "Animal"],
    }
    
    def __init__(self, ontology_path: Optional[str] = None):
        """
        Initialize type checker with ontology.
        
        Args:
            ontology_path: Path to business_ontology.json. If None, uses default location.
        """
        if ontology_path is None:
            # Default to business_ontology.json in project root
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            ontology_path = os.path.join(current_dir, "business_ontology.json")
        
        self.ontology_path = ontology_path
        self.forbidden_merges: Set[Tuple[str, str]] = set()
        self.type_aliases: Dict[str, List[str]] = {}
        self.type_hierarchies: Dict[str, List[str]] = {}
        
        self._load_ontology()
    
    def _load_ontology(self) -> None:
        """Load ontology and extract type compatibility rules"""
        try:
            if os.path.exists(self.ontology_path):
                with open(self.ontology_path, 'r', encoding='utf-8') as f:
                    ontology = json.load(f)
                
                # Extract forbidden merges from ontology
                forbidden_merges = ontology.get("forbidden_merges", [])
                for merge_pair in forbidden_merges:
                    if isinstance(merge_pair, list) and len(merge_pair) == 2:
                        # Normalize order (alphabetical)
                        type1, type2 = sorted(merge_pair)
                        self.forbidden_merges.add((type1, type2))
                
                # Extract type aliases
                self.type_aliases = ontology.get("type_aliases", {})
                
                # Extract type hierarchies
                self.type_hierarchies = ontology.get("type_hierarchies", {})
                
                # Merge with defaults
                self.forbidden_merges.update(self.DEFAULT_FORBIDDEN_MERGES)
                self.type_hierarchies.update(self.TYPE_HIERARCHIES)
            else:
                # Use defaults if ontology file doesn't exist
                self.forbidden_merges = self.DEFAULT_FORBIDDEN_MERGES.copy()
                self.type_hierarchies = self.TYPE_HIERARCHIES.copy()
        except Exception as e:
            # Fallback to defaults on error
            print(f"Warning: Failed to load ontology from {self.ontology_path}: {e}")
            self.forbidden_merges = self.DEFAULT_FORBIDDEN_MERGES.copy()
            self.type_hierarchies = self.TYPE_HIERARCHIES.copy()
    
    def _normalize_type(self, entity_type: str) -> str:
        """
        Normalize entity type using aliases.
        
        Args:
            entity_type: Entity type to normalize
            
        Returns:
            Normalized type name
        """
        # Check if type is an alias
        for canonical, aliases in self.type_aliases.items():
            if entity_type in aliases or entity_type == canonical:
                return canonical
        
        return entity_type
    
    def _are_types_compatible(self, type1: str, type2: str) -> bool:
        """
        Check if two types are compatible (can be merged).
        
        Args:
            type1: First entity type
            type2: Second entity type
            
        Returns:
            True if types are compatible, False otherwise
        """
        # Same type is always compatible
        if type1 == type2:
            return True
        
        # Normalize types
        type1 = self._normalize_type(type1)
        type2 = self._normalize_type(type2)
        
        # Check if explicitly forbidden
        merge_pair = tuple(sorted([type1, type2]))
        if merge_pair in self.forbidden_merges:
            return False
        
        # Check type hierarchies (subtypes can merge with parent)
        for parent_type, subtypes in self.type_hierarchies.items():
            if type1 == parent_type and type2 in subtypes:
                return True
            if type2 == parent_type and type1 in subtypes:
                return True
            if type1 in subtypes and type2 in subtypes:
                # Both are subtypes of same parent - check if compatible
                return True
        
        # Default: compatible if not explicitly forbidden
        return True
    
    def check_compatibility(
        self,
        entity_name: str,
        existing_type: Optional[str],
        new_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if two entity types are compatible for merging.
        
        Args:
            entity_name: Name of the entity being checked
            existing_type: Existing entity type (if any)
            new_type: New entity type to merge
            
        Returns:
            Tuple of (is_compatible, reason)
            - is_compatible: True if types can be merged
            - reason: Explanation if incompatible, None if compatible
        """
        if existing_type is None:
            # No existing type, always compatible
            return True, None
        
        # Normalize types
        existing_type = self._normalize_type(existing_type)
        new_type = self._normalize_type(new_type)
        
        # Check compatibility
        if self._are_types_compatible(existing_type, new_type):
            return True, None
        
        # Types are incompatible
        merge_pair = tuple(sorted([existing_type, new_type]))
        reason = f"Types '{existing_type}' and '{new_type}' are explicitly forbidden from merging"
        
        return False, reason


# Global instance
_type_checker = None


def get_type_checker() -> TypeChecker:
    """Get or create global type checker instance"""
    global _type_checker
    if _type_checker is None:
        _type_checker = TypeChecker()
    return _type_checker


def type_compatibility_check(
    entity_name: str,
    existing_type: Optional[str],
    new_type: str
) -> None:
    """
    Check type compatibility and raise error if incompatible.
    
    This is the main function to call during node creation (US-015).
    
    Args:
        entity_name: Name of the entity
        existing_type: Existing entity type (if any)
        new_type: New entity type to merge
        
    Raises:
        TypeCompatibilityError: If types are incompatible
    """
    checker = get_type_checker()
    is_compatible, reason = checker.check_compatibility(
        entity_name, existing_type, new_type
    )
    
    if not is_compatible:
        raise TypeCompatibilityError(
            entity_name=entity_name,
            existing_type=existing_type or "Unknown",
            new_type=new_type,
            reason=reason or "Types are incompatible"
        )

