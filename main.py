"""
AI Agent Connector - Entry Point
Flask application for managing AI agent connections
"""

from flask import Flask, render_template, session, request, jsonify
from ai_agent_connector.app.api import api_bp
from ai_agent_connector.app.graphql import graphql_bp, init_graphql
from ai_agent_connector.app.graphql.routes import _hook_cost_tracker, _hook_failover_manager
from ai_agent_connector.app.widgets import widget_bp
from ai_agent_connector.app.prompts import prompt_bp
import os
import secrets


def create_app(config_name: str = None) -> Flask:
    """
    Create and configure Flask application
    
    Args:
        config_name: Configuration name (development, production, testing)
        
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config['ENV'] = config_name
    app.config['DEBUG'] = config_name == 'development'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
    
    # Air-gapped mode configuration
    app.config['AIR_GAPPED_MODE'] = os.getenv('AIR_GAPPED_MODE', 'false').lower() in ('true', '1', 'yes')
    app.config['LOCAL_AI_BASE_URL'] = os.getenv('LOCAL_AI_BASE_URL', 'http://localhost:11434')  # Default Ollama
    app.config['LOCAL_AI_MODEL'] = os.getenv('LOCAL_AI_MODEL', 'llama2')  # Default model
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Register GraphQL blueprint first
    app.register_blueprint(graphql_bp)
    
    # Register widget blueprint
    app.register_blueprint(widget_bp)
    
    # Register prompt studio blueprint
    app.register_blueprint(prompt_bp)
    
    # Initialize GraphQL with managers from API routes
    # Import after app is created to avoid circular imports
    from ai_agent_connector.app.api.routes import (
        agent_registry,
        ai_agent_manager,
        cost_tracker,
        audit_logger
    )
    
    # Get failover manager
    failover_manager = None
    if hasattr(ai_agent_manager, '_failover_manager'):
        failover_manager = ai_agent_manager._failover_manager
    
    # Initialize GraphQL
    init_graphql(agent_registry, ai_agent_manager, cost_tracker, audit_logger, failover_manager)
    
    # Hook into managers for subscriptions
    _hook_cost_tracker(cost_tracker)
    if failover_manager:
        _hook_failover_manager(failover_manager)
    
    # Generate console PIN on startup
    console_pin = secrets.randbelow(10000)
    console_pin_str = f"{console_pin:04d}"  # 4-digit PIN with leading zeros
    app.config['CONSOLE_PIN'] = console_pin_str
    
    @app.route('/api/console/unlock', methods=['POST'])
    def unlock_console():
        """Unlock console with PIN"""
        data = request.get_json()
        pin = data.get('pin', '')
        
        if pin == app.config['CONSOLE_PIN']:
            session['console_unlocked'] = True
            return jsonify({'success': True, 'message': 'Console unlocked'}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid PIN'}), 401
    
    @app.route('/console')
    def console():
        """Console/log viewer page - requires PIN unlock"""
        if not session.get('console_unlocked', False):
            return render_template('console_locked.html')
        return render_template('console.html')
    
    @app.route('/')
    def index():
        """Root endpoint - redirect to dashboard"""
        return render_template('dashboard.html')
    
    @app.route('/analytics')
    def analytics_dashboard():
        """Adoption analytics dashboard"""
        return render_template('analytics_dashboard.html')
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard page"""
        return render_template('dashboard.html')
    
    @app.route('/wizard')
    def wizard():
        """Integration wizard page"""
        return render_template('wizard.html')
    
    @app.route('/agents')
    def agents():
        """Agents management page"""
        return render_template('agents.html')
    
    @app.route('/agents/<agent_id>')
    def agent_detail(agent_id):
        """Agent detail page"""
        return render_template('agent_detail.html')
    
    @app.route('/notifications')
    def notifications():
        """Security notifications page"""
        return render_template('notifications.html')
    
    @app.route('/agents/<agent_id>/access-preview')
    def access_preview(agent_id):
        """Agent access preview page"""
        return render_template('access_preview.html')
    
    @app.route('/collaboration/trace')
    def collaboration_trace():
        """Collaboration trace visualization page"""
        return render_template('collaboration_trace.html')
    
    @app.route('/prompts')
    def prompts():
        """Prompt engineering studio"""
        return render_template('prompts/index.html')
    
    @app.route('/cost-dashboard')
    def cost_dashboard():
        """Cost tracking dashboard page"""
        return render_template('cost_dashboard.html')
    
    @app.route('/api')
    def api_info():
        """API information endpoint"""
        return {
            'service': 'AI Agent Connector',
            'version': '0.1.0',
            'status': 'running',
            'endpoints': {
                'health': '/api/health',
                'api_docs': '/api/api-docs',
                'test_database': '/api/databases/test',
                'register_agent': '/api/agents/register',
                'list_agents': '/api/agents',
                'get_agent': '/api/agents/<agent_id>',
                'update_agent_database': '/api/agents/<agent_id>/database',
                'revoke_agent': '/api/agents/<agent_id>',
                'list_tables': '/api/agents/<agent_id>/tables',
                'access_preview': '/api/agents/<agent_id>/access-preview',
                'set_permissions': '/api/agents/<agent_id>/permissions/resources',
                'list_permissions': '/api/agents/<agent_id>/permissions/resources',
                'revoke_permissions': '/api/agents/<agent_id>/permissions/resources/<resource_id>',
                'execute_query': '/api/agents/<agent_id>/query',
                'natural_language_query': '/api/agents/<agent_id>/query/natural',
                'audit_logs': '/api/audit/logs',
                'audit_log': '/api/audit/logs/<log_id>',
                'audit_statistics': '/api/audit/statistics',
                'notifications': '/api/notifications',
                'notification_stats': '/api/notifications/stats',
                'cost_dashboard': '/api/cost/dashboard',
                'cost_export': '/api/cost/export',
                'cost_stats': '/api/cost/stats',
                'budget_alerts': '/api/cost/budget-alerts'
            }
        }
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '127.0.0.1')
    
    console_pin = app.config.get('CONSOLE_PIN', 'N/A')
    
    print("=" * 60)
    print("🚀 AI Agent Connector Starting...")
    print("=" * 60)
    print(f"📍 Server running on: http://{host}:{port}")
    print(f"🌐 Dashboard: http://{host}:{port}/dashboard")
    print(f"🔧 Wizard: http://{host}:{port}/wizard")
    print(f"📚 API Docs: http://{host}:{port}/api/api-docs")
    print(f"🔷 GraphQL Playground: http://{host}:{port}/graphql/playground")
    print(f"🖥️  Console: http://{host}:{port}/console")
    print("=" * 60)
    print(f"🔐 Console PIN: {console_pin}")
    print("=" * 60)
    print("💡 Press CTRL+C to stop the server")
    print("=" * 60)
    print()
    
    app.run(host=host, port=port, debug=True, use_reloader=False)
