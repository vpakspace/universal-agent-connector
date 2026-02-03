"""
Prometheus metrics definitions and utilities for AI Agent Connector.

Metrics exposed:
- uac_http_requests_total: Total HTTP requests by method, endpoint, status
- uac_http_request_duration_seconds: HTTP request latency histogram
- uac_ontoguard_validations_total: OntoGuard validations by action, entity, result
- uac_ontoguard_validation_duration_seconds: OntoGuard validation latency
- uac_websocket_connections: Current WebSocket connections (gauge)
- uac_schema_drift_checks_total: Schema drift checks by severity
- uac_db_queries_total: Database queries by type, status
- uac_db_query_duration_seconds: Database query latency
- uac_agent_operations_total: Agent operations by type, status
"""

import time
import logging
from functools import wraps
from typing import Callable, Optional
from contextlib import contextmanager

from flask import Blueprint, Response, request, g
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
)

logger = logging.getLogger(__name__)

# Custom registry to avoid conflicts
METRICS_REGISTRY = REGISTRY

# =============================================================================
# HTTP Request Metrics
# =============================================================================

HTTP_REQUEST_COUNT = Counter(
    'uac_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=METRICS_REGISTRY
)

HTTP_REQUEST_LATENCY = Histogram(
    'uac_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=METRICS_REGISTRY
)

# =============================================================================
# OntoGuard Validation Metrics
# =============================================================================

ONTOGUARD_VALIDATION_COUNT = Counter(
    'uac_ontoguard_validations_total',
    'Total OntoGuard validations',
    ['action', 'entity_type', 'result', 'role'],
    registry=METRICS_REGISTRY
)

