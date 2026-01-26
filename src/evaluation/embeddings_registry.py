"""
Mock Embeddings Model Registry Interface

This provides an interface for text embeddings that can be used by the MINE evaluator.
In production, this would integrate with an actual embeddings service.
"""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

# Optional import for numpy
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None  # type: ignore


class EmbeddingsModel(ABC):
    """Abstract base class for embeddings models"""
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        pass
    
    @abstractmethod
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        pass


class MockEmbeddingsModel(EmbeddingsModel):
    """
    Mock embeddings model for testing.
    
    Uses simple hash-based embeddings for deterministic testing.
    In production, replace with actual embeddings model (OpenAI, Sentence-BERT, etc.)
    """
    
    def __init__(self, dimension: int = 384):
        """
        Initialize mock embeddings model.
        
        Args:
            dimension: Embedding dimension (default: 384 for sentence-transformers)
        """
        self.dimension = dimension
    
    def embed(self, text: str) -> List[float]:
        """Generate mock embedding for text"""
        if not HAS_NUMPY:
            raise ImportError(
                "numpy is required for MockEmbeddingsModel. "
                "Install with: pip install numpy"
            )
        
        # Simple hash-based embedding for testing
        # In production, use actual embeddings model
        import hashlib
        
        # Hash the text and convert to embedding-like vector
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val % (2**32))  # type: ignore
        embedding = np.random.normal(0, 1, self.dimension).tolist()  # type: ignore
        
        # Normalize to unit vector
        norm = np.linalg.norm(embedding)  # type: ignore
        if norm > 0:
            embedding = (np.array(embedding) / norm).tolist()  # type: ignore
        
        return embedding
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        if not HAS_NUMPY:
            raise ImportError(
                "numpy is required for MockEmbeddingsModel. "
                "Install with: pip install numpy"
            )
        
        vec1 = np.array(embedding1)  # type: ignore
        vec2 = np.array(embedding2)  # type: ignore
        
        # Cosine similarity
        dot_product = np.dot(vec1, vec2)  # type: ignore
        norm1 = np.linalg.norm(vec1)  # type: ignore
        norm2 = np.linalg.norm(vec2)  # type: ignore
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        # Clamp to [0, 1] (similarity can be negative)
        return max(0.0, min(1.0, (similarity + 1) / 2))


class EmbeddingsModelRegistry:
    """
    Registry for embeddings models.
    
    In production, this would manage actual embeddings models.
    For now, provides a simple interface with mock implementation.
    """
    
    def __init__(self):
        """Initialize registry"""
        self._models: Dict[str, EmbeddingsModel] = {}
        self._default_model: Optional[EmbeddingsModel] = None
    
    def register_model(self, name: str, model: EmbeddingsModel) -> None:
        """
        Register an embeddings model.
        
        Args:
            name: Model name
            model: Embeddings model instance
        """
        self._models[name] = model
        if self._default_model is None:
            self._default_model = model
    
    def get_model(self, name: Optional[str] = None) -> EmbeddingsModel:
        """
        Get embeddings model by name.
        
        Args:
            name: Model name (None for default)
            
        Returns:
            EmbeddingsModel instance
            
        Raises:
            ValueError: If model not found
        """
        if name is None:
            if self._default_model is None:
                # Create default mock model
                self._default_model = MockEmbeddingsModel()
            return self._default_model
        
        if name not in self._models:
            raise ValueError(f"Model '{name}' not found in registry")
        
        return self._models[name]
    
    def set_default(self, name: str) -> None:
        """
        Set default model.
        
        Args:
            name: Model name
        """
        if name not in self._models:
            raise ValueError(f"Model '{name}' not found in registry")
        self._default_model = self._models[name]


# Global registry instance
_global_registry = None


def get_embeddings_registry() -> EmbeddingsModelRegistry:
    """Get or create global embeddings registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = EmbeddingsModelRegistry()
        # Register default mock model
        _global_registry.register_model("default", MockEmbeddingsModel())
    return _global_registry

