"""
AI Agent Connector - Simplified Entry Point (without GraphQL)

This is the main entry point for the AI Agent Connector application,
providing a Flask-based web server with OntoGuard integration.
"""

import os
from dotenv import load_dotenv

# Load .env BEFORE any app imports (NLToSQLConverter reads OPENAI_API_KEY at import time)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from flask import Flask, render_template, session, request, jsonify
from ai_agent_connector.app.api import api_bp
from ai_agent_connector.app.widgets import widget_bp
from ai_agent_connector.app.prompts import prompt_bp
import secrets
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name: str = None) -> Flask:
    app = Flask(__name__)

    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config['ENV'] = config_name
    app.config['DEBUG'] = config_name == 'development'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))

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

    # Register OntoGuard error handlers
    _register_ontoguard_error_handlers(app)

    # Initialize OntoGuard
    _initialize_ontoguard(app)

    return app


def _register_ontoguard_error_handlers(app: Flask) -> None:
    """Register OntoGuard-specific error handlers."""
    try:
        from ai_agent_connector.app.security.exceptions import (
            OntoGuardError,
            ValidationDeniedError,
            OntologyLoadError,
            ConfigurationError,
            PermissionDeniedError,
            ApprovalRequiredError
        )

        @app.errorhandler(ValidationDeniedError)
        def handle_validation_denied(error):
            """Handle action validation denial."""
            logger.warning(f"OntoGuard validation denied: {error.message}")
            return jsonify({
                'error': 'Validation Denied',
                'error_type': 'ValidationDeniedError',
                'action': error.action,
                'entity_type': error.entity_type,
                'reason': error.reason,
                'suggestions': error.suggestions
            }), 403

        @app.errorhandler(PermissionDeniedError)
        def handle_permission_denied(error):
            """Handle permission denial."""
            logger.warning(f"OntoGuard permission denied: {error.message}")
            return jsonify({
                'error': 'Permission Denied',
                'error_type': 'PermissionDeniedError',
                'role': error.role,
                'action': error.action,
                'entity_type': error.entity_type,
                'required_role': error.required_role
            }), 403

        @app.errorhandler(ApprovalRequiredError)
        def handle_approval_required(error):
            """Handle approval required error."""
            logger.warning(f"OntoGuard approval required: {error.message}")
            return jsonify({
                'error': 'Approval Required',
                'error_type': 'ApprovalRequiredError',
                'action': error.action,
                'entity_type': error.entity_type,
                'approver_role': error.approver_role
            }), 403

        @app.errorhandler(OntologyLoadError)
        def handle_ontology_load_error(error):
            """Handle ontology loading error."""
            logger.error(f"OntoGuard ontology load error: {error.message}")
            return jsonify({
                'error': 'Ontology Load Error',
                'error_type': 'OntologyLoadError',
                'path': error.path,
                'message': error.error
            }), 500

        @app.errorhandler(ConfigurationError)
        def handle_configuration_error(error):
            """Handle configuration error."""
            logger.error(f"OntoGuard configuration error: {error.message}")
            return jsonify({
                'error': 'Configuration Error',
                'error_type': 'ConfigurationError',
                'config_path': error.config_path,
                'field': error.field,
                'message': error.error
            }), 500

        @app.errorhandler(OntoGuardError)
        def handle_ontoguard_error(error):
            """Handle generic OntoGuard error."""
            logger.error(f"OntoGuard error: {error.message}")
            return jsonify({
                'error': 'OntoGuard Error',
                'error_type': error.__class__.__name__,
                'message': str(error)
            }), 500

        logger.info("OntoGuard error handlers registered")

    except ImportError:
        logger.warning("OntoGuard security module not available, error handlers not registered")


def _initialize_ontoguard(app: Flask) -> None:
    """Initialize OntoGuard with configuration."""
    try:
        from ai_agent_connector.app.security import initialize_ontoguard

        # Get ontology path from config or use default (hospital.owl for hospital domain)
        ontology_path = os.getenv(
            'ONTOGUARD_ONTOLOGY_PATH',
            os.path.join(os.path.dirname(__file__), 'ontologies', 'hospital.owl')
        )

        config = {
            'ontology_paths': [ontology_path] if os.path.exists(ontology_path) else [],
            'config_path': os.getenv(
                'ONTOGUARD_CONFIG_PATH',
                os.path.join(os.path.dirname(__file__), 'config', 'ontoguard.yaml')
            )
        }

        if initialize_ontoguard(config):
            logger.info(f"OntoGuard initialized with ontology: {ontology_path}")
        else:
            logger.warning("OntoGuard running in pass-through mode")

    except ImportError:
        logger.warning("OntoGuard module not available")
    except Exception as e:
        logger.error(f"OntoGuard initialization error: {e}")


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
