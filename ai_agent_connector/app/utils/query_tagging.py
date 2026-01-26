"""
Query tagging system for organizing and searching queries
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from ..utils.helpers import get_timestamp
import uuid


@dataclass
class QueryTag:
    """A tag for organizing queries"""
    tag_id: str
    name: str
    color: Optional[str] = None  # Hex color code
    description: Optional[str] = None
    created_by: str = ""
    created_at: str = field(default_factory=get_timestamp)
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'tag_id': self.tag_id,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'usage_count': self.usage_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryTag':
        """Create from dictionary"""
        return cls(
            tag_id=data['tag_id'],
            name=data['name'],
            color=data.get('color'),
            description=data.get('description'),
            created_by=data.get('created_by', ''),
            created_at=data.get('created_at', get_timestamp()),
            usage_count=data.get('usage_count', 0)
        )


@dataclass
class TaggedQuery:
    """A query with tags"""
    query_id: str
    agent_id: str
    query: str
    query_type: str
    tags: List[str] = field(default_factory=list)  # List of tag names
    created_at: str = field(default_factory=get_timestamp)
    last_executed_at: Optional[str] = None
    execution_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'query_id': self.query_id,
            'agent_id': self.agent_id,
            'query': self.query,
            'query_type': self.query_type,
            'tags': self.tags,
            'created_at': self.created_at,
            'last_executed_at': self.last_executed_at,
            'execution_count': self.execution_count
        }


class QueryTaggingManager:
    """
    Manages query tagging for organization and search.
    """
    
    def __init__(self):
        """Initialize query tagging manager"""
        # tag_name -> QueryTag
        self._tags: Dict[str, QueryTag] = {}
        # query_id -> TaggedQuery
        self._tagged_queries: Dict[str, TaggedQuery] = {}
        # tag_name -> set of query_ids
        self._tag_index: Dict[str, set] = {}
    
    def create_tag(
        self,
        name: str,
        created_by: str,
        color: Optional[str] = None,
        description: Optional[str] = None
    ) -> QueryTag:
        """
        Create a new tag.
        
        Args:
            name: Tag name
            created_by: User ID who created
            color: Optional hex color code
            description: Optional description
            
        Returns:
            QueryTag: Created tag
        """
        tag_id = str(uuid.uuid4())
        
        tag = QueryTag(
            tag_id=tag_id,
            name=name,
            color=color,
            description=description,
            created_by=created_by
        )
        
        self._tags[name] = tag
        self._tag_index[name] = set()
        
        return tag
    
    def get_tag(self, name: str) -> Optional[QueryTag]:
        """Get a tag by name"""
        return self._tags.get(name)
    
    def list_tags(
        self,
        search: Optional[str] = None,
        sort_by_usage: bool = True
    ) -> List[QueryTag]:
        """
        List all tags.
        
        Args:
            search: Search in tag names
            sort_by_usage: Sort by usage count
            
        Returns:
            List of QueryTag objects
        """
        tags = list(self._tags.values())
        
        if search:
            search_lower = search.lower()
            tags = [t for t in tags if search_lower in t.name.lower()]
        
        if sort_by_usage:
            tags.sort(key=lambda x: x.usage_count, reverse=True)
        
        return tags
    
    def tag_query(
        self,
        agent_id: str,
        query: str,
        query_type: str,
        tags: List[str],
        query_id: Optional[str] = None
    ) -> TaggedQuery:
        """
        Tag a query.
        
        Args:
            agent_id: Agent ID
            query: Query string
            query_type: Query type
            tags: List of tag names
            query_id: Optional query ID (generated if not provided)
            
        Returns:
            TaggedQuery: Tagged query
        """
        if query_id is None:
            query_id = str(uuid.uuid4())
        
        # Get or create existing tagged query
        tagged_query = self._tagged_queries.get(query_id)
        
        if tagged_query:
            # Update tags
            old_tags = set(tagged_query.tags)
            new_tags = set(tags)
            
            # Remove from old tag indices
            for tag in old_tags - new_tags:
                if tag in self._tag_index:
                    self._tag_index[tag].discard(query_id)
                    if tag in self._tags:
                        self._tags[tag].usage_count = max(0, self._tags[tag].usage_count - 1)
            
            # Add to new tag indices
            for tag in new_tags - old_tags:
                if tag not in self._tags:
                    # Auto-create tag if it doesn't exist
                    self.create_tag(tag, created_by='system')
                
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                
                self._tag_index[tag].add(query_id)
                if tag in self._tags:
                    self._tags[tag].usage_count += 1
            
            tagged_query.tags = tags
        else:
            # Create new tagged query
            tagged_query = TaggedQuery(
                query_id=query_id,
                agent_id=agent_id,
                query=query,
                query_type=query_type,
                tags=tags
            )
            
            # Add to tag indices
            for tag in tags:
                if tag not in self._tags:
                    # Auto-create tag if it doesn't exist
                    self.create_tag(tag, created_by='system')
                
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                
                self._tag_index[tag].add(query_id)
                if tag in self._tags:
                    self._tags[tag].usage_count += 1
            
            self._tagged_queries[query_id] = tagged_query
        
        return tagged_query
    
    def record_query_execution(self, query_id: str) -> None:
        """Record that a query was executed"""
        tagged_query = self._tagged_queries.get(query_id)
        if tagged_query:
            tagged_query.execution_count += 1
            tagged_query.last_executed_at = get_timestamp()
    
    def search_queries(
        self,
        tags: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
        query_type: Optional[str] = None,
        search_text: Optional[str] = None
    ) -> List[TaggedQuery]:
        """
        Search tagged queries.
        
        Args:
            tags: Filter by tags (AND logic - query must have all tags)
            agent_id: Filter by agent ID
            query_type: Filter by query type
            search_text: Search in query text
            
        Returns:
            List of TaggedQuery objects
        """
        query_ids = set(self._tagged_queries.keys())
        
        # Filter by tags
        if tags:
            for tag in tags:
                if tag in self._tag_index:
                    query_ids &= self._tag_index[tag]
                else:
                    # Tag doesn't exist, no matches
                    return []
        
        # Filter by agent
        if agent_id:
            query_ids = {
                qid for qid in query_ids
                if self._tagged_queries[qid].agent_id == agent_id
            }
        
        # Filter by query type
        if query_type:
            query_ids = {
                qid for qid in query_ids
                if self._tagged_queries[qid].query_type == query_type
            }
        
        # Filter by search text
        if search_text:
            search_lower = search_text.lower()
            query_ids = {
                qid for qid in query_ids
                if search_lower in self._tagged_queries[qid].query.lower()
            }
        
        # Return results
        results = [self._tagged_queries[qid] for qid in query_ids]
        
        # Sort by last_executed_at (most recent first)
        results.sort(
            key=lambda x: x.last_executed_at or x.created_at,
            reverse=True
        )
        
        return results
    
    def get_query_tags(self, query_id: str) -> List[str]:
        """Get tags for a query"""
        tagged_query = self._tagged_queries.get(query_id)
        return tagged_query.tags if tagged_query else []
    
    def remove_tag_from_query(self, query_id: str, tag_name: str) -> bool:
        """Remove a tag from a query"""
        tagged_query = self._tagged_queries.get(query_id)
        if not tagged_query:
            return False
        
        if tag_name in tagged_query.tags:
            tagged_query.tags.remove(tag_name)
            
            # Update tag index
            if tag_name in self._tag_index:
                self._tag_index[tag_name].discard(query_id)
            
            # Update usage count
            if tag_name in self._tags:
                self._tags[tag_name].usage_count = max(0, self._tags[tag_name].usage_count - 1)
            
            return True
        
        return False
    
    def delete_tag(self, tag_name: str) -> bool:
        """Delete a tag (removes from all queries)"""
        if tag_name not in self._tags:
            return False
        
        # Remove tag from all queries
        query_ids = list(self._tag_index.get(tag_name, set()))
        for query_id in query_ids:
            self.remove_tag_from_query(query_id, tag_name)
        
        # Delete tag
        del self._tags[tag_name]
        if tag_name in self._tag_index:
            del self._tag_index[tag_name]
        
        return True
    
    def get_tag_statistics(self) -> Dict[str, Any]:
        """Get statistics about tags"""
        total_tags = len(self._tags)
        total_tagged_queries = len(self._tagged_queries)
        
        most_used_tags = sorted(
            self._tags.values(),
            key=lambda x: x.usage_count,
            reverse=True
        )[:10]
        
        return {
            'total_tags': total_tags,
            'total_tagged_queries': total_tagged_queries,
            'most_used_tags': [t.to_dict() for t in most_used_tags]
        }

