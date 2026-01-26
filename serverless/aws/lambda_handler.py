"""
AWS Lambda handler for AI Agent Connector
Optimized for cold start <2s with lazy imports and connection pooling
"""
import json
import os
import time
from typing import Dict, Any, Optional

# Lazy imports to reduce cold start time
_app = None
_initialized = False
_init_start_time = None


def _lazy_import_app():
    """Lazy import Flask app to reduce cold start time"""
    global _app, _initialized, _init_start_time
    
    if _initialized:
        return _app
    
    _init_start_time = time.time()
    
    # Import only what's needed
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Import Flask app factory
    from main import create_app
    
    # Create app with serverless configuration
    _app = create_app('production')
    
    # Configure for serverless
    _app.config['SERVERLESS'] = True
    _app.config['DATABASE_POOL_SIZE'] = int(os.getenv('DATABASE_POOL_SIZE', '5'))
    _app.config['DATABASE_MAX_OVERFLOW'] = int(os.getenv('DATABASE_MAX_OVERFLOW', '10'))
    
    _initialized = True
    init_time = time.time() - _init_start_time
    
    # Log initialization time (for monitoring)
    if init_time > 2.0:
        print(f"WARNING: Cold start took {init_time:.2f}s (target: <2s)")
    
    return _app


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for API Gateway requests
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    # Lazy load app on first invocation
    app = _lazy_import_app()
    
    # Parse API Gateway event
    path = event.get('path', '/')
    http_method = event.get('httpMethod', 'GET')
    headers = event.get('headers', {})
    query_string_parameters = event.get('queryStringParameters') or {}
    body = event.get('body', '')
    
    # Convert API Gateway event to WSGI environment
    environ = {
        'REQUEST_METHOD': http_method,
        'PATH_INFO': path,
        'QUERY_STRING': '&'.join([f'{k}={v}' for k, v in query_string_parameters.items()]),
        'SERVER_NAME': headers.get('Host', 'localhost'),
        'SERVER_PORT': headers.get('X-Forwarded-Port', '443'),
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': headers.get('X-Forwarded-Proto', 'https'),
        'wsgi.input': None,
        'wsgi.errors': None,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }
    
    # Add headers
    for key, value in headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            key = f'HTTP_{key}'
        environ[key] = value
    
    # Handle body
    if body:
        environ['CONTENT_LENGTH'] = str(len(body))
        environ['wsgi.input'] = type('obj', (object,), {'read': lambda: body})()
    
    # Create response
    from werkzeug.wrappers import Response
    
    with app.request_context(environ):
        try:
            response = app.full_dispatch_request()
        except Exception as e:
            response = app.handle_exception(e)
    
    # Convert Flask response to API Gateway format
    return {
        'statusCode': response.status_code,
        'headers': dict(response.headers),
        'body': response.get_data(as_text=True)
    }


def health_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lightweight health check handler (no app initialization)
    """
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'status': 'healthy',
            'service': 'ai-agent-connector',
            'runtime': 'aws-lambda',
            'cold_start': not _initialized
        })
    }

