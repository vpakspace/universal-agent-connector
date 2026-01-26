"""
Unit tests for legal documents generator
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime

from ai_agent_connector.app.utils.legal_documents import (
    LegalTemplate,
    DocumentGenerationRequest,
    GeneratedDocument,
    DocumentType,
    Jurisdiction,
    LegalDocumentGenerator
)


class TestLegalTemplate(unittest.TestCase):
    """Test cases for LegalTemplate"""
    
    def test_create_template(self):
        """Test creating a legal template"""
        template = LegalTemplate(
            template_id="test-template",
            document_type="privacy_policy",
            jurisdiction="gdpr",
            name="Test Template",
            description="Test description",
            template_content="Template with {{variable}}",
            required_variables=["variable"]
        )
        
        self.assertEqual(template.template_id, "test-template")
        self.assertEqual(template.document_type, "privacy_policy")
        self.assertEqual(template.jurisdiction, "gdpr")
        self.assertEqual(template.name, "Test Template")
    
    def test_extract_variables(self):
        """Test extracting variables from template"""
        template = LegalTemplate(
            template_id="test",
            document_type="privacy_policy",
            jurisdiction="generic",
            name="Test",
            template_content="Hello {{name}}, welcome to {{service}}"
        )
        
        variables = template.extract_variables()
        self.assertIn("name", variables)
        self.assertIn("service", variables)
        self.assertEqual(len(variables), 2)
    
    def test_extract_variables_no_duplicates(self):
        """Test that duplicate variables are not included"""
        template = LegalTemplate(
            template_id="test",
            document_type="privacy_policy",
            jurisdiction="generic",
            name="Test",
            template_content="{{name}} {{name}} {{service}}"
        )
        
        variables = template.extract_variables()
        self.assertEqual(len(variables), 2)  # name and service, no duplicates
    
    def test_template_to_dict(self):
        """Test converting template to dictionary"""
        template = LegalTemplate(
            template_id="test",
            document_type="privacy_policy",
            jurisdiction="generic",
            name="Test",
            template_content="Content"
        )
        
        template_dict = template.to_dict()
        self.assertIn("template_id", template_dict)
        self.assertIn("document_type", template_dict)
        self.assertEqual(template_dict["name"], "Test")
    
    def test_template_from_dict(self):
        """Test creating template from dictionary"""
        data = {
            "template_id": "test",
            "document_type": "privacy_policy",
            "jurisdiction": "generic",
            "name": "Test",
            "description": "Description",
            "template_content": "Content",
            "variables": [],
            "required_variables": []
        }
        
        template = LegalTemplate.from_dict(data)
        self.assertEqual(template.template_id, "test")
        self.assertEqual(template.name, "Test")


class TestDocumentGenerationRequest(unittest.TestCase):
    """Test cases for DocumentGenerationRequest"""
    
    def test_create_request(self):
        """Test creating document generation request"""
        request = DocumentGenerationRequest(
            document_type="privacy_policy",
            jurisdiction="gdpr",
            template_id="template-1",
            variables={"company_name": "Test Co"}
        )
        
        self.assertEqual(request.document_type, "privacy_policy")
        self.assertEqual(request.jurisdiction, "gdpr")
        self.assertEqual(request.template_id, "template-1")
        self.assertEqual(request.variables["company_name"], "Test Co")
    
    def test_request_to_dict(self):
        """Test converting request to dictionary"""
        request = DocumentGenerationRequest(
            document_type="privacy_policy",
            jurisdiction="gdpr",
            variables={"company_name": "Test Co"}
        )
        
        request_dict = request.to_dict()
        self.assertIn("document_type", request_dict)
        self.assertIn("jurisdiction", request_dict)
        self.assertIn("variables", request_dict)


class TestGeneratedDocument(unittest.TestCase):
    """Test cases for GeneratedDocument"""
    
    def test_create_generated_document(self):
        """Test creating generated document"""
        document = GeneratedDocument(
            document_id="doc-123",
            document_type="privacy_policy",
            jurisdiction="gdpr",
            template_id="template-1",
            content="Generated content",
            variables_used={"company_name": "Test Co"},
            generated_at=datetime.utcnow().isoformat()
        )
        
        self.assertEqual(document.document_id, "doc-123")
        self.assertEqual(document.document_type, "privacy_policy")
        self.assertEqual(document.content, "Generated content")
    
    def test_document_to_dict(self):
        """Test converting document to dictionary"""
        document = GeneratedDocument(
            document_id="doc-123",
            document_type="privacy_policy",
            jurisdiction="gdpr",
            content="Content",
            variables_used={},
            generated_at=datetime.utcnow().isoformat()
        )
        
        document_dict = document.to_dict()
        self.assertIn("document_id", document_dict)
        self.assertIn("content", document_dict)


class TestLegalDocumentGenerator(unittest.TestCase):
    """Test cases for LegalDocumentGenerator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = LegalDocumentGenerator()
    
    def test_generator_initialization(self):
        """Test generator initializes with default templates"""
        self.assertGreater(len(self.generator.templates), 0)
        self.assertIn("tos-generic-v1", self.generator.templates)
        self.assertIn("privacy-generic-v1", self.generator.templates)
    
    def test_register_template(self):
        """Test registering a custom template"""
        template = LegalTemplate(
            template_id="custom-template",
            document_type="privacy_policy",
            jurisdiction="generic",
            name="Custom Template",
            template_content="Custom content"
        )
        
        self.generator.register_template(template)
        
        retrieved = self.generator.get_template("custom-template")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Custom Template")
    
    def test_get_template(self):
        """Test getting template by ID"""
        template = self.generator.get_template("tos-generic-v1")
        self.assertIsNotNone(template)
        self.assertEqual(template.template_id, "tos-generic-v1")
    
    def test_get_template_not_found(self):
        """Test getting non-existent template"""
        template = self.generator.get_template("non-existent")
        self.assertIsNone(template)
    
    def test_list_templates(self):
        """Test listing all templates"""
        templates = self.generator.list_templates()
        self.assertGreater(len(templates), 0)
    
    def test_list_templates_filter_by_type(self):
        """Test filtering templates by document type"""
        privacy_templates = self.generator.list_templates(document_type="privacy_policy")
        
        for template in privacy_templates:
            self.assertEqual(template.document_type, "privacy_policy")
    
    def test_list_templates_filter_by_jurisdiction(self):
        """Test filtering templates by jurisdiction"""
        gdpr_templates = self.generator.list_templates(jurisdiction="gdpr")
        
        for template in gdpr_templates:
            self.assertEqual(template.jurisdiction, "gdpr")
    
    def test_list_templates_filter_by_both(self):
        """Test filtering templates by both type and jurisdiction"""
        templates = self.generator.list_templates(
            document_type="privacy_policy",
            jurisdiction="gdpr"
        )
        
        for template in templates:
            self.assertEqual(template.document_type, "privacy_policy")
            self.assertEqual(template.jurisdiction, "gdpr")
    
    def test_generate_document_with_template_id(self):
        """Test generating document with specific template ID"""
        request = DocumentGenerationRequest(
            document_type="privacy_policy",
            jurisdiction="generic",
            template_id="privacy-generic-v1",
            variables={
                "company_name": "Test Company",
                "contact_email": "contact@test.com"
            }
        )
        
        document = self.generator.generate_document(request)
        
        self.assertIsNotNone(document)
        self.assertEqual(document.document_type, "privacy_policy")
        self.assertEqual(document.jurisdiction, "generic")
        self.assertIn("Test Company", document.content)
        self.assertIn("contact@test.com", document.content)
    
    def test_generate_document_with_default_template(self):
        """Test generating document using default template"""
        request = DocumentGenerationRequest(
            document_type="privacy_policy",
            jurisdiction="generic",
            variables={
                "company_name": "Test Company",
                "contact_email": "contact@test.com"
            }
        )
        
        document = self.generator.generate_document(request)
        
        self.assertIsNotNone(document)
        self.assertIsNotNone(document.template_id)
        self.assertIn("Test Company", document.content)
    
    def test_generate_document_with_custom_template(self):
        """Test generating document with custom template"""
        request = DocumentGenerationRequest(
            document_type="privacy_policy",
            jurisdiction="generic",
            custom_template="Hello {{company_name}}, contact us at {{contact_email}}",
            variables={
                "company_name": "Test Company",
                "contact_email": "contact@test.com"
            }
        )
        
        document = self.generator.generate_document(request)
        
        self.assertIsNotNone(document)
        self.assertIn("Test Company", document.content)
        self.assertIn("contact@test.com", document.content)
        self.assertIsNone(document.template_id)
    
    def test_generate_document_missing_required_variables(self):
        """Test generating document with missing required variables"""
        request = DocumentGenerationRequest(
            document_type="privacy_policy",
            jurisdiction="generic",
            template_id="privacy-generic-v1",
            variables={
                "company_name": "Test Company"
                # Missing contact_email
            }
        )
        
        with self.assertRaises(ValueError) as context:
            self.generator.generate_document(request)
        
        self.assertIn("Missing required variables", str(context.exception))
    
    def test_generate_document_template_type_mismatch(self):
        """Test generating document with template type mismatch"""
        request = DocumentGenerationRequest(
            document_type="terms_of_service",
            jurisdiction="generic",
            template_id="privacy-generic-v1",  # Wrong type
            variables={"company_name": "Test"}
        )
        
        with self.assertRaises(ValueError) as context:
            self.generator.generate_document(request)
        
        self.assertIn("Template type mismatch", str(context.exception))
    
    def test_generate_document_template_jurisdiction_mismatch(self):
        """Test generating document with template jurisdiction mismatch"""
        request = DocumentGenerationRequest(
            document_type="privacy_policy",
            jurisdiction="ccpa",
            template_id="privacy-generic-v1",  # Wrong jurisdiction
            variables={"company_name": "Test"}
        )
        
        with self.assertRaises(ValueError) as context:
            self.generator.generate_document(request)
        
        self.assertIn("Template jurisdiction mismatch", str(context.exception))
    
    def test_generate_document_template_not_found(self):
        """Test generating document with non-existent template"""
        request = DocumentGenerationRequest(
            document_type="privacy_policy",
            jurisdiction="generic",
            template_id="non-existent",
            variables={"company_name": "Test"}
        )
        
        with self.assertRaises(ValueError) as context:
            self.generator.generate_document(request)
        
        self.assertIn("not found", str(context.exception))
    
    def test_render_template(self):
        """Test template rendering"""
        template = "Hello {{name}}, welcome to {{service}}"
        variables = {
            "name": "John",
            "service": "MyService"
        }
        
        content = self.generator._render_template(template, variables)
        
        self.assertEqual(content, "Hello John, welcome to MyService")
        self.assertNotIn("{{", content)
        self.assertNotIn("}}", content)
    
    def test_render_template_with_none_value(self):
        """Test template rendering with None value"""
        template = "Hello {{name}}"
        variables = {"name": None}
        
        content = self.generator._render_template(template, variables)
        
        self.assertEqual(content, "Hello ")
    
    def test_render_template_with_non_string_value(self):
        """Test template rendering with non-string value"""
        template = "Count: {{count}}"
        variables = {"count": 42}
        
        content = self.generator._render_template(template, variables)
        
        self.assertEqual(content, "Count: 42")
    
    def test_validate_template(self):
        """Test template validation"""
        template_content = "Hello {{name}}, welcome to {{service}}"
        variables = {
            "name": "John",
            "service": "MyService"
        }
        
        is_valid, missing = self.generator.validate_template(template_content, variables)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)
    
    def test_validate_template_missing_variables(self):
        """Test template validation with missing variables"""
        template_content = "Hello {{name}}, welcome to {{service}}, email: {{email}}"
        variables = {
            "name": "John",
            "service": "MyService"
            # Missing email
        }
        
        is_valid, missing = self.generator.validate_template(template_content, variables)
        
        self.assertFalse(is_valid)
        self.assertIn("email", missing)
    
    def test_get_jurisdiction_requirements(self):
        """Test getting jurisdiction requirements"""
        requirements = self.generator.get_jurisdiction_requirements("gdpr")
        
        self.assertIsNotNone(requirements)
        self.assertIn("name", requirements)
        self.assertIn("key_requirements", requirements)
        self.assertIn("required_sections", requirements)
        self.assertEqual(requirements["name"], "General Data Protection Regulation")
    
    def test_get_jurisdiction_requirements_generic(self):
        """Test getting generic jurisdiction requirements"""
        requirements = self.generator.get_jurisdiction_requirements("generic")
        
        self.assertIsNotNone(requirements)
        self.assertIn("name", requirements)
    
    def test_get_jurisdiction_requirements_unknown(self):
        """Test getting requirements for unknown jurisdiction"""
        requirements = self.generator.get_jurisdiction_requirements("unknown")
        
        # Should return generic requirements
        self.assertIsNotNone(requirements)
        self.assertEqual(requirements["name"], "Generic")
    
    def test_default_templates_have_required_variables(self):
        """Test that default templates have required variables defined"""
        for template_id, template in self.generator.templates.items():
            self.assertIsNotNone(template.required_variables)
            self.assertIsInstance(template.required_variables, list)
            
            # Check that required variables are in template variables
            for req_var in template.required_variables:
                self.assertIn(req_var, template.variables)
    
    def test_default_templates_extract_variables(self):
        """Test that default templates extract variables correctly"""
        for template_id, template in self.generator.templates.items():
            extracted = template.extract_variables()
            self.assertEqual(set(template.variables), set(extracted))
    
    def test_generate_document_includes_last_updated(self):
        """Test that generated documents include last_updated variable"""
        request = DocumentGenerationRequest(
            document_type="privacy_policy",
            jurisdiction="generic",
            variables={
                "company_name": "Test Company",
                "contact_email": "contact@test.com"
            }
        )
        
        document = self.generator.generate_document(request)
        
        # Check that last_updated was added
        self.assertIn("last_updated", document.variables_used)
        self.assertIsNotNone(document.variables_used["last_updated"])


if __name__ == '__main__':
    unittest.main()

