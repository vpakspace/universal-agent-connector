"""
Prompt Engineering Studio Routes
"""

from flask import render_template, request, jsonify, session
from functools import wraps
from typing import Dict, Any, Optional
import secrets
import json

from . import prompt_bp
from .models import (
    PromptStore, PromptTemplate, PromptVariable, ABTest,
    PromptStatus, prompt_store
)
from ..api.routes import agent_registry


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key by checking if agent exists
        agent = None
        for agent_id, agent_data in agent_registry._agents.items():
            if agent_data.get('api_key') == api_key:
                agent = agent_data
                break
        
        if not agent:
            return jsonify({'error': 'Invalid API key'}), 401
        
        request.agent = agent
        return f(*args, **kwargs)
    return decorated_function


@prompt_bp.route('/')
def index():
    """Prompt studio home page"""
    return render_template('prompts/index.html')


@prompt_bp.route('/editor/<prompt_id>')
def editor(prompt_id: str):
    """Visual prompt editor"""
    prompt = prompt_store.get_prompt(prompt_id)
    if not prompt:
        return jsonify({'error': 'Prompt not found'}), 404
    
    return render_template('prompts/editor.html', prompt=prompt.to_dict())


@prompt_bp.route('/editor')
def new_editor():
    """New prompt editor"""
    return render_template('prompts/editor.html', prompt=None)


@prompt_bp.route('/templates')
def templates():
    """Template library page"""
    return render_template('prompts/templates.html')


@prompt_bp.route('/ab-testing')
def ab_testing():
    """A/B testing dashboard"""
    return render_template('prompts/ab_testing.html')


# API Routes

@prompt_bp.route('/api/prompts', methods=['GET'])
@require_api_key
def list_prompts():
    """List prompts for agent"""
    agent_id = request.agent.get('agent_id')
    status = request.args.get('status')
    
    prompts = prompt_store.list_prompts(agent_id=agent_id, status=status)
    
    return jsonify({
        'prompts': [p.to_dict() for p in prompts]
    })


