"""
Query result caching system with configurable TTL
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json


@dataclass
class CacheEntry:
    """A cached query result"""
    query_hash: str
    query: str
    results: Any
    cached_at: datetime
    expires_at: datetime
    hit_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'query_hash': self.query_hash,
            'query': self.query,
            'cached_at': self.cached_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'hit_count': self.hit_count,
            'metadata': self.metadata
        }


class QueryCache:
    """
    Query result cache with configurable TTL.
    Caches query results to avoid repeated database hits.
    """
    
    def __init__(self, default_ttl_seconds: int = 300):
        """
        Initialize query cache.
        
        Args:
            default_ttl_seconds: Default TTL in seconds (default: 5 minutes)
        """
        # query_hash -> CacheEntry
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl_seconds = default_ttl_seconds
        # Agent-specific TTL overrides
        self._agent_ttls: Dict[str, int] = {}
    
    def _hash_query(self, query: str, params: Optional[Any] = None) -> str:
        """
        Generate hash for a query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            str: Query hash
        """
        # Normalize query (remove extra whitespace)
        normalized_query = ' '.join(query.split())
        
        # Include parameters in hash
        if params:
            params_str = json.dumps(params, sort_keys=True)
            hash_input = f"{normalized_query}:{params_str}"
        else:
            hash_input = normalized_query
        
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def set_agent_ttl(self, agent_id: str, ttl_seconds: int) -> None:
        """
        Set TTL for a specific agent.
        
        Args:
            agent_id: Agent ID
            ttl_seconds: TTL in seconds
        """
        self._agent_ttls[agent_id] = ttl_seconds
    
    def get_agent_ttl(self, agent_id: str) -> int:
        """
        Get TTL for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            int: TTL in seconds
        """
        return self._agent_ttls.get(agent_id, self.default_ttl_seconds)
    
    def get(
        self,
        query: str,
        params: Optional[Any] = None,
        agent_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get cached query results.
        
        Args:
            query: SQL query
            params: Query parameters
            agent_id: Optional agent ID (for agent-specific TTL)
            
        Returns:
            Cached results or None if not found/expired
        """
        query_hash = self._hash_query(query, params)
        entry = self._cache.get(query_hash)
        
        if not entry:
            return None
        
        # Check if expired
        if entry.is_expired():
            del self._cache[query_hash]
            return None
        
        # Update hit count
        entry.hit_count += 1
        
        return entry.results
    
    def set(
        self,
        query: str,
        results: Any,
        params: Optional[Any] = None,
        agent_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Cache query results.
        
        Args:
            query: SQL query
            results: Query results to cache
            params: Query parameters
            agent_id: Optional agent ID
            ttl_seconds: Optional TTL override
            metadata: Optional metadata to store
        """
        query_hash = self._hash_query(query, params)
        
        # Determine TTL
        if ttl_seconds is None:
            if agent_id:
                ttl_seconds = self.get_agent_ttl(agent_id)
            else:
                ttl_seconds = self.default_ttl_seconds
        
        now = datetime.now()
        expires_at = now + timedelta(seconds=ttl_seconds)
        
        entry = CacheEntry(
            query_hash=query_hash,
            query=query,
            results=results,
            cached_at=now,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        self._cache[query_hash] = entry
    
    def invalidate(
        self,
        query: Optional[str] = None,
        params: Optional[Any] = None,
        pattern: Optional[str] = None
    ) -> int:
        """
        Invalidate cache entries.
        
        Args:
            query: Specific query to invalidate
            pattern: Pattern to match queries (e.g., "SELECT * FROM users")
            params: Query parameters
            
        Returns:
            int: Number of entries invalidated
        """
        if query:
            query_hash = self._hash_query(query, params)
            if query_hash in self._cache:
                del self._cache[query_hash]
                return 1
            return 0
        
        if pattern:
            # Invalidate all queries matching pattern
            count = 0
            to_remove = []
            for entry in self._cache.values():
                if pattern.lower() in entry.query.lower():
                    to_remove.append(entry.query_hash)
            
            for query_hash in to_remove:
                del self._cache[query_hash]
                count += 1
            
            return count
        
        # Invalidate all
        count = len(self._cache)
        self._cache.clear()
        return count
    
    def clear_expired(self) -> int:
        """
        Clear expired cache entries.
        
        Returns:
            int: Number of entries cleared
        """
        now = datetime.now()
        to_remove = [
            query_hash for query_hash, entry in self._cache.items()
            if entry.expires_at < now
        ]
        
        for query_hash in to_remove:
            del self._cache[query_hash]
        
        return len(to_remove)
    
    def get_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            Dict containing cache statistics
        """
        now = datetime.now()
        
        total_entries = len(self._cache)
        expired_entries = sum(1 for e in self._cache.values() if e.is_expired())
        active_entries = total_entries - expired_entries
        
        total_hits = sum(e.hit_count for e in self._cache.values())
        
        # Calculate average TTL
        if self._cache:
            avg_ttl = sum(
                (e.expires_at - e.cached_at).total_seconds()
                for e in self._cache.values()
            ) / len(self._cache)
        else:
            avg_ttl = 0
        
        return {
            'total_entries': total_entries,
            'active_entries': active_entries,
            'expired_entries': expired_entries,
            'total_hits': total_hits,
            'average_ttl_seconds': avg_ttl,
            'default_ttl_seconds': self.default_ttl_seconds
        }
    
    def list_entries(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List cache entries.
        
        Args:
            agent_id: Optional agent ID to filter by
            limit: Maximum number of entries to return
            
        Returns:
            List of cache entry dictionaries
        """
        entries = []
        
        for entry in self._cache.values():
            # Filter by agent if specified (would need agent_id in metadata)
            if agent_id and entry.metadata.get('agent_id') != agent_id:
                continue
            
            entries.append(entry.to_dict())
        
        # Sort by cached_at (newest first)
        entries.sort(key=lambda x: x['cached_at'], reverse=True)
        
        return entries[:limit]
    
    def remove_agent_cache(self, agent_id: str) -> int:
        """
        Remove all cache entries for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            int: Number of entries removed
        """
        count = 0
        to_remove = []
        
        for query_hash, entry in self._cache.items():
            if entry.metadata.get('agent_id') == agent_id:
                to_remove.append(query_hash)
        
        for query_hash in to_remove:
            del self._cache[query_hash]
            count += 1
        
        return count

