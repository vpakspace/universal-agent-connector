"""
Mock Graph Storage Interface for Integration (US-015)

This provides a simple interface that can be integrated with actual graph storage.
The disambiguation service uses this interface to query neighboring nodes.
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod


class GraphStorageInterface(ABC):
    """
    Abstract interface for graph storage operations.
    
    This allows the disambiguation service to work with any graph storage
    implementation (Neo4j, NetworkX, custom, etc.).
    """
    
    @abstractmethod
    def get_neighbors(self, entity_name: str) -> List[Dict[str, Any]]:
        """
        Get neighboring nodes for an entity.
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            List of neighboring node dictionaries with:
            - uri: Entity URI
            - type: Entity type
            - relationship: Relationship type
            - metadata: Additional metadata
        """
        pass
    
    @abstractmethod
    def create_node(
        self,
        entity_name: str,
        entity_type: str,
        uri: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a node in the graph.
        
        Args:
            entity_name: Name of the entity
            entity_type: Type of the entity
            uri: Unique URI for the entity
            metadata: Additional metadata
            
        Returns:
            Created node dictionary
        """
        pass


class MockGraphStorage(GraphStorageInterface):
    """
    Mock implementation of graph storage for testing.
    
    Stores nodes and relationships in memory.
    """
    
    def __init__(self):
        """Initialize mock graph storage"""
        self.nodes: Dict[str, Dict[str, Any]] = {}  # uri -> node
        self.relationships: List[Dict[str, Any]] = []  # List of relationships
    
    def get_neighbors(self, entity_name: str) -> List[Dict[str, Any]]:
        """Get neighboring nodes for an entity"""
        neighbors = []
        
        # Find node by name
        entity_node = None
        for node in self.nodes.values():
            if node.get("name") == entity_name:
                entity_node = node
                break
        
        if not entity_node:
            return []
        
        entity_uri = entity_node.get("uri")
        
        # Find relationships
        for rel in self.relationships:
            if rel.get("source_uri") == entity_uri:
                target_uri = rel.get("target_uri")
                if target_uri in self.nodes:
                    neighbors.append(self.nodes[target_uri])
            elif rel.get("target_uri") == entity_uri:
                source_uri = rel.get("source_uri")
                if source_uri in self.nodes:
                    neighbors.append(self.nodes[source_uri])
        
        return neighbors
    
    def create_node(
        self,
        entity_name: str,
        entity_type: str,
        uri: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a node in the graph"""
        node = {
            "name": entity_name,
            "type": entity_type,
            "uri": uri,
            "metadata": metadata or {}
        }
        
        self.nodes[uri] = node
        return node
    
    def create_relationship(
        self,
        source_uri: str,
        target_uri: str,
        relationship_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a relationship between two nodes.
        
        Args:
            source_uri: URI of source node
            target_uri: URI of target node
            relationship_type: Type of relationship
            metadata: Additional metadata
            
        Returns:
            Created relationship dictionary
        """
        relationship = {
            "source_uri": source_uri,
            "target_uri": target_uri,
            "type": relationship_type,
            "metadata": metadata or {}
        }
        
        self.relationships.append(relationship)
        return relationship
    
    def get_node(self, uri: str) -> Optional[Dict[str, Any]]:
        """Get a node by URI"""
        return self.nodes.get(uri)
    
    def list_nodes(self) -> List[Dict[str, Any]]:
        """List all nodes"""
        return list(self.nodes.values())
    
    def reset(self) -> None:
        """Reset the graph (for testing)"""
        self.nodes.clear()
        self.relationships.clear()