@prompt_bp.route('/api/prompts', methods=['POST'])
@require_api_key
def create_prompt():
    """Create a new prompt"""
    data = request.get_json()
    
    # Validate required fields
    required = ['name', 'system_prompt', 'user_prompt_template']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Parse variables
    variables = []
    for var_data in data.get('variables', []):
        variables.append(PromptVariable(
            name=var_data['name'],
            description=var_data.get('description', ''),
            default_value=var_data.get('default_value', ''),
            required=var_data.get('required', True)
        ))
    
    # Create prompt
    prompt = PromptTemplate(
        id=data.get('id') or f"prompt-{secrets.token_urlsafe(8)}",
        name=data['name'],
        description=data.get('description', ''),
        system_prompt=data['system_prompt'],
        user_prompt_template=data['user_prompt_template'],
        variables=variables,
        agent_id=request.agent.get('agent_id'),
        status=data.get('status', PromptStatus.DRAFT.value),
        created_by=data.get('created_by'),
        metadata=data.get('metadata', {})
    )
    
    try:
        created = prompt_store.create_prompt(prompt)
        return jsonify(created.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@prompt_bp.route('/api/prompts/<prompt_id>', methods=['GET'])
@require_api_key
def get_prompt(prompt_id: str):
    """Get prompt by ID"""
    prompt = prompt_store.get_prompt(prompt_id)
    if not prompt:
        return jsonify({'error': 'Prompt not found'}), 404
    
    # Check agent access
    if prompt.agent_id and prompt.agent_id != request.agent.get('agent_id'):
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(prompt.to_dict())


@prompt_bp.route('/api/prompts/<prompt_id>', methods=['PUT'])
@require_api_key
def update_prompt(prompt_id: str):
    """Update prompt"""
    prompt = prompt_store.get_prompt(prompt_id)
    if not prompt:
        return jsonify({'error': 'Prompt not found'}), 404
    
    # Check agent access
    if prompt.agent_id and prompt.agent_id != request.agent.get('agent_id'):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    updates = {}
    
    # Update allowed fields
    allowed_fields = ['name', 'description', 'system_prompt', 'user_prompt_template', 
                      'status', 'metadata']
    for field in allowed_fields:
        if field in data:
            updates[field] = data[field]
    
    # Update variables if provided
    if 'variables' in data:
        variables = [PromptVariable.from_dict(v) for v in data['variables']]
        updates['variables'] = variables
    
    updated = prompt_store.update_prompt(prompt_id, updates)
    if not updated:
        return jsonify({'error': 'Update failed'}), 500
    
    return jsonify(updated.to_dict())


@prompt_bp.route('/api/prompts/<prompt_id>', methods=['DELETE'])
@require_api_key
def delete_prompt(prompt_id: str):
    """Delete prompt"""
    prompt = prompt_store.get_prompt(prompt_id)
    if not prompt:
        return jsonify({'error': 'Prompt not found'}), 404
    
    # Check agent access
    if prompt.agent_id and prompt.agent_id != request.agent.get('agent_id'):
        return jsonify({'error': 'Access denied'}), 403
    
    success = prompt_store.delete_prompt(prompt_id)
    if not success:
        return jsonify({'error': 'Delete failed'}), 500
    
    return jsonify({'message': 'Prompt deleted'}), 200


@prompt_bp.route('/api/prompts/<prompt_id>/render', methods=['POST'])
@require_api_key
def render_prompt(prompt_id: str):
    """Render prompt with variables"""
    prompt = prompt_store.get_prompt(prompt_id)
    if not prompt:
        return jsonify({'error': 'Prompt not found'}), 404
    
    data = request.get_json()
    context = data.get('context', {})
    
    system_prompt, user_prompt = prompt.render(context)
    
    return jsonify({
        'system_prompt': system_prompt,
        'user_prompt': user_prompt
    })


@prompt_bp.route('/api/templates', methods=['GET'])
def list_templates():
    """List template library"""
    templates = prompt_store.get_templates()
    return jsonify({
        'templates': [t.to_dict() for t in templates]
    })


@prompt_bp.route('/api/templates/<template_id>', methods=['GET'])
def get_template(template_id: str):
    """Get template by ID"""
    template = prompt_store.get_template(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    return jsonify(template.to_dict())


@prompt_bp.route('/api/templates/<template_id>/clone', methods=['POST'])
@require_api_key
def clone_template(template_id: str):
    """Clone template as new prompt"""
    template = prompt_store.get_template(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    data = request.get_json()
    
    # Create new prompt from template
    prompt = PromptTemplate(
        id=f"prompt-{secrets.token_urlsafe(8)}",
        name=data.get('name', f"{template.name} (Clone)"),
        description=data.get('description', template.description),
        system_prompt=template.system_prompt,
        user_prompt_template=template.user_prompt_template,
        variables=template.variables.copy(),
        agent_id=request.agent.get('agent_id'),
        status=PromptStatus.DRAFT.value,
        metadata={**template.metadata, 'cloned_from': template_id}
    )
    
    try:
        created = prompt_store.create_prompt(prompt)
        return jsonify(created.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# A/B Testing Routes

@prompt_bp.route('/api/ab-tests', methods=['GET'])
@require_api_key
def list_ab_tests():
    """List A/B tests for agent"""
    agent_id = request.agent.get('agent_id')
    tests = prompt_store.list_ab_tests(agent_id=agent_id)
    
    return jsonify({
        'ab_tests': [t.to_dict() for t in tests]
    })


@prompt_bp.route('/api/ab-tests', methods=['POST'])
@require_api_key
def create_ab_test():
    """Create A/B test"""
    data = request.get_json()
    
    required = ['name', 'prompt_a_id', 'prompt_b_id']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate prompts exist
    prompt_a = prompt_store.get_prompt(data['prompt_a_id'])
    prompt_b = prompt_store.get_prompt(data['prompt_b_id'])
    
    if not prompt_a or not prompt_b:
        return jsonify({'error': 'One or both prompts not found'}), 404
    
    # Check agent access
    agent_id = request.agent.get('agent_id')
    if prompt_a.agent_id != agent_id or prompt_b.agent_id != agent_id:
        return jsonify({'error': 'Access denied'}), 403
    
    ab_test = ABTest(
        id=f"abtest-{secrets.token_urlsafe(8)}",
        name=data['name'],
        description=data.get('description', ''),
        prompt_a_id=data['prompt_a_id'],
        prompt_b_id=data['prompt_b_id'],
        agent_id=agent_id,
        split_ratio=data.get('split_ratio', 0.5),
        status=data.get('status', 'active')
    )
    
    try:
        created = prompt_store.create_ab_test(ab_test)
        return jsonify(created.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@prompt_bp.route('/api/ab-tests/<test_id>', methods=['GET'])
@require_api_key
def get_ab_test(test_id: str):
    """Get A/B test by ID"""
    test = prompt_store.get_ab_test(test_id)
    if not test:
        return jsonify({'error': 'A/B test not found'}), 404
    
    # Check agent access
    if test.agent_id != request.agent.get('agent_id'):
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(test.to_dict())


@prompt_bp.route('/api/ab-tests/<test_id>/select', methods=['POST'])
@require_api_key
def select_ab_test_prompt(test_id: str):
    """Select prompt for A/B test"""
    test = prompt_store.get_ab_test(test_id)
    if not test:
        return jsonify({'error': 'A/B test not found'}), 404
    
    # Check agent access
    if test.agent_id != request.agent.get('agent_id'):
        return jsonify({'error': 'Access denied'}), 403
    
    if test.status != 'active':
        return jsonify({'error': 'A/B test is not active'}), 400
    
    data = request.get_json()
    user_id = data.get('user_id')
    
    prompt_id = test.select_prompt(user_id)
    return jsonify({'prompt_id': prompt_id})


@prompt_bp.route('/api/ab-tests/<test_id>/metrics', methods=['POST'])
@require_api_key
def update_ab_test_metrics(test_id: str):
    """Update A/B test metrics"""
    test = prompt_store.get_ab_test(test_id)
    if not test:
        return jsonify({'error': 'A/B test not found'}), 404
    
    # Check agent access
    if test.agent_id != request.agent.get('agent_id'):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    prompt_id = data.get('prompt_id')
    success = data.get('success', True)
    tokens = data.get('tokens', 0)
    
    if prompt_id not in [test.prompt_a_id, test.prompt_b_id]:
        return jsonify({'error': 'Invalid prompt ID'}), 400
    
    prompt_store.update_ab_test_metrics(test_id, prompt_id, success, tokens)
    
    updated_test = prompt_store.get_ab_test(test_id)
    return jsonify(updated_test.to_dict())

