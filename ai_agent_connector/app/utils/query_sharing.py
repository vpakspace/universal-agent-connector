"""
Query result sharing system with shareable links
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from ..utils.helpers import get_timestamp
import uuid
import hashlib
import base64


@dataclass
class SharedQuery:
    """A shared query result"""
    share_id: str
    agent_id: str
    query: str
    query_type: str
    result: Any
    shared_by: str
    shared_at: str = field(default_factory=get_timestamp)
    expires_at: Optional[str] = None
    access_count: int = 0
    max_access_count: Optional[int] = None
    is_public: bool = False
    password_hash: Optional[str] = None  # Optional password protection
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'share_id': self.share_id,
            'agent_id': self.agent_id,
            'query': self.query,
            'query_type': self.query_type,
            'shared_by': self.shared_by,
            'shared_at': self.shared_at,
            'expires_at': self.expires_at,
            'access_count': self.access_count,
            'max_access_count': self.max_access_count,
            'is_public': self.is_public,
            'metadata': self.metadata
        }
    
    def is_expired(self) -> bool:
        """Check if share is expired"""
        if self.expires_at:
            try:
                expires = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00').split('.')[0])
                return datetime.now() > expires
            except Exception:
                return False
        return False
    
    def is_access_limit_reached(self) -> bool:
        """Check if access limit is reached"""
        if self.max_access_count:
            return self.access_count >= self.max_access_count
        return False
    
    def can_access(self, password: Optional[str] = None) -> bool:
        """Check if share can be accessed"""
        if self.is_expired():
            return False
        
        if self.is_access_limit_reached():
            return False
        
        if self.password_hash and password:
            # Verify password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            return password_hash == self.password_hash
        elif self.password_hash:
            # Password required but not provided
            return False
        
        return True


class QuerySharingManager:
    """
    Manages sharing of query results via shareable links.
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize query sharing manager.
        
        Args:
            base_url: Base URL for generating share links
        """
        # share_id -> SharedQuery
        self._shares: Dict[str, SharedQuery] = {}
        self.base_url = base_url
    
    def create_share(
        self,
        agent_id: str,
        query: str,
        query_type: str,
        result: Any,
        shared_by: str,
        expires_in_hours: Optional[int] = None,
        max_access_count: Optional[int] = None,
        is_public: bool = True,
        password: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SharedQuery:
        """
        Create a shareable link for query results.
        
        Args:
            agent_id: Agent ID
            query: Query string
            query_type: Query type
            result: Query result
            shared_by: User ID who shared
            expires_in_hours: Hours until expiration (None for no expiration)
            max_access_count: Maximum number of accesses (None for unlimited)
            is_public: Whether share is public
            password: Optional password for access
            metadata: Additional metadata
            
        Returns:
            SharedQuery: Created share
        """
        share_id = str(uuid.uuid4())
        
        expires_at = None
        if expires_in_hours:
            expires_at = (datetime.now() + timedelta(hours=expires_in_hours)).isoformat()
        
        password_hash = None
        if password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        share = SharedQuery(
            share_id=share_id,
            agent_id=agent_id,
            query=query,
            query_type=query_type,
            result=result,
            shared_by=shared_by,
            expires_at=expires_at,
            max_access_count=max_access_count,
            is_public=is_public,
            password_hash=password_hash,
            metadata=metadata or {}
        )
        
        self._shares[share_id] = share
        
        return share
    
    def get_share(
        self,
        share_id: str,
        password: Optional[str] = None
    ) -> Optional[SharedQuery]:
        """
        Get a shared query result.
        
        Args:
            share_id: Share ID
            password: Optional password
            
        Returns:
            SharedQuery if accessible, None otherwise
        """
        share = self._shares.get(share_id)
        if not share:
            return None
        
        if not share.can_access(password):
            return None
        
        # Increment access count
        share.access_count += 1
        
        return share
    
    def get_share_link(self, share_id: str) -> str:
        """Get shareable link for a share"""
        return f"{self.base_url}/api/shared/{share_id}"
    
    def list_shares(
        self,
        shared_by: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> List[SharedQuery]:
        """
        List shares.
        
        Args:
            shared_by: Filter by user who shared
            agent_id: Filter by agent ID
            
        Returns:
            List of SharedQuery objects
        """
        shares = list(self._shares.values())
        
        if shared_by:
            shares = [s for s in shares if s.shared_by == shared_by]
        
        if agent_id:
            shares = [s for s in shares if s.agent_id == agent_id]
        
        # Sort by shared_at (newest first)
        shares.sort(key=lambda x: x.shared_at, reverse=True)
        
        return shares
    
    def delete_share(self, share_id: str, user_id: str) -> bool:
        """
        Delete a share.
        
        Args:
            share_id: Share ID
            user_id: User ID (must be the one who shared)
            
        Returns:
            bool: True if deleted
        """
        share = self._shares.get(share_id)
        if not share:
            return False
        
        if share.shared_by != user_id:
            return False
        
        del self._shares[share_id]
        return True
    
    def clear_expired_shares(self) -> int:
        """
        Clear expired shares.
        
        Returns:
            int: Number of shares cleared
        """
        expired_ids = [
            share_id for share_id, share in self._shares.items()
            if share.is_expired()
        ]
        
        for share_id in expired_ids:
            del self._shares[share_id]
        
        return len(expired_ids)
    
    def get_share_stats(self, share_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a share"""
        share = self._shares.get(share_id)
        if not share:
            return None
        
        return {
            'share_id': share_id,
            'access_count': share.access_count,
            'max_access_count': share.max_access_count,
            'is_expired': share.is_expired(),
            'is_access_limit_reached': share.is_access_limit_reached(),
            'shared_at': share.shared_at,
            'expires_at': share.expires_at
        }

