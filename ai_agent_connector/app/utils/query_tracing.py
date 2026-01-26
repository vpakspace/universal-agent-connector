"""
Query lifecycle tracing system
Tracks full lifecycle: input → SQL generation → execution → result
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from ..utils.helpers import get_timestamp
import uuid


class TraceStage(Enum):
    """Stages in query lifecycle"""
    INPUT = "input"
    SQL_GENERATION = "sql_generation"
    VALIDATION = "validation"
    APPROVAL = "approval"
    EXECUTION = "execution"
    RESULT = "result"
    ERROR = "error"


@dataclass
class TraceSpan:
    """A span in the query trace"""
    span_id: str
    stage: TraceStage
    start_time: str
    end_time: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'span_id': self.span_id,
            'stage': self.stage.value,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_ms': self.duration_ms,
            'metadata': self.metadata,
            'error': self.error
        }


@dataclass
class QueryTrace:
    """Complete trace of a query lifecycle"""
    trace_id: str
    agent_id: str
    query_type: str  # SELECT, INSERT, NATURAL_LANGUAGE, etc.
    natural_language_query: Optional[str] = None
    generated_sql: Optional[str] = None
    final_sql: Optional[str] = None  # After RLS, etc.
    spans: List[TraceSpan] = field(default_factory=list)
    result_row_count: Optional[int] = None
    success: bool = False
    error_message: Optional[str] = None
    total_duration_ms: Optional[float] = None
    created_at: str = field(default_factory=get_timestamp)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'trace_id': self.trace_id,
            'agent_id': self.agent_id,
            'query_type': self.query_type,
            'natural_language_query': self.natural_language_query,
            'generated_sql': self.generated_sql,
            'final_sql': self.final_sql,
            'spans': [span.to_dict() for span in self.spans],
            'result_row_count': self.result_row_count,
            'success': self.success,
            'error_message': self.error_message,
            'total_duration_ms': self.total_duration_ms,
            'created_at': self.created_at
        }


class QueryTracer:
    """
    Traces the full lifecycle of queries for debugging and monitoring.
    """
    
    def __init__(self, max_traces: int = 10000):
        """
        Initialize query tracer.
        
        Args:
            max_traces: Maximum number of traces to keep in memory
        """
        # trace_id -> QueryTrace
        self._traces: Dict[str, QueryTrace] = {}
        self.max_traces = max_traces
    
    def start_trace(
        self,
        agent_id: str,
        query_type: str,
        natural_language_query: Optional[str] = None
    ) -> str:
        """
        Start a new query trace.
        
        Args:
            agent_id: Agent ID
            query_type: Type of query
            natural_language_query: Natural language query if applicable
            
        Returns:
            str: Trace ID
        """
        trace_id = str(uuid.uuid4())
        
        trace = QueryTrace(
            trace_id=trace_id,
            agent_id=agent_id,
            query_type=query_type,
            natural_language_query=natural_language_query
        )
        
        # Add input span
        input_span = TraceSpan(
            span_id=str(uuid.uuid4()),
            stage=TraceStage.INPUT,
            start_time=get_timestamp(),
            metadata={
                'query_type': query_type,
                'natural_language_query': natural_language_query
            }
        )
        trace.spans.append(input_span)
        
        self._traces[trace_id] = trace
        
        # Enforce max traces limit
        if len(self._traces) > self.max_traces:
            # Remove oldest traces
            sorted_traces = sorted(
                self._traces.items(),
                key=lambda x: x[1].created_at
            )
            for trace_id, _ in sorted_traces[:len(self._traces) - self.max_traces]:
                del self._traces[trace_id]
        
        return trace_id
    
    def add_span(
        self,
        trace_id: str,
        stage: TraceStage,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> str:
        """
        Add a span to a trace.
        
        Args:
            trace_id: Trace ID
            stage: Stage of the lifecycle
            metadata: Additional metadata
            error: Error message if stage failed
            
        Returns:
            str: Span ID
        """
        trace = self._traces.get(trace_id)
        if not trace:
            return ""
        
        span_id = str(uuid.uuid4())
        start_time = get_timestamp()
        
        span = TraceSpan(
            span_id=span_id,
            stage=stage,
            start_time=start_time,
            metadata=metadata or {},
            error=error
        )
        
        trace.spans.append(span)
        
        return span_id
    
    def end_span(
        self,
        trace_id: str,
        span_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        End a span in a trace.
        
        Args:
            trace_id: Trace ID
            span_id: Span ID
            metadata: Additional metadata to add
        """
        trace = self._traces.get(trace_id)
        if not trace:
            return
        
        span = next((s for s in trace.spans if s.span_id == span_id), None)
        if not span:
            return
        
        span.end_time = get_timestamp()
        
        # Calculate duration
        try:
            start = datetime.fromisoformat(span.start_time.replace('Z', '+00:00').split('.')[0])
            end = datetime.fromisoformat(span.end_time.replace('Z', '+00:00').split('.')[0])
            span.duration_ms = (end - start).total_seconds() * 1000
        except Exception:
            pass
        
        if metadata:
            span.metadata.update(metadata)
    
    def complete_trace(
        self,
        trace_id: str,
        success: bool,
        generated_sql: Optional[str] = None,
        final_sql: Optional[str] = None,
        result_row_count: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Complete a trace.
        
        Args:
            trace_id: Trace ID
            success: Whether query succeeded
            generated_sql: Generated SQL query
            final_sql: Final SQL after transformations
            result_row_count: Number of rows returned
            error_message: Error message if failed
        """
        trace = self._traces.get(trace_id)
        if not trace:
            return
        
        trace.success = success
        trace.generated_sql = generated_sql
        trace.final_sql = final_sql
        trace.result_row_count = result_row_count
        trace.error_message = error_message
        
        # Calculate total duration
        if trace.spans:
            try:
                first_span = trace.spans[0]
                last_span = trace.spans[-1]
                
                start = datetime.fromisoformat(first_span.start_time.replace('Z', '+00:00').split('.')[0])
                end_time = last_span.end_time or get_timestamp()
                end = datetime.fromisoformat(end_time.replace('Z', '+00:00').split('.')[0])
                
                trace.total_duration_ms = (end - start).total_seconds() * 1000
            except Exception:
                pass
    
    def get_trace(self, trace_id: str) -> Optional[QueryTrace]:
        """Get a trace by ID"""
        return self._traces.get(trace_id)
    
    def list_traces(
        self,
        agent_id: Optional[str] = None,
        query_type: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 100
    ) -> List[QueryTrace]:
        """
        List traces with filtering.
        
        Args:
            agent_id: Filter by agent ID
            query_type: Filter by query type
            success: Filter by success status
            limit: Maximum number of traces to return
            
        Returns:
            List of QueryTrace objects
        """
        traces = list(self._traces.values())
        
        if agent_id:
            traces = [t for t in traces if t.agent_id == agent_id]
        
        if query_type:
            traces = [t for t in traces if t.query_type == query_type]
        
        if success is not None:
            traces = [t for t in traces if t.success == success]
        
        # Sort by created_at (newest first)
        traces.sort(key=lambda x: x.created_at, reverse=True)
        
        return traces[:limit]
    
    def clear_traces(self, agent_id: Optional[str] = None) -> int:
        """
        Clear traces.
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            int: Number of traces cleared
        """
        if agent_id:
            to_remove = [
                trace_id for trace_id, trace in self._traces.items()
                if trace.agent_id == agent_id
            ]
            for trace_id in to_remove:
                del self._traces[trace_id]
            return len(to_remove)
        else:
            count = len(self._traces)
            self._traces.clear()
            return count

