"""
GraphQL API routes with playground and subscriptions
"""

from flask import Blueprint, request, jsonify, render_template_string, Response, stream_with_context
from graphql import graphql_sync
from graphql.error import format_error
import json
import threading
from collections import defaultdict
from typing import Dict, Any, List
import queue
import time

from .schema import schema, set_managers

graphql_bp = Blueprint('graphql', __name__, url_prefix='/graphql')

# Subscription manager for real-time updates
_subscription_queues: Dict[str, List[queue.Queue]] = defaultdict(list)
_subscription_lock = threading.Lock()


def add_subscription(channel: str, queue_obj: queue.Queue):
    """Add a subscription queue"""
    with _subscription_lock:
        _subscription_queues[channel].append(queue_obj)


def remove_subscription(channel: str, queue_obj: queue.Queue):
    """Remove a subscription queue"""
    with _subscription_lock:
        if channel in _subscription_queues:
            try:
                _subscription_queues[channel].remove(queue_obj)
            except ValueError:
                pass


def publish_subscription(channel: str, data: Dict[str, Any]):
    """Publish data to all subscribers of a channel"""
    with _subscription_lock:
        queues_to_remove = []
        for q in _subscription_queues.get(channel, []):
            try:
                q.put_nowait(data)
            except queue.Full:
                queues_to_remove.append(q)
        
        # Remove full queues
        for q in queues_to_remove:
            remove_subscription(channel, q)


@graphql_bp.route('/playground', methods=['GET'])
def graphql_playground():
    """GraphQL Playground UI"""
    playground_html = """
<!DOCTYPE html>
<html>
<head>
    <title>GraphQL Playground</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/css/index.css" />
    <link rel="shortcut icon" href="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/favicon.png" />
    <script src="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/js/middleware.js"></script>
</head>
<body>
    <div id="root">
        <style>
            body {
                background-color: rgb(23, 42, 58);
                font-family: Open Sans, sans-serif;
                height: 100vh;
                margin: 0;
                overflow: hidden;
            }
            #root {
                height: 100vh;
            }
        </style>
        <script>
            window.addEventListener('load', function (event) {
                GraphQLPlayground.init(document.getElementById('root'), {
                    endpoint: '/graphql',
                    subscriptionEndpoint: '/graphql/subscriptions',
                    settings: {
                        'editor.theme': 'dark',
                        'editor.cursorShape': 'line',
                        'editor.fontSize': 14,
                        'editor.fontFamily': "'Source Code Pro', 'Consolas', 'Inconsolata', 'Droid Sans Mono', 'Monaco', monospace",
                        'editor.reuseHeaders': true,
                        'request.credentials': 'same-origin',
                        'tracing.hideTracingResponse': false
                    }
                })
            });
        </script>
    </div>
</body>
</html>
    """
    return playground_html


@graphql_bp.route('', methods=['POST'])
def graphql_query():
    """GraphQL query/mutation endpoint"""
    try:
        data = request.get_json()
        query = data.get('query')
        variables = data.get('variables')
        operation_name = data.get('operationName')
        
        if not query:
            return jsonify({
                'errors': [{'message': 'No query provided'}]
            }), 400
        
        # Execute GraphQL query
        result = graphql_sync(
            schema,
            query,
            variable_values=variables,
            operation_name=operation_name,
            context_value={'request': request}
        )
        
        response_data = {'data': result.data}
        
        if result.errors:
            response_data['errors'] = [
                {
                    'message': error.message,
                    'locations': [{'line': loc.line, 'column': loc.column} for loc in error.locations] if error.locations else None,
                    'path': error.path
                }
                for error in result.errors
            ]
        
        status_code = 200
        if result.errors:
            status_code = 400
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        return jsonify({
            'errors': [{'message': str(e)}]
        }), 500


