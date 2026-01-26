"""
GCP Cloud Functions handler for AI Agent Connector
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


def cloud_function_handler(request):
    """
    GCP Cloud Functions HTTP handler
    
    Args:
        request: Flask request object (Cloud Functions provides this)
        
    Returns:
        Flask response
    """
    # Lazy load app on first invocation
    app = _lazy_import_app()
    
    # Use Flask's test client to handle the request
    with app.test_request_context(
        path=request.path,
        method=request.method,
        headers=dict(request.headers),
        data=request.get_data(),
        query_string=request.query_string
    ):
        try:
            response = app.full_dispatch_request()
        except Exception as e:
            response = app.handle_exception(e)
    
    return response


def health_handler(request):
    """
    Lightweight health check handler (no app initialization)
    """
    from flask import jsonify
    return jsonify({
        'status': 'healthy',
        'service': 'ai-agent-connector',
        'runtime': 'gcp-cloud-functions',
        'cold_start': not _initialized
    }), 200

