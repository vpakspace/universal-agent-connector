"""
Prometheus metrics module for AI Agent Connector.

Provides metrics for monitoring:
- HTTP requests (count, latency, status codes)
- OntoGuard validations (allowed/denied, latency)
- WebSocket connections
- Schema drift checks
- Database queries
- Agent operations
"""

from .prometheus_metrics import (
    # Metrics
    HTTP_REQUEST_COUNT,
    HTTP_REQUEST_LATENCY,
    ONTOGUARD_VALIDATION_COUNT,
    ONTOGUARD_VALIDATION_LATENCY,
    WEBSOCKET_CONNECTIONS,
    SCHEMA_DRIFT_COUNT,
    DB_QUERY_COUNT,
    DB_QUERY_LATENCY,
    AGENT_OPERATION_COUNT,
    # Functions
    init_metrics,
    get_metrics_blueprint,
    track_request,
    track_ontoguard_validation,
    track_websocket_connection,
    track_schema_drift,
    track_db_query,
    track_agent_operation,
)

__all__ = [
    'HTTP_REQUEST_COUNT',
    'HTTP_REQUEST_LATENCY',
    'ONTOGUARD_VALIDATION_COUNT',
    'ONTOGUARD_VALIDATION_LATENCY',
    'WEBSOCKET_CONNECTIONS',
    'SCHEMA_DRIFT_COUNT',
    'DB_QUERY_COUNT',
    'DB_QUERY_LATENCY',
    'AGENT_OPERATION_COUNT',
    'init_metrics',
    'get_metrics_blueprint',
    'track_request',
    'track_ontoguard_validation',
    'track_websocket_connection',
    'track_schema_drift',
    'track_db_query',
    'track_agent_operation',
]
