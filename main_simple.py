"""
AI Agent Connector - Simplified Entry Point (without GraphQL)
"""

from flask import Flask, render_template, session, request, jsonify
from ai_agent_connector.app.api import api_bp
from ai_agent_connector.app.widgets import widget_bp
from ai_agent_connector.app.prompts import prompt_bp
import os
import secrets


def create_app(config_name: str = None) -> Flask:
    app = Flask(__name__)

    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config['ENV'] = config_name
    app.config['DEBUG'] = config_name == 'development'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

    # Air-gapped mode configuration
    app.config['AIR_GAPPED_MODE'] = os.getenv('AIR_GAPPED_MODE', 'false').lower() in ('true', '1', 'yes')
    app.config['LOCAL_AI_BASE_URL'] = os.getenv('LOCAL_AI_BASE_URL', 'http://localhost:11434')
    app.config['LOCAL_AI_MODEL'] = os.getenv('LOCAL_AI_MODEL', 'llama2')

    # Register blueprints (without GraphQL)
    app.register_blueprint(api_bp)
    app.register_blueprint(widget_bp)
    app.register_blueprint(prompt_bp)

    # Generate console PIN
    console_pin = secrets.randbelow(10000)
    app.config['CONSOLE_PIN'] = f"{console_pin:04d}"

    @app.route('/api/console/unlock', methods=['POST'])
    def unlock_console():
        data = request.get_json()
        pin = data.get('pin', '')
        if pin == app.config['CONSOLE_PIN']:
            session['console_unlocked'] = True
            return jsonify({'success': True, 'message': 'Console unlocked'}), 200
        return jsonify({'success': False, 'message': 'Invalid PIN'}), 401

    @app.route('/console')
    def console():
        if not session.get('console_unlocked', False):
            return render_template('console_locked.html')
        return render_template('console.html')

    @app.route('/')
    def index():
        return render_template('dashboard.html')

    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/wizard')
    def wizard():
        return render_template('wizard.html')

    @app.route('/agents')
    def agents():
        return render_template('agents.html')

    @app.route('/agents/<agent_id>')
    def agent_detail(agent_id):
        return render_template('agent_detail.html')

    @app.route('/notifications')
    def notifications():
        return render_template('notifications.html')

    @app.route('/analytics')
    def analytics_dashboard():
        return render_template('analytics_dashboard.html')

    @app.route('/agents/<agent_id>/access-preview')
    def access_preview(agent_id):
        return render_template('access_preview.html')

    @app.route('/collaboration/trace')
    def collaboration_trace():
        return render_template('collaboration_trace.html')

    @app.route('/prompts')
    def prompts():
        return render_template('prompts/index.html')

    @app.route('/cost-dashboard')
    def cost_dashboard():
        return render_template('cost_dashboard.html')

    @app.route('/api')
    def api_info():
        return {
            'service': 'AI Agent Connector',
            'version': '0.1.0',
            'status': 'running',
            'note': 'Running in simplified mode (no GraphQL)'
        }

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '127.0.0.1')

    print("=" * 60)
    print("AI Agent Connector Starting (Simplified Mode)...")
    print("=" * 60)
    print(f"Server: http://{host}:{port}")
    print(f"Dashboard: http://{host}:{port}/dashboard")
    print(f"Wizard: http://{host}:{port}/wizard")
    print(f"API: http://{host}:{port}/api")
    print(f"Console PIN: {app.config['CONSOLE_PIN']}")
    print("=" * 60)

    app.run(host=host, port=port, debug=True, use_reloader=False)
