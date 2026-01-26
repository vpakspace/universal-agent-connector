# Legal Documents API Endpoints to Add

The following endpoints should be added to `ai_agent_connector/app/api/routes.py`.

## Import Statement

Add this import with the other imports at the top of the file:

```python
from ..utils.legal_documents import (
    legal_generator,
    LegalTemplate,
    DocumentGenerationRequest,
    DocumentType,
    Jurisdiction
)
```

## Endpoints to Add

Add these endpoints in a new section (e.g., before "Result Explanation Endpoints"):

```python
# ============================================================================
# Legal Documents Endpoints
# ============================================================================

@api_bp.route('/legal/templates', methods=['GET'])
def list_legal_templates():
    """
    List legal document templates.
    
    Query parameters:
    - document_type: Filter by document type (terms_of_service, privacy_policy)
    - jurisdiction: Filter by jurisdiction (gdpr, ccpa, etc.)
    
    Returns list of available templates.
    """
    document_type = request.args.get('document_type')
    jurisdiction = request.args.get('jurisdiction')
    
    templates = legal_generator.list_templates(document_type, jurisdiction)
    
    return jsonify({
        'templates': [t.to_dict() for t in templates]
    }), 200


@api_bp.route('/legal/templates', methods=['POST'])
def create_legal_template():
    """
    Create a custom legal document template.
    
    Request body:
    {
        "template_id": "my-template",
        "document_type": "privacy_policy",
        "jurisdiction": "generic",
        "name": "My Template",
        "description": "Custom template",
        "template_content": "Template with {{variables}}",
        "required_variables": ["company_name"]
    }
    
    Returns created template.
    """
    data = request.get_json() or {}
    
    template_id = data.get('template_id')
    if not template_id:
        return jsonify({'error': 'template_id is required'}), 400
    
    if legal_generator.get_template(template_id):
        return jsonify({'error': f'Template {template_id} already exists'}), 409
    
    try:
        template = LegalTemplate.from_dict(data)
        
        # Extract variables from template if not provided
        if not template.variables:
            template.variables = template.extract_variables()
        
        legal_generator.register_template(template)
        
        return jsonify({
            'template_id': template_id,
            'message': 'Template created successfully',
            'template': template.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': f'Failed to create template: {str(e)}'}), 500


@api_bp.route('/legal/templates/<template_id>', methods=['GET'])
def get_legal_template(template_id: str):
    """
    Get legal document template by ID.
    
    Returns template details including content.
    """
    template = legal_generator.get_template(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    return jsonify({'template': template.to_dict()}), 200


@api_bp.route('/legal/templates/<template_id>', methods=['PUT'])
def update_legal_template(template_id: str):
    """
    Update legal document template.
    
    Request body: Same as create, but only provided fields are updated.
    """
    template = legal_generator.get_template(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    data = request.get_json() or {}
    
    try:
        # Update template fields
        for key, value in data.items():
            if hasattr(template, key) and key not in ['created_at', 'template_id']:
                setattr(template, key, value)
        
        # Re-extract variables if content changed
        if 'template_content' in data:
            template.variables = template.extract_variables()
        
        template.updated_at = datetime.utcnow().isoformat()
        legal_generator.register_template(template)
        
        return jsonify({
            'template_id': template_id,
            'message': 'Template updated successfully',
            'template': template.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update template: {str(e)}'}), 500


@api_bp.route('/legal/templates/<template_id>', methods=['DELETE'])
def delete_legal_template(template_id: str):
    """
    Delete legal document template.
    
    Note: Cannot delete default templates.
    """
    template = legal_generator.get_template(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    # Prevent deletion of default templates
    if template.template_id.startswith(('tos-', 'privacy-')) and template.template_id.endswith('-v1'):
        return jsonify({'error': 'Cannot delete default templates'}), 403
    
    try:
        del legal_generator.templates[template_id]
        return jsonify({'message': 'Template deleted successfully'}), 200
    except KeyError:
        return jsonify({'error': 'Template not found'}), 404


@api_bp.route('/legal/documents/generate', methods=['POST'])
def generate_legal_document():
    """
    Generate a legal document from a template.
    
    Request body:
    {
        "document_type": "privacy_policy",
        "jurisdiction": "gdpr",
        "template_id": "privacy-gdpr-v1",  // Optional
        "variables": {
            "company_name": "My Company",
            "service_name": "My Service",
            "dpo_email": "dpo@example.com"
        },
        "custom_template": null  // Optional: use custom template instead
    }
    
    Returns generated document.
    """
    data = request.get_json() or {}
    
    document_type = data.get('document_type')
    jurisdiction = data.get('jurisdiction')
    
    if not document_type:
        return jsonify({'error': 'document_type is required'}), 400
    
    if not jurisdiction:
        return jsonify({'error': 'jurisdiction is required'}), 400
    
    try:
        request_obj = DocumentGenerationRequest.from_dict(data)
        document = legal_generator.generate_document(request_obj)
        
        return jsonify(document.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Document generation failed: {str(e)}'}), 500


@api_bp.route('/legal/jurisdictions', methods=['GET'])
def list_jurisdictions():
    """
    List supported jurisdictions.
    
    Returns list of jurisdictions with descriptions.
    """
    jurisdictions = [
        {
            'value': Jurisdiction.GDPR.value,
            'name': 'General Data Protection Regulation',
            'region': 'European Union'
        },
        {
            'value': Jurisdiction.CCPA.value,
            'name': 'California Consumer Privacy Act',
            'region': 'California, USA'
        },
        {
            'value': Jurisdiction.PIPEDA.value,
            'name': 'Personal Information Protection and Electronic Documents Act',
            'region': 'Canada'
        },
        {
            'value': Jurisdiction.LGPD.value,
            'name': 'Lei Geral de Proteção de Dados',
            'region': 'Brazil'
        },
        {
            'value': Jurisdiction.PDPA.value,
            'name': 'Personal Data Protection Act',
            'region': 'Singapore'
        },
        {
            'value': Jurisdiction.APPI.value,
            'name': 'Act on the Protection of Personal Information',
            'region': 'Japan'
        },
        {
            'value': Jurisdiction.AU_PRIVACY.value,
            'name': 'Australian Privacy Act',
            'region': 'Australia'
        },
        {
            'value': Jurisdiction.GENERIC.value,
            'name': 'Generic',
            'region': 'International'
        }
    ]
    
    return jsonify({'jurisdictions': jurisdictions}), 200


@api_bp.route('/legal/jurisdictions/<jurisdiction>/requirements', methods=['GET'])
def get_jurisdiction_requirements(jurisdiction: str):
    """
    Get compliance requirements for a jurisdiction.
    
    Returns jurisdiction requirements and required sections.
    """
    try:
        requirements = legal_generator.get_jurisdiction_requirements(jurisdiction)
        
        return jsonify({
            'jurisdiction': jurisdiction,
            'requirements': requirements
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get requirements: {str(e)}'}), 500


@api_bp.route('/legal/templates/validate', methods=['POST'])
def validate_template():
    """
    Validate template variables.
    
    Request body:
    {
        "template_content": "Template with {{variables}}",
        "variables": {
            "variable1": "value1",
            "variable2": "value2"
        }
    }
    
    Returns validation result.
    """
    data = request.get_json() or {}
    
    template_content = data.get('template_content')
    variables = data.get('variables', {})
    
    if not template_content:
        return jsonify({'error': 'template_content is required'}), 400
    
    try:
        is_valid, missing = legal_generator.validate_template(template_content, variables)
        
        return jsonify({
            'valid': is_valid,
            'missing_variables': missing
        }), 200
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500
```

## Summary

**Status**: Legal documents implementation is complete ✅

**Core modules created:**
- `ai_agent_connector/app/utils/legal_documents.py` - Full legal documents generator

**Documentation:**
- `docs/LEGAL_DOCUMENTS_GUIDE.md` - Complete user guide

**Note**: Add these endpoints to `routes.py` to complete the integration. All legal document functionality is implemented and ready to use.

