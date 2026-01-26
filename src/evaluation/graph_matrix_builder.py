"""
Graph Matrix Builder (JAG-004)

Builds sparse adjacency matrices from graph structures for spectral analysis.
Supports NetworkX graphs and provides interface for Neo4j integration.
"""

from typing import Dict, List, Optional, Tuple, Any

# Optional imports
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None  # type: ignore

# Optional imports
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None  # type: ignore

try:
    from scipy import sparse
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    sparse = None  # type: ignore


class GraphMatrixBuilder:
    """
    Builds sparse adjacency matrices from graphs for spectral analysis.
    
    Converts graph structures (NetworkX, Neo4j, etc.) into sparse matrices
    for eigenvalue calculations.
    """
    
    def __init__(self):
        """Initialize matrix builder"""
        pass
    
    def build_adjacency_matrix_from_nx(
        self,
        graph: Any,
        weight_attribute: Optional[str] = None
    ) -> Any:
        """
        Build sparse adjacency matrix from NetworkX graph.
        
        Args:
            graph: NetworkX graph object
            weight_attribute: Optional edge attribute for weights (default: unweighted)
            
        Returns:
            scipy.sparse matrix (CSR format)
            
        Raises:
            ImportError: If scipy or networkx not available
        """
        if not HAS_SCIPY:
            raise ImportError(
                "scipy is required for graph matrix building. "
                "Install with: pip install scipy"
            )
        
        if not HAS_NETWORKX:
            raise ImportError(
                "networkx is required for graph matrix building. "
                "Install with: pip install networkx"
            )
        
        # Convert to sparse adjacency matrix
        if weight_attribute:
            matrix = nx.adjacency_matrix(graph, weight=weight_attribute)
        else:
            matrix = nx.adjacency_matrix(graph)
        
        # Convert to CSR format for efficient operations
        return matrix.tocsr()
    
    def build_adjacency_matrix_from_entities(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        weight_attribute: Optional[str] = None
    ) -> Tuple[Any, Dict[str, int]]:
        """
        Build sparse adjacency matrix from entities and relationships.
        
        Args:
            entities: List of entity dictionaries with 'uri' field
            relationships: List of relationship dictionaries with:
                - source_uri: Source entity URI
                - target_uri: Target entity URI
                - weight: Optional weight (if weight_attribute provided)
            weight_attribute: Optional attribute name for edge weights
            
        Returns:
            Tuple of (sparse matrix, index mapping)
            - sparse matrix: scipy.sparse matrix (CSR format)
            - index mapping: Dictionary mapping URI -> matrix index
        """
        if not HAS_SCIPY:
            raise ImportError(
                "scipy is required for graph matrix building. "
                "Install with: pip install scipy"
            )
        
        # Build index mapping (URI -> index)
        uris = [e.get("uri") for e in entities if e.get("uri")]
        uri_to_index = {uri: idx for idx, uri in enumerate(uris)}
        num_nodes = len(uris)
        
        if num_nodes == 0:
            # Return empty matrix
            matrix = sparse.csr_matrix((0, 0))
            return matrix, uri_to_index
        
        # Build adjacency list
        rows = []
        cols = []
        weights = []
        
        for rel in relationships:
            source_uri = rel.get("source_uri")
            target_uri = rel.get("target_uri")
            
            if source_uri in uri_to_index and target_uri in uri_to_index:
                source_idx = uri_to_index[source_uri]
                target_idx = uri_to_index[target_uri]
                
                # Get weight (default: 1.0 for unweighted)
                weight = 1.0
                if weight_attribute and weight_attribute in rel:
                    weight = rel[weight_attribute]
                elif "weight" in rel:
                    weight = rel["weight"]
                
                rows.append(source_idx)
                cols.append(target_idx)
                weights.append(weight)
                
                # For undirected graphs, add reverse edge
                # (For directed, comment this out)
                rows.append(target_idx)
                cols.append(source_idx)
                weights.append(weight)
        
        # Build sparse matrix
        matrix = sparse.csr_matrix(
            (weights, (rows, cols)),
            shape=(num_nodes, num_nodes)
        )
        
        return matrix, uri_to_index
    
    def build_laplacian_matrix(
        self,
        adjacency_matrix: Any
    ) -> Any:
        """
        Build Laplacian matrix from adjacency matrix.
        
        Laplacian = D - A, where:
        - D: Degree matrix (diagonal)
        - A: Adjacency matrix
        
        Args:
            adjacency_matrix: Sparse adjacency matrix (CSR format)
            
        Returns:
            Sparse Laplacian matrix (CSR format)
        """
        if not HAS_SCIPY:
            raise ImportError(
                "scipy is required for Laplacian matrix. "
                "Install with: pip install scipy"
            )
        
        # Degree matrix (diagonal with node degrees)
        degrees = np.array(adjacency_matrix.sum(axis=1)).flatten()
        degree_matrix = sparse.diags(degrees, format='csr')
        
        # Laplacian = D - A
        laplacian = degree_matrix - adjacency_matrix
        
        return laplacian
    
    def get_matrix_statistics(self, matrix: Any) -> Dict[str, Any]:
        """
        Get statistics about the matrix.
        
        Args:
            matrix: Sparse matrix
            
        Returns:
            Dictionary with matrix statistics
        """
        if not HAS_SCIPY:
            raise ImportError("scipy is required for matrix statistics")
        
        return {
            "shape": matrix.shape,
            "nnz": matrix.nnz,  # Number of non-zero elements
            "density": matrix.nnz / (matrix.shape[0] * matrix.shape[1]) if matrix.shape[0] > 0 else 0.0,
            "is_symmetric": self._is_symmetric(matrix),
            "num_nodes": matrix.shape[0]
        }
    
    def _is_symmetric(self, matrix: Any) -> bool:
        """Check if matrix is symmetric"""
        if not HAS_SCIPY:
            return False
        
        # Check if matrix is symmetric (within tolerance)
        if matrix.shape[0] != matrix.shape[1]:
            return False
        
        diff = matrix - matrix.T
        return diff.nnz == 0

