"""
Widget routes for embeddable query widgets
"""

from flask import render_template, request, jsonify, Response, make_response
from functools import wraps
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from . import widget_bp
from ..api.routes import agent_registry, ai_agent_manager, access_control
from ..utils.helpers import validate_json


# In-memory widget storage (use database in production)
widget_store = {}


def generate_widget_key():
    """Generate a secure widget API key"""
    return secrets.token_urlsafe(32)


def validate_widget_key(widget_key):
    """Validate widget API key"""
    if not widget_key:
        return None
    
    # Find widget by key
    for widget_id, widget_data in widget_store.items():
        if widget_data.get('api_key') == widget_key:
            return widget_data
    
    return None


def widget_auth_required(f):
    """Decorator to require widget API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        widget_key = request.headers.get('X-Widget-Key') or request.args.get('widget_key')
        
        if not widget_key:
            return jsonify({'error': 'Widget API key required'}), 401
        
        widget_data = validate_widget_key(widget_key)
        if not widget_data:
            return jsonify({'error': 'Invalid widget API key'}), 401
        
        # Add widget data to request context
        request.widget_data = widget_data
        return f(*args, **kwargs)
    
    return decorated_function


@widget_bp.route('/embed/<widget_id>')
def embed_widget(widget_id):
    """
    Embeddable widget endpoint - returns HTML that can be embedded in iframe
    """
    widget_data = widget_store.get(widget_id)
    
    if not widget_data:
        return render_template('widget/error.html', 
                             error='Widget not found'), 404
    
    # Get theme from query params or use default
    theme = request.args.get('theme', widget_data.get('theme', 'default'))
    height = request.args.get('height', widget_data.get('height', '600px'))
    width = request.args.get('width', widget_data.get('width', '100%'))
    
    # Get agent_id from widget config
    agent_id = widget_data.get('agent_id')
    if not agent_id:
        return render_template('widget/error.html', 
                             error='Widget not configured'), 400
    
    # Check if agent exists
    if not agent_registry.get_agent(agent_id):
        return render_template('widget/error.html', 
                             error='Agent not found'), 404
    
    # Render widget with theme
    response = make_response(render_template(
        'widget/embed.html',
        widget_id=widget_id,
        agent_id=agent_id,
        theme=theme,
        height=height,
        width=width,
        widget_config=widget_data
    ))
    
    # Set iframe-friendly headers
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Content-Security-Policy'] = "frame-ancestors *"
    
    return response


@widget_bp.route('/api/query', methods=['POST'])
@widget_auth_required
def widget_query():
    """
    Execute query from widget (requires widget API key)
    """
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    widget_data = request.widget_data
    agent_id = widget_data.get('agent_id')
    
    if not agent_id:
        return jsonify({'error': 'Widget not configured'}), 400
    
    # Get agent
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    # Execute query using natural language
    try:
        # Use the agent's API key for authentication
        agent = agent_registry.get_agent(agent_id)
        agent_api_key = agent.get('api_key')
        
        # Get database connector for schema info
        connector = agent_registry.get_database_connector(agent_id)
        if not connector:
            return jsonify({
                'success': False,
                'error': 'Agent does not have a database connection configured'
            }), 400
        
        # Convert natural language to SQL
        from ..api.routes import nl_converter
        schema_info = nl_converter.get_schema_info(connector)
        conversion_result = nl_converter.convert_to_sql(
            natural_language_query=query,
            schema_info=schema_info,
            database_type="PostgreSQL"
        )
        
        if conversion_result.get('error') or not conversion_result.get('sql'):
            return jsonify({
                'success': False,
                'error': conversion_result.get('error', 'Failed to convert query to SQL')
            }), 400
        
        sql_query = conversion_result['sql']
        
        # Execute the SQL query
        result = ai_agent_manager.execute_query(
            agent_id=agent_id,
            query=sql_query,
            api_key=agent_api_key
        )
        
        # Track widget usage
        widget_data['usage_count'] = widget_data.get('usage_count', 0) + 1
        widget_data['last_used'] = datetime.utcnow().isoformat()
        
        return jsonify({
            'success': True,
            'result': result,
            'widget_id': widget_data.get('widget_id')
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@widget_bp.route('/api/create', methods=['POST'])
def create_widget():
    """
    Create a new embeddable widget
    Requires agent API key for authentication
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['agent_id', 'name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    agent_id = data['agent_id']
    widget_name = data['name']
    
    # Authenticate with agent API key
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401
    
    # Verify agent exists and API key is valid
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    # Verify API key matches agent
    if agent.get('api_key') != api_key:
        return jsonify({'error': 'Invalid API key'}), 401
    
    # Generate widget ID and API key
    widget_id = f"widget_{secrets.token_urlsafe(16)}"
    widget_api_key = generate_widget_key()
    
    # Create widget configuration
    widget_data = {
        'widget_id': widget_id,
        'name': widget_name,
        'agent_id': agent_id,
        'api_key': widget_api_key,
        'theme': data.get('theme', 'default'),
        'height': data.get('height', '600px'),
        'width': data.get('width', '100%'),
        'created_at': datetime.utcnow().isoformat(),
        'created_by': data.get('created_by', 'unknown'),
        'usage_count': 0,
        'allowed_domains': data.get('allowed_domains', []),  # Optional domain restrictions
        'custom_css': data.get('custom_css', ''),  # Custom CSS for theming
        'custom_js': data.get('custom_js', ''),  # Custom JS for advanced customization
    }
    
    # Store widget
    widget_store[widget_id] = widget_data
    
    # Generate embed code
    embed_code = f'''<iframe 
    src="{request.host_url.rstrip('/')}/widget/embed/{widget_id}?theme={widget_data['theme']}"
    width="{widget_data['width']}"
    height="{widget_data['height']}"
    frameborder="0"
    allow="clipboard-read; clipboard-write"
    style="border: none; border-radius: 8px;">
</iframe>'''
    
    return jsonify({
        'success': True,
        'widget_id': widget_id,
        'widget_api_key': widget_api_key,
        'embed_code': embed_code,
        'embed_url': f"{request.host_url.rstrip('/')}/widget/embed/{widget_id}",
        'widget': widget_data
    }), 201


@widget_bp.route('/api/list', methods=['GET'])
def list_widgets():
    """
    List all widgets for an agent
    Requires agent API key
    """
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401
    
    # Find agent by API key
    agent_id = None
    for agent_id_key, agent in agent_registry._agents.items():
        if agent.get('api_key') == api_key:
            agent_id = agent_id_key
            break
    
    if not agent_id:
        return jsonify({'error': 'Invalid API key'}), 401
    
    # Get widgets for this agent
    agent_widgets = [
        {
            'widget_id': w['widget_id'],
            'name': w['name'],
            'theme': w['theme'],
            'created_at': w['created_at'],
            'usage_count': w.get('usage_count', 0),
            'last_used': w.get('last_used'),
            'embed_url': f"{request.host_url.rstrip('/')}/widget/embed/{w['widget_id']}"
        }
        for w in widget_store.values()
        if w.get('agent_id') == agent_id
    ]
    
    return jsonify({
        'success': True,
        'widgets': agent_widgets,
        'count': len(agent_widgets)
    })


@widget_bp.route('/api/<widget_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_widget(widget_id):
    """
    Get, update, or delete a widget
    """
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401
    
    widget_data = widget_store.get(widget_id)
    if not widget_data:
        return jsonify({'error': 'Widget not found'}), 404
    
    # Verify API key matches agent
    agent = agent_registry.get_agent(widget_data.get('agent_id'))
    if not agent or agent.get('api_key') != api_key:
        return jsonify({'error': 'Invalid API key'}), 401
    
    if request.method == 'GET':
        # Return widget info (without sensitive data)
        return jsonify({
            'success': True,
            'widget': {
                'widget_id': widget_data['widget_id'],
                'name': widget_data['name'],
                'agent_id': widget_data['agent_id'],
                'theme': widget_data['theme'],
                'height': widget_data['height'],
                'width': widget_data['width'],
                'created_at': widget_data['created_at'],
                'usage_count': widget_data.get('usage_count', 0),
                'last_used': widget_data.get('last_used'),
                'embed_url': f"{request.host_url.rstrip('/')}/widget/embed/{widget_id}"
            }
        })
    
    elif request.method == 'PUT':
        # Update widget
        data = request.get_json()
        
        # Update allowed fields
        updatable_fields = ['name', 'theme', 'height', 'width', 'custom_css', 'custom_js', 'allowed_domains']
        for field in updatable_fields:
            if field in data:
                widget_data[field] = data[field]
        
        widget_data['updated_at'] = datetime.utcnow().isoformat()
        
        return jsonify({
            'success': True,
            'widget': widget_data
        })
    
    elif request.method == 'DELETE':
        # Delete widget
        del widget_store[widget_id]
        return jsonify({
            'success': True,
            'message': 'Widget deleted'
        })


@widget_bp.route('/api/<widget_id>/regenerate-key', methods=['POST'])
def regenerate_widget_key(widget_id):
    """
    Regenerate widget API key
    """
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401
    
    widget_data = widget_store.get(widget_id)
    if not widget_data:
        return jsonify({'error': 'Widget not found'}), 404
    
    # Verify API key matches agent
    agent = agent_registry.get_agent(widget_data.get('agent_id'))
    if not agent or agent.get('api_key') != api_key:
        return jsonify({'error': 'Invalid API key'}), 401
    
    # Generate new key
    new_key = generate_widget_key()
    widget_data['api_key'] = new_key
    widget_data['key_regenerated_at'] = datetime.utcnow().isoformat()
    
    return jsonify({
        'success': True,
        'widget_api_key': new_key,
        'message': 'Widget API key regenerated'
    })


@widget_bp.route('/api/<widget_id>/embed-code', methods=['GET'])
def get_embed_code(widget_id):
    """
    Get embed code for a widget
    """
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401
    
    widget_data = widget_store.get(widget_id)
    if not widget_data:
        return jsonify({'error': 'Widget not found'}), 404
    
    # Verify API key matches agent
    agent = agent_registry.get_agent(widget_data.get('agent_id'))
    if not agent or agent.get('api_key') != api_key:
        return jsonify({'error': 'Invalid API key'}), 401
    
    # Generate embed code with current settings
    theme = request.args.get('theme', widget_data.get('theme', 'default'))
    height = request.args.get('height', widget_data.get('height', '600px'))
    width = request.args.get('width', widget_data.get('width', '100%'))
    
    embed_code = f'''<iframe 
    src="{request.host_url.rstrip('/')}/widget/embed/{widget_id}?theme={theme}"
    width="{width}"
    height="{height}"
    frameborder="0"
    allow="clipboard-read; clipboard-write"
    style="border: none; border-radius: 8px;">
</iframe>'''
    
    return jsonify({
        'success': True,
        'embed_code': embed_code,
        'embed_url': f"{request.host_url.rstrip('/')}/widget/embed/{widget_id}",
        'widget_id': widget_id
    })