ONTOGUARD_VALIDATION_LATENCY = Histogram(
    'uac_ontoguard_validation_duration_seconds',
    'OntoGuard validation latency in seconds',
    ['action', 'entity_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=METRICS_REGISTRY
)

# =============================================================================
# WebSocket Metrics
# =============================================================================

WEBSOCKET_CONNECTIONS = Gauge(
    'uac_websocket_connections',
    'Current WebSocket connections',
    ['event_type'],
    registry=METRICS_REGISTRY
)

WEBSOCKET_EVENTS = Counter(
    'uac_websocket_events_total',
    'Total WebSocket events',
    ['event_type', 'status'],
    registry=METRICS_REGISTRY
)

# =============================================================================
# Schema Drift Metrics
# =============================================================================

SCHEMA_DRIFT_COUNT = Counter(
    'uac_schema_drift_checks_total',
    'Total schema drift checks',
    ['domain', 'severity', 'drift_type'],
    registry=METRICS_REGISTRY
)

SCHEMA_DRIFT_ISSUES = Gauge(
    'uac_schema_drift_issues',
    'Current schema drift issues by severity',
    ['domain', 'severity'],
    registry=METRICS_REGISTRY
)

# =============================================================================
# Database Query Metrics
# =============================================================================

DB_QUERY_COUNT = Counter(
    'uac_db_queries_total',
    'Total database queries',
    ['query_type', 'status', 'agent_id'],
    registry=METRICS_REGISTRY
)

DB_QUERY_LATENCY = Histogram(
    'uac_db_query_duration_seconds',
    'Database query latency in seconds',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=METRICS_REGISTRY
)

# =============================================================================
# Agent Operation Metrics
# =============================================================================

AGENT_OPERATION_COUNT = Counter(
    'uac_agent_operations_total',
    'Total agent operations',
    ['operation', 'status'],
    registry=METRICS_REGISTRY
)

AGENT_REGISTERED = Gauge(
    'uac_agents_registered',
    'Number of registered agents',
    registry=METRICS_REGISTRY
)

# =============================================================================
# System Info
# =============================================================================

SYSTEM_INFO = Info(
    'uac_build',
    'AI Agent Connector build information',
    registry=METRICS_REGISTRY
)

# =============================================================================
# Helper Functions
# =============================================================================

def init_metrics(app):
    """
    Initialize metrics for a Flask application.

    Adds before_request and after_request hooks to track HTTP metrics.

    Args:
        app: Flask application instance
    """
    # Set build info
    SYSTEM_INFO.info({
        'version': '0.1.0',
        'component': 'ai-agent-connector',
        'ontoguard': 'enabled'
    })

    @app.before_request
    def before_request():
        """Record request start time."""
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        """Record request metrics."""
        # Skip metrics endpoint itself
        if request.path == '/metrics':
            return response

        # Calculate latency
        latency = time.time() - getattr(g, 'start_time', time.time())

        # Normalize endpoint for cardinality control
        endpoint = _normalize_endpoint(request.path)

        # Record metrics
        HTTP_REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()

        HTTP_REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(latency)

        return response

    logger.info("Prometheus metrics initialized")


def _normalize_endpoint(path: str) -> str:
    """
    Normalize endpoint path to reduce cardinality.

    Replaces dynamic path segments (IDs, UUIDs) with placeholders.

    Args:
        path: Request path

    Returns:
        Normalized path
    """
    import re

    # Replace UUIDs
    path = re.sub(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        '{id}',
        path,
        flags=re.IGNORECASE
    )

    # Replace numeric IDs
    path = re.sub(r'/\d+(?=/|$)', '/{id}', path)

    # Replace agent IDs (alphanumeric with dashes)
    path = re.sub(r'/agents/[a-zA-Z0-9_-]+', '/agents/{agent_id}', path)

    return path


def get_metrics_blueprint() -> Blueprint:
    """
    Create a Flask Blueprint for the /metrics endpoint.

    Returns:
        Flask Blueprint with /metrics route
    """
    metrics_bp = Blueprint('metrics', __name__)

    @metrics_bp.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint."""
        return Response(
            generate_latest(METRICS_REGISTRY),
            mimetype=CONTENT_TYPE_LATEST
        )

    return metrics_bp


# =============================================================================
# Tracking Functions
# =============================================================================

def track_request(method: str, endpoint: str, status: int, latency: float):
    """
    Manually track an HTTP request.

    Args:
        method: HTTP method
        endpoint: Request endpoint
        status: Response status code
        latency: Request latency in seconds
    """
    HTTP_REQUEST_COUNT.labels(
        method=method,
        endpoint=endpoint,
        status=status
    ).inc()

    HTTP_REQUEST_LATENCY.labels(
        method=method,
        endpoint=endpoint
    ).observe(latency)


def track_ontoguard_validation(
    action: str,
    entity_type: str,
    allowed: bool,
    role: str = 'unknown',
    latency: Optional[float] = None
):
    """
    Track an OntoGuard validation.

    Args:
        action: Validated action (read, create, update, delete)
        entity_type: Entity type being validated
        allowed: Whether the action was allowed
        role: User role
        latency: Validation latency in seconds (optional)
    """
    result = 'allowed' if allowed else 'denied'

    ONTOGUARD_VALIDATION_COUNT.labels(
        action=action,
        entity_type=entity_type,
        result=result,
        role=role
    ).inc()

    if latency is not None:
        ONTOGUARD_VALIDATION_LATENCY.labels(
            action=action,
            entity_type=entity_type
        ).observe(latency)


@contextmanager
def track_ontoguard_validation_time(action: str, entity_type: str):
    """
    Context manager to track OntoGuard validation time.

    Usage:
        with track_ontoguard_validation_time('read', 'User'):
            result = adapter.validate_action(...)

    Args:
        action: Validated action
        entity_type: Entity type
    """
    start = time.time()
    try:
        yield
    finally:
        latency = time.time() - start
        ONTOGUARD_VALIDATION_LATENCY.labels(
            action=action,
            entity_type=entity_type
        ).observe(latency)


def track_websocket_connection(event_type: str, connected: bool):
    """
    Track WebSocket connection state.

    Args:
        event_type: Type of connection (validation, subscription)
        connected: True if connecting, False if disconnecting
    """
    if connected:
        WEBSOCKET_CONNECTIONS.labels(event_type=event_type).inc()
    else:
        WEBSOCKET_CONNECTIONS.labels(event_type=event_type).dec()


def track_websocket_event(event_type: str, success: bool = True):
    """
    Track a WebSocket event.

    Args:
        event_type: Event type (validate_action, check_permissions, etc.)
        success: Whether the event was successful
    """
    WEBSOCKET_EVENTS.labels(
        event_type=event_type,
        status='success' if success else 'error'
    ).inc()


def track_schema_drift(
    domain: str,
    severity: str,
    drift_type: str,
    issue_count: int = 0
):
    """
    Track a schema drift check.

    Args:
        domain: Domain being checked (hospital, finance)
        severity: Drift severity (CRITICAL, WARNING, INFO)
        drift_type: Type of drift (missing_column, type_change, new_column)
        issue_count: Number of issues found (for gauge)
    """
    SCHEMA_DRIFT_COUNT.labels(
        domain=domain,
        severity=severity,
        drift_type=drift_type
    ).inc()

    if issue_count > 0:
        SCHEMA_DRIFT_ISSUES.labels(
            domain=domain,
            severity=severity
        ).set(issue_count)


def track_db_query(
    query_type: str,
    success: bool,
    agent_id: str = 'unknown',
    latency: Optional[float] = None
):
    """
    Track a database query.

    Args:
        query_type: Query type (SELECT, INSERT, UPDATE, DELETE)
        success: Whether the query succeeded
        agent_id: Agent that executed the query
        latency: Query latency in seconds (optional)
    """
    DB_QUERY_COUNT.labels(
        query_type=query_type,
        status='success' if success else 'error',
        agent_id=agent_id
    ).inc()

    if latency is not None:
        DB_QUERY_LATENCY.labels(query_type=query_type).observe(latency)


@contextmanager
def track_db_query_time(query_type: str):
    """
    Context manager to track database query time.

    Usage:
        with track_db_query_time('SELECT'):
            result = connector.execute(query)

    Args:
        query_type: Query type
    """
    start = time.time()
    try:
        yield
    finally:
        latency = time.time() - start
        DB_QUERY_LATENCY.labels(query_type=query_type).observe(latency)


def track_agent_operation(operation: str, success: bool):
    """
    Track an agent operation.

    Args:
        operation: Operation type (register, unregister, query, etc.)
        success: Whether the operation succeeded
    """
    AGENT_OPERATION_COUNT.labels(
        operation=operation,
        status='success' if success else 'error'
    ).inc()


def set_registered_agents(count: int):
    """
    Set the number of registered agents.

    Args:
        count: Number of registered agents
    """
    AGENT_REGISTERED.set(count)


# =============================================================================
# Decorators
# =============================================================================

def track_latency(metric_name: str = 'http'):
    """
    Decorator to track function latency.

    Args:
        metric_name: Name prefix for the metric

    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                latency = time.time() - start
                logger.debug(f"{func.__name__} latency: {latency:.4f}s")
        return wrapper
    return decorator
