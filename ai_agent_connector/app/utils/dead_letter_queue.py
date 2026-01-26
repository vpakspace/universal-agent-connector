"""
Dead-letter queue for failed queries
Allows replaying queries after fixing issues
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from ..utils.helpers import get_timestamp
import uuid
import json

if TYPE_CHECKING:
    from ..db import DatabaseConnector


class DLQStatus(Enum):
    """Dead-letter queue entry status"""
    PENDING = "pending"  # Waiting to be replayed
    REPLAYING = "replaying"  # Currently being replayed
    SUCCESS = "success"  # Successfully replayed
    FAILED = "failed"  # Failed again on replay
    ARCHIVED = "archived"  # Archived (no longer active)


@dataclass
class DLQEntry:
    """A dead-letter queue entry"""
    entry_id: str
    agent_id: str
    query: str
    query_type: str
    params: Optional[Any] = None
    error_message: str = ""
    error_type: str = ""
    failed_at: str = field(default_factory=get_timestamp)
    status: DLQStatus = DLQStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    last_attempted_at: Optional[str] = None
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'entry_id': self.entry_id,
            'agent_id': self.agent_id,
            'query': self.query,
            'query_type': self.query_type,
            'params': self.params,
            'error_message': self.error_message,
            'error_type': self.error_type,
            'failed_at': self.failed_at,
            'status': self.status.value,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'last_attempted_at': self.last_attempted_at,
            'last_error': self.last_error,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DLQEntry':
        """Create from dictionary"""
        return cls(
            entry_id=data['entry_id'],
            agent_id=data['agent_id'],
            query=data['query'],
            query_type=data['query_type'],
            params=data.get('params'),
            error_message=data.get('error_message', ''),
            error_type=data.get('error_type', ''),
            failed_at=data.get('failed_at', get_timestamp()),
            status=DLQStatus(data.get('status', 'pending')),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            last_attempted_at=data.get('last_attempted_at'),
            last_error=data.get('last_error'),
            metadata=data.get('metadata', {})
        )


class DeadLetterQueue:
    """
    Dead-letter queue for failed queries.
    Stores failed queries for later replay.
    """
    
    def __init__(self, max_entries: int = 10000):
        """
        Initialize dead-letter queue.
        
        Args:
            max_entries: Maximum number of entries to keep
        """
        # entry_id -> DLQEntry
        self._entries: Dict[str, DLQEntry] = {}
        # agent_id -> list of entry_ids
        self._agent_entries: Dict[str, List[str]] = {}
        self.max_entries = max_entries
    
    def add_failed_query(
        self,
        agent_id: str,
        query: str,
        query_type: str,
        error: Exception,
        params: Optional[Any] = None,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DLQEntry:
        """
        Add a failed query to the dead-letter queue.
        
        Args:
            agent_id: Agent ID
            query: Query that failed
            query_type: Type of query
            error: Exception that occurred
            params: Query parameters
            max_retries: Maximum retry attempts
            metadata: Additional metadata
            
        Returns:
            DLQEntry: Created entry
        """
        entry_id = str(uuid.uuid4())
        
        entry = DLQEntry(
            entry_id=entry_id,
            agent_id=agent_id,
            query=query,
            query_type=query_type,
            params=params,
            error_message=str(error),
            error_type=type(error).__name__,
            max_retries=max_retries,
            metadata=metadata or {}
        )
        
        self._entries[entry_id] = entry
        
        # Track by agent
        if agent_id not in self._agent_entries:
            self._agent_entries[agent_id] = []
        self._agent_entries[agent_id].append(entry_id)
        
        # Enforce max entries limit
        if len(self._entries) > self.max_entries:
            self._remove_oldest_entries()
        
        return entry
    
    def get_entry(self, entry_id: str) -> Optional[DLQEntry]:
        """Get an entry by ID"""
        return self._entries.get(entry_id)
    
    def list_entries(
        self,
        agent_id: Optional[str] = None,
        status: Optional[DLQStatus] = None,
        limit: int = 100
    ) -> List[DLQEntry]:
        """
        List dead-letter queue entries.
        
        Args:
            agent_id: Filter by agent ID
            status: Filter by status
            limit: Maximum number of entries to return
            
        Returns:
            List of DLQEntry objects
        """
        entries = list(self._entries.values())
        
        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]
        
        if status:
            entries = [e for e in entries if e.status == status]
        
        # Sort by failed_at (newest first)
        entries.sort(key=lambda x: x.failed_at, reverse=True)
        
        return entries[:limit]
    
    def replay_entry(
        self,
        entry_id: str,
        connector: 'DatabaseConnector'
    ) -> Dict[str, Any]:
        """
        Replay a dead-letter queue entry.
        
        Args:
            entry_id: Entry ID to replay
            connector: Database connector to use
            
        Returns:
            Dict with replay result
        """
        entry = self._entries.get(entry_id)
        if not entry:
            return {'success': False, 'error': 'Entry not found'}
        
        if entry.status == DLQStatus.ARCHIVED:
            return {'success': False, 'error': 'Entry is archived and cannot be replayed'}
        
        if entry.retry_count >= entry.max_retries:
            return {'success': False, 'error': 'Maximum retries exceeded'}
        
        # Update status
        entry.status = DLQStatus.REPLAYING
        entry.retry_count += 1
        entry.last_attempted_at = get_timestamp()
        
        try:
            # Execute query
            connector.connect()
            
            fetch = entry.query_type.upper() == 'SELECT'
            result = connector.execute_query(
                query=entry.query,
                params=entry.params,
                fetch=fetch
            )
            
            connector.disconnect()
            
            # Success
            entry.status = DLQStatus.SUCCESS
            entry.last_error = None
            
            return {
                'success': True,
                'result': result,
                'retry_count': entry.retry_count
            }
            
        except Exception as e:
            # Failed again
            entry.status = DLQStatus.FAILED
            entry.last_error = str(e)
            
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'retry_count': entry.retry_count
            }
    
    def archive_entry(self, entry_id: str) -> bool:
        """
        Archive an entry (mark as archived).
        
        Args:
            entry_id: Entry ID to archive
            
        Returns:
            bool: True if archived
        """
        entry = self._entries.get(entry_id)
        if not entry:
            return False
        
        entry.status = DLQStatus.ARCHIVED
        return True
    
    def delete_entry(self, entry_id: str) -> bool:
        """
        Delete an entry.
        
        Args:
            entry_id: Entry ID to delete
            
        Returns:
            bool: True if deleted
        """
        entry = self._entries.get(entry_id)
        if not entry:
            return False
        
        # Remove from agent tracking
        if entry.agent_id in self._agent_entries:
            self._agent_entries[entry.agent_id] = [
                eid for eid in self._agent_entries[entry.agent_id] if eid != entry_id
            ]
        
        del self._entries[entry_id]
        return True
    
    def get_statistics(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get dead-letter queue statistics.
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            Dict with statistics
        """
        entries = list(self._entries.values())
        
        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]
        
        status_counts = {}
        for status in DLQStatus:
            status_counts[status.value] = sum(1 for e in entries if e.status == status)
        
        error_type_counts = {}
        for entry in entries:
            error_type = entry.error_type
            error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        return {
            'total_entries': len(entries),
            'status_counts': status_counts,
            'error_type_counts': error_type_counts,
            'pending_count': status_counts.get('pending', 0),
            'failed_count': status_counts.get('failed', 0),
            'success_count': status_counts.get('success', 0)
        }
    
    def _remove_oldest_entries(self) -> None:
        """Remove oldest entries to stay within limit"""
        # Sort by failed_at (oldest first)
        sorted_entries = sorted(
            self._entries.items(),
            key=lambda x: x[1].failed_at
        )
        
        # Remove oldest entries
        to_remove = len(self._entries) - self.max_entries
        for entry_id, entry in sorted_entries[:to_remove]:
            self.delete_entry(entry_id)
    
    def clear_agent_entries(self, agent_id: str) -> int:
        """
        Clear all entries for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            int: Number of entries cleared
        """
        if agent_id not in self._agent_entries:
            return 0
        
        entry_ids = list(self._agent_entries[agent_id])
        count = 0
        
        for entry_id in entry_ids:
            if self.delete_entry(entry_id):
                count += 1
        
        return count

