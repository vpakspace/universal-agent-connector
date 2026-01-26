"""
Jaguar Resolver - Entity Disambiguation Service (JAG-001)

Resolves ambiguous entity names like "Jaguar" (cat vs car company) using:
- Type compatibility checks
- Neighboring node context
- Unique URI assignment
- Audit logging
"""

import hashlib
import json
import os
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .type_checker import type_compatibility_check, TypeCompatibilityError, get_type_checker


@dataclass
class DisambiguationResult:
    """Result of entity disambiguation"""
    entity_name: str
    resolved_uri: str
    entity_type: str
    confidence: float
    method: str  # "type_check", "context", "unique_uri"
    context_nodes: List[str] = field(default_factory=list)
    conflicting_entities: List[Dict] = field(default_factory=list)
    decision_reason: str = ""


class DisambiguationService:
    """
    Service for disambiguating entities during graph ingestion.
    
    Prevents conflating entities with same name but different types
    (e.g., "Jaguar" the cat vs "Jaguar" the car company).
    """
    
    def __init__(
        self,
        ontology_path: Optional[str] = None,
        audit_log_path: Optional[str] = None
    ):
        """
        Initialize disambiguation service.
        
        Args:
            ontology_path: Path to business_ontology.json
            audit_log_path: Path to audit log file (JSONL format)
        """
        self.type_checker = get_type_checker()
        
        # Entity registry: name -> List of (uri, type, metadata)
        self.entity_registry: Dict[str, List[Dict]] = {}
        
        # URI registry: uri -> entity info
        self.uri_registry: Dict[str, Dict] = {}
        
        # Audit log path
        if audit_log_path is None:
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            audit_log_path = os.path.join(current_dir, "disambiguation_audit.jsonl")
        self.audit_log_path = audit_log_path
        
        # Ensure audit log directory exists
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
    
    def _generate_unique_uri(
        self,
        entity_name: str,
        entity_type: str,
        existing_uris: Set[str]
    ) -> str:
        """
        Generate unique URI for entity.
        
        Format: entity://{type}/{normalized_name}_{suffix}
        
        Args:
            entity_name: Name of the entity
            entity_type: Type of the entity
            existing_uris: Set of existing URIs to avoid collisions
            
        Returns:
            Unique URI string
        """
        # Normalize entity name for URI
        normalized_name = entity_name.lower().replace(" ", "_").replace("-", "_")
        normalized_name = "".join(c for c in normalized_name if c.isalnum() or c == "_")
        
        base_uri = f"entity://{entity_type.lower()}/{normalized_name}"
        
        # If base URI exists, add suffix
        if base_uri in existing_uris:
            suffix = 1
            while f"{base_uri}_{suffix}" in existing_uris:
                suffix += 1
            return f"{base_uri}_{suffix}"
        
        return base_uri
    
    def _get_neighboring_nodes(
        self,
        entity_name: str,
        graph_storage: Optional[any] = None
    ) -> List[Dict]:
        """
        Get neighboring nodes for context-based disambiguation.
        
        Args:
            entity_name: Name of entity to disambiguate
            graph_storage: Graph storage interface (optional)
            
        Returns:
            List of neighboring node dictionaries with type and relationships
        """
        # If graph storage is provided, query it
        if graph_storage and hasattr(graph_storage, 'get_neighbors'):
            try:
                return graph_storage.get_neighbors(entity_name)
            except Exception:
                pass
        
        # Fallback: check entity registry for related entities
        neighbors = []
        if entity_name in self.entity_registry:
            for entity_info in self.entity_registry[entity_name]:
                # Get related entities from metadata
                related = entity_info.get("related_entities", [])
                for related_uri in related:
                    if related_uri in self.uri_registry:
                        neighbors.append(self.uri_registry[related_uri])
        
        return neighbors
    
    def _analyze_context(
        self,
        entity_name: str,
        entity_type: str,
        neighbors: List[Dict]
    ) -> Tuple[float, str]:
        """
        Analyze neighboring nodes to determine entity type.
        
        Args:
            entity_name: Name of entity
            entity_type: Proposed entity type
            neighbors: List of neighboring nodes
            
        Returns:
            Tuple of (confidence, reason)
        """
        if not neighbors:
            return 0.5, "No context available"
        
        # Count type matches in neighbors
        type_matches = sum(1 for n in neighbors if n.get("type") == entity_type)
        total_neighbors = len(neighbors)
        
        if total_neighbors == 0:
            return 0.5, "No neighbors"
        
        confidence = type_matches / total_neighbors
        
        # Boost confidence if many neighbors match
        if type_matches >= 3:
            confidence = min(1.0, confidence + 0.2)
        
        reason = (
            f"Context analysis: {type_matches}/{total_neighbors} neighbors "
            f"have type '{entity_type}'"
        )
        
        return confidence, reason
    
    def _log_disambiguation(
        self,
        result: DisambiguationResult,
        action: str = "disambiguate"
    ) -> None:
        """
        Log disambiguation decision to audit log.
        
        Args:
            result: Disambiguation result
            action: Action performed (disambiguate, block, merge)
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "entity_name": result.entity_name,
            "resolved_uri": result.resolved_uri,
            "entity_type": result.entity_type,
            "confidence": result.confidence,
            "method": result.method,
            "context_nodes": result.context_nodes,
            "conflicting_entities": result.conflicting_entities,
            "decision_reason": result.decision_reason
        }
        
        try:
            with open(self.audit_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"Warning: Failed to write audit log: {e}")
    
    def disambiguate(
        self,
        entity_name: str,
        entity_type: str,
        graph_storage: Optional[any] = None,
        context_entities: Optional[List[str]] = None
    ) -> DisambiguationResult:
        """
        Disambiguate an entity during ingestion.
        
        This is the main method to call during node creation (US-015).
        
        Args:
            entity_name: Name of the entity (e.g., "Jaguar")
            entity_type: Type of the entity (e.g., "Animal" or "Company")
            graph_storage: Graph storage interface for querying neighbors
            context_entities: List of related entity names for context
            
        Returns:
            DisambiguationResult with resolved URI and metadata
            
        Raises:
            TypeCompatibilityError: If entity conflicts with existing entity
        """
        # Check if entity already exists
        existing_entities = self.entity_registry.get(entity_name, [])
        
        # Check type compatibility with existing entities
        conflicting_entities = []
        for existing in existing_entities:
            existing_type = existing.get("type")
            existing_uri = existing.get("uri")
            
            try:
                # This will raise TypeCompatibilityError if incompatible
                type_compatibility_check(
                    entity_name=entity_name,
                    existing_type=existing_type,
                    new_type=entity_type
                )
            except TypeCompatibilityError as e:
                # Types are incompatible - need unique URI
                conflicting_entities.append({
                    "uri": existing_uri,
                    "type": existing_type,
                    "reason": str(e)
                })
        
        # Get neighboring nodes for context
        neighbors = self._get_neighboring_nodes(entity_name, graph_storage)
        if context_entities:
            # Add context entities to neighbors
            for ctx_name in context_entities:
                if ctx_name in self.entity_registry:
                    neighbors.extend(self.entity_registry[ctx_name])
        
        # Analyze context
        context_confidence, context_reason = self._analyze_context(
            entity_name, entity_type, neighbors
        )
        
        # Generate unique URI
        existing_uris = set(self.uri_registry.keys())
        if conflicting_entities:
            # Must use unique URI due to type conflict
            resolved_uri = self._generate_unique_uri(
                entity_name, entity_type, existing_uris
            )
            method = "unique_uri"
            confidence = 0.9  # High confidence in separation
            decision_reason = (
                f"Type conflict detected. Assigned unique URI to prevent merge. "
                f"Conflicting entities: {len(conflicting_entities)}"
            )
        elif existing_entities:
            # Check if we can merge with existing
            compatible_existing = [
                e for e in existing_entities
                if e.get("type") == entity_type
            ]
            
            if compatible_existing:
                # Merge with existing entity
                resolved_uri = compatible_existing[0]["uri"]
                method = "merge"
                confidence = 0.95
                decision_reason = f"Merged with existing entity of same type: {resolved_uri}"
            else:
                # Different type but compatible - use unique URI
                resolved_uri = self._generate_unique_uri(
                    entity_name, entity_type, existing_uris
                )
                method = "unique_uri"
                confidence = 0.8
                decision_reason = "Different compatible type, assigned unique URI"
        else:
            # New entity
            resolved_uri = self._generate_unique_uri(
                entity_name, entity_type, existing_uris
            )
            method = "new_entity"
            confidence = 1.0
            decision_reason = "New entity, assigned base URI"
        
        # Combine context confidence with method confidence
        if method == "context":
            confidence = (confidence + context_confidence) / 2
        
        # Create result
        result = DisambiguationResult(
            entity_name=entity_name,
            resolved_uri=resolved_uri,
            entity_type=entity_type,
            confidence=confidence,
            method=method,
            context_nodes=[n.get("uri", "") for n in neighbors],
            conflicting_entities=conflicting_entities,
            decision_reason=decision_reason
        )
        
        # Register entity
        if entity_name not in self.entity_registry:
            self.entity_registry[entity_name] = []
        
        self.entity_registry[entity_name].append({
            "uri": resolved_uri,
            "type": entity_type,
            "registered_at": datetime.utcnow().isoformat()
        })
        
        self.uri_registry[resolved_uri] = {
            "name": entity_name,
            "type": entity_type,
            "uri": resolved_uri
        }
        
        # Log disambiguation
        self._log_disambiguation(result)
        
        return result
    
    def get_entity_uri(
        self,
        entity_name: str,
        entity_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Get URI for an entity.
        
        Args:
            entity_name: Name of entity
            entity_type: Optional type filter
            
        Returns:
            URI if found, None otherwise
        """
        entities = self.entity_registry.get(entity_name, [])
        
        if entity_type:
            # Filter by type
            for entity in entities:
                if entity.get("type") == entity_type:
                    return entity.get("uri")
        elif entities:
            # Return first match
            return entities[0].get("uri")
        
        return None
    
    def list_conflicts(self) -> List[Dict]:
        """
        List all entity name conflicts (same name, different types).
        
        Returns:
            List of conflict dictionaries
        """
        conflicts = []
        
        for entity_name, entities in self.entity_registry.items():
            if len(entities) > 1:
                # Multiple entities with same name
                types = [e.get("type") for e in entities]
                if len(set(types)) > 1:
                    # Different types
                    conflicts.append({
                        "entity_name": entity_name,
                        "entities": [
                            {
                                "uri": e.get("uri"),
                                "type": e.get("type")
                            }
                            for e in entities
                        ]
                    })
        
        return conflicts