@graphql_bp.route('/schema', methods=['GET'])
def graphql_schema():
    """Get GraphQL schema in SDL format"""
    try:
        schema_str = str(schema)
        return jsonify({
            'schema': schema_str,
            'sdl': schema_str
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@graphql_bp.route('/subscriptions', methods=['GET', 'POST'])
def graphql_subscriptions():
    """
    GraphQL subscriptions endpoint (WebSocket-like using Server-Sent Events)
    For full WebSocket support, integrate with Flask-SocketIO
    """
    if request.method == 'GET':
        # Return SSE endpoint info
        return jsonify({
            'endpoint': '/graphql/subscriptions/stream',
            'method': 'GET',
            'format': 'server-sent-events',
            'channels': [
                'cost_updated',
                'agent_status_changed',
                'failover_switched',
                'audit_log_created',
                'notification_created',
                'budget_alert_triggered'
            ]
        }), 200
    
    # POST for subscription queries
    try:
        data = request.get_json()
        query = data.get('query')
        variables = data.get('variables')
        operation_name = data.get('operationName')
        
        if not query:
            return jsonify({
                'errors': [{'message': 'No query provided'}]
            }), 400
        
        # Parse subscription query to determine channel
        # This is a simplified version - full implementation would parse the AST
        channel = None
        if 'cost_updated' in query:
            channel = 'cost_updated'
        elif 'agent_status_changed' in query:
            channel = 'agent_status_changed'
        elif 'failover_switched' in query:
            channel = 'failover_switched'
        elif 'audit_log_created' in query:
            channel = 'audit_log_created'
        elif 'notification_created' in query:
            channel = 'notification_created'
        elif 'budget_alert_triggered' in query:
            channel = 'budget_alert_triggered'
        
        if channel:
            # Create subscription queue
            sub_queue = queue.Queue(maxsize=100)
            add_subscription(channel, sub_queue)
            
            return jsonify({
                'success': True,
                'channel': channel,
                'subscription_id': id(sub_queue),
                'stream_url': f'/graphql/subscriptions/stream?channel={channel}&id={id(sub_queue)}'
            }), 200
        else:
            return jsonify({
                'errors': [{'message': 'Invalid subscription query'}]
            }), 400
            
    except Exception as e:
        return jsonify({
            'errors': [{'message': str(e)}]
        }), 500


@graphql_bp.route('/subscriptions/stream', methods=['GET'])
def graphql_subscription_stream():
    """Server-Sent Events stream for subscriptions"""
    channel = request.args.get('channel')
    subscription_id = request.args.get('id')
    
    if not channel:
        return jsonify({'error': 'Channel required'}), 400
    
    def event_stream():
        """Generate SSE events"""
        sub_queue = queue.Queue(maxsize=100)
        add_subscription(channel, sub_queue)
        
        try:
            yield f"data: {json.dumps({'type': 'connected', 'channel': channel})}\n\n"
            
            while True:
                try:
                    # Wait for data with timeout
                    data = sub_queue.get(timeout=30)
                    if data:
                        yield f"data: {json.dumps(data)}\n\n"
                except queue.Empty:
                    # Send keepalive
                    yield f": keepalive\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    break
        finally:
            remove_subscription(channel, sub_queue)
            yield f"data: {json.dumps({'type': 'disconnected'})}\n\n"
    
    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


def init_graphql(agent_registry, ai_agent_manager, cost_tracker, audit_logger, failover_manager):
    """Initialize GraphQL with managers"""
    set_managers(agent_registry, ai_agent_manager, cost_tracker, audit_logger, failover_manager)


# Hook into cost tracker to publish subscriptions
def _hook_cost_tracker(cost_tracker):
    """Hook into cost tracker to publish cost updates"""
    original_track_call = cost_tracker.track_call
    
    def tracked_track_call(*args, **kwargs):
        result = original_track_call(*args, **kwargs)
        if result:
            # Publish cost update
            publish_subscription('cost_updated', {
                'type': 'cost_updated',
                'data': {
                    'call_id': result.call_id,
                    'agent_id': result.agent_id,
                    'provider': result.provider,
                    'cost_usd': result.cost_usd,
                    'timestamp': result.timestamp
                }
            })
        return result
    
    cost_tracker.track_call = tracked_track_call


# Hook into failover manager to publish subscriptions
def _hook_failover_manager(failover_manager):
    """Hook into failover manager to publish failover events"""
    if hasattr(failover_manager, '_switch_provider'):
        original_switch = failover_manager._switch_provider
        
        def tracked_switch(*args, **kwargs):
            result = original_switch(*args, **kwargs)
            if result and len(args) > 0:
                agent_id = args[0]
                # Publish failover switch
                publish_subscription('failover_switched', {
                    'type': 'failover_switched',
                    'data': {
                        'agent_id': agent_id,
                        'timestamp': time.time()
                    }
                })
            return result
        
        failover_manager._switch_provider = tracked_switch
