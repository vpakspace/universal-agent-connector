"""
Integration tests for legal documents API endpoints
"""

import unittest
from unittest.mock import Mock, patch
from flask import Flask
import json
from datetime import datetime

from ai_agent_connector.app.api import api_bp
from ai_agent_connector.app.utils.legal_documents import (
    legal_generator,
    LegalTemplate,
    DocumentType,
    Jurisdiction
)


class TestLegalDocumentsAPI(unittest.TestCase):
    """Test cases for legal documents API endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Clear custom templates (keep defaults)
        custom_templates = [
            tid for tid in legal_generator.templates.keys()
            if not tid.startswith(('tos-', 'privacy-')) or not tid.endswith('-v1')
        ]
        for tid in custom_templates:
            del legal_generator.templates[tid]
    
    def test_list_templates(self):
        """Test listing all templates"""
        response = self.client.get('/api/legal/templates')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('templates', data)
        self.assertGreater(len(data['templates']), 0)
    
    def test_list_templates_filter_by_type(self):
        """Test filtering templates by document type"""
        response = self.client.get('/api/legal/templates?document_type=privacy_policy')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        for template in data['templates']:
            self.assertEqual(template['document_type'], 'privacy_policy')
    
    def test_list_templates_filter_by_jurisdiction(self):
        """Test filtering templates by jurisdiction"""
        response = self.client.get('/api/legal/templates?jurisdiction=gdpr')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        for template in data['templates']:
            self.assertEqual(template['jurisdiction'], 'gdpr')
    
    def test_list_templates_filter_by_both(self):
        """Test filtering templates by both type and jurisdiction"""
        response = self.client.get('/api/legal/templates?document_type=privacy_policy&jurisdiction=gdpr')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        for template in data['templates']:
            self.assertEqual(template['document_type'], 'privacy_policy')
            self.assertEqual(template['jurisdiction'], 'gdpr')
    
    def test_get_template(self):
        """Test getting template by ID"""
        response = self.client.get('/api/legal/templates/privacy-generic-v1')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('template', data)
        self.assertEqual(data['template']['template_id'], 'privacy-generic-v1')
    
    def test_get_template_not_found(self):
        """Test getting non-existent template"""
        response = self.client.get('/api/legal/templates/non-existent')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_create_template(self):
        """Test creating custom template"""
        response = self.client.post(
            '/api/legal/templates',
            json={
                'template_id': 'test-template',
                'document_type': 'privacy_policy',
                'jurisdiction': 'generic',
                'name': 'Test Template',
                'description': 'Test description',
                'template_content': 'Template with {{variable}}',
                'required_variables': ['variable']
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['template_id'], 'test-template')
        self.assertIn('message', data)
    
    def test_create_template_missing_template_id(self):
        """Test creating template without template_id"""
        response = self.client.post(
            '/api/legal/templates',
            json={
                'document_type': 'privacy_policy',
                'jurisdiction': 'generic',
                'name': 'Test'
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_create_template_duplicate(self):
        """Test creating duplicate template"""
        # Create first template
        self.client.post(
            '/api/legal/templates',
            json={
                'template_id': 'duplicate-test',
                'document_type': 'privacy_policy',
                'jurisdiction': 'generic',
                'name': 'Test',
                'template_content': 'Content'
            }
        )
        
        # Try to create duplicate
        response = self.client.post(
            '/api/legal/templates',
            json={
                'template_id': 'duplicate-test',
                'document_type': 'privacy_policy',
                'jurisdiction': 'generic',
                'name': 'Test',
                'template_content': 'Content'
            }
        )
        
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_update_template(self):
        """Test updating template"""
        # Create template
        self.client.post(
            '/api/legal/templates',
            json={
                'template_id': 'update-test',
                'document_type': 'privacy_policy',
                'jurisdiction': 'generic',
                'name': 'Original Name',
                'template_content': 'Original content'
            }
        )
        
        # Update template
        response = self.client.put(
            '/api/legal/templates/update-test',
            json={'name': 'Updated Name'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['template']['name'], 'Updated Name')
    
    def test_update_template_not_found(self):
        """Test updating non-existent template"""
        response = self.client.put(
            '/api/legal/templates/non-existent',
            json={'name': 'Updated Name'}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_delete_template(self):
        """Test deleting template"""
        # Create template
        self.client.post(
            '/api/legal/templates',
            json={
                'template_id': 'delete-test',
                'document_type': 'privacy_policy',
                'jurisdiction': 'generic',
                'name': 'Test',
                'template_content': 'Content'
            }
        )
        
        # Delete template
        response = self.client.delete('/api/legal/templates/delete-test')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        
        # Verify deleted
        get_response = self.client.get('/api/legal/templates/delete-test')
        self.assertEqual(get_response.status_code, 404)
    
    def test_delete_template_not_found(self):
        """Test deleting non-existent template"""
        response = self.client.delete('/api/legal/templates/non-existent')
        
        self.assertEqual(response.status_code, 404)
    
    def test_delete_default_template_forbidden(self):
        """Test that default templates cannot be deleted"""
        response = self.client.delete('/api/legal/templates/privacy-generic-v1')
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('default templates', data['error'])
    
    def test_generate_document_with_template_id(self):
        """Test generating document with template ID"""
        response = self.client.post(
            '/api/legal/documents/generate',
            json={
                'document_type': 'privacy_policy',
                'jurisdiction': 'generic',
                'template_id': 'privacy-generic-v1',
                'variables': {
                    'company_name': 'Test Company',
                    'contact_email': 'contact@test.com'
                }
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('document_id', data)
        self.assertIn('content', data)
        self.assertIn('Test Company', data['content'])
        self.assertEqual(data['template_id'], 'privacy-generic-v1')
    
    def test_generate_document_without_template_id(self):
        """Test generating document without template ID (uses default)"""
        response = self.client.post(
            '/api/legal/documents/generate',
            json={
                'document_type': 'privacy_policy',
                'jurisdiction': 'generic',
                'variables': {
                    'company_name': 'Test Company',
                    'contact_email': 'contact@test.com'
                }
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('document_id', data)
        self.assertIn('content', data)
        self.assertIsNotNone(data['template_id'])
    
    def test_generate_document_with_custom_template(self):
        """Test generating document with custom template"""
        response = self.client.post(
            '/api/legal/documents/generate',
            json={
                'document_type': 'privacy_policy',
                'jurisdiction': 'generic',
                'custom_template': 'Hello {{company_name}}, contact {{contact_email}}',
                'variables': {
                    'company_name': 'Test Company',
                    'contact_email': 'contact@test.com'
                }
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('Test Company', data['content'])
        self.assertIn('contact@test.com', data['content'])
    
    def test_generate_document_missing_document_type(self):
        """Test generating document without document_type"""
        response = self.client.post(
            '/api/legal/documents/generate',
            json={
                'jurisdiction': 'generic',
                'variables': {}
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('document_type', data['error'])
    
    def test_generate_document_missing_jurisdiction(self):
        """Test generating document without jurisdiction"""
        response = self.client.post(
            '/api/legal/documents/generate',
            json={
                'document_type': 'privacy_policy',
                'variables': {}
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('jurisdiction', data['error'])
    
    def test_generate_document_missing_required_variables(self):
        """Test generating document with missing required variables"""
        response = self.client.post(
            '/api/legal/documents/generate',
            json={
                'document_type': 'privacy_policy',
                'jurisdiction': 'generic',
                'template_id': 'privacy-generic-v1',
                'variables': {
                    'company_name': 'Test Company'
                    # Missing contact_email
                }
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Missing required variables', data['error'])
    
    def test_list_jurisdictions(self):
        """Test listing supported jurisdictions"""
        response = self.client.get('/api/legal/jurisdictions')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('jurisdictions', data)
        self.assertGreater(len(data['jurisdictions']), 0)
        
        # Check that GDPR is included
        gdpr = next((j for j in data['jurisdictions'] if j['value'] == 'gdpr'), None)
        self.assertIsNotNone(gdpr)
        self.assertEqual(gdpr['name'], 'General Data Protection Regulation')
    
    def test_get_jurisdiction_requirements(self):
        """Test getting jurisdiction requirements"""
        response = self.client.get('/api/legal/jurisdictions/gdpr/requirements')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('jurisdiction', data)
        self.assertIn('requirements', data)
        self.assertEqual(data['jurisdiction'], 'gdpr')
        self.assertIn('key_requirements', data['requirements'])
        self.assertIn('required_sections', data['requirements'])
    
    def test_get_jurisdiction_requirements_unknown(self):
        """Test getting requirements for unknown jurisdiction"""
        response = self.client.get('/api/legal/jurisdictions/unknown/requirements')
        
        # Should return generic requirements
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('requirements', data)
    
    def test_validate_template(self):
        """Test template validation"""
        response = self.client.post(
            '/api/legal/templates/validate',
            json={
                'template_content': 'Hello {{name}}, welcome to {{service}}',
                'variables': {
                    'name': 'John',
                    'service': 'MyService'
                }
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['valid'])
        self.assertEqual(len(data['missing_variables']), 0)
    
    def test_validate_template_missing_variables(self):
        """Test template validation with missing variables"""
        response = self.client.post(
            '/api/legal/templates/validate',
            json={
                'template_content': 'Hello {{name}}, email: {{email}}',
                'variables': {
                    'name': 'John'
                    # Missing email
                }
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data['valid'])
        self.assertIn('email', data['missing_variables'])
    
    def test_validate_template_missing_content(self):
        """Test template validation without template_content"""
        response = self.client.post(
            '/api/legal/templates/validate',
            json={
                'variables': {'name': 'John'}
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('template_content', data['error'])


if __name__ == '__main__':
    unittest.main()

