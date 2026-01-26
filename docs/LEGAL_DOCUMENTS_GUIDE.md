# Legal Documents Generator Guide

Complete guide for generating Terms of Service and Privacy Policy documents with customizable templates and multi-jurisdiction compliance.

## 🎯 Overview

The Legal Documents Generator helps you create compliant legal documents:

- **Terms of Service**: Customizable terms with jurisdiction-specific requirements
- **Privacy Policy**: Privacy policies compliant with GDPR, CCPA, PIPEDA, and more
- **Multi-Jurisdiction Support**: Templates for various jurisdictions
- **Customizable Templates**: Create and use custom templates
- **Variable Substitution**: Fill templates with your organization's information

## 🚀 Quick Start

### Generate a Privacy Policy

```bash
POST /api/legal/documents/generate
Body: {
  "document_type": "privacy_policy",
  "jurisdiction": "gdpr",
  "variables": {
    "company_name": "My Company Inc.",
    "service_name": "My Service",
    "contact_email": "privacy@example.com",
    "dpo_email": "dpo@example.com",
    "company_address": "123 Main St, City, Country"
  }
}
```

### Generate Terms of Service

```bash
POST /api/legal/documents/generate
Body: {
  "document_type": "terms_of_service",
  "jurisdiction": "generic",
  "variables": {
    "service_name": "My Service",
    "company_name": "My Company Inc.",
    "contact_email": "support@example.com",
    "service_description": "cloud-based software solution"
  }
}
```

## 📚 Supported Jurisdictions

### GDPR (European Union)

**Key Requirements:**
- Data controller identification
- Legal basis for processing
- Data subject rights (access, rectification, erasure, etc.)
- Data Protection Officer (DPO) contact
- Data retention policies
- Cross-border transfer safeguards

**Use Case:** Services available to EU residents

### CCPA (California, USA)

**Key Requirements:**
- Notice at collection
- Information categories disclosure
- Consumer rights (know, delete, opt-out)
- Do Not Sell link
- Non-discrimination policy

**Use Case:** Services available to California residents

### PIPEDA (Canada)

**Key Requirements:**
- Consent for collection
- Purpose limitation
- Individual access rights
- Security safeguards
- Openness about practices

**Use Case:** Services available to Canadian residents

### Other Jurisdictions

- **LGPD** (Brazil)
- **PDPA** (Singapore)
- **APPI** (Japan)
- **AU Privacy Act** (Australia)
- **Generic** (International/Default)

## 📝 Document Types

### Terms of Service

**Purpose:** Define terms and conditions for using your service

**Common Sections:**
- Acceptance of terms
- Service description
- User accounts and conduct
- Intellectual property
- Limitation of liability
- Termination
- Changes to terms
- Contact information

### Privacy Policy

**Purpose:** Explain how you collect, use, and protect personal information

**Common Sections:**
- Information collection
- Information use
- Information sharing
- Data security
- User rights
- Cookies and tracking
- Children's privacy
- Contact information

## 🔧 Using Templates

### Default Templates

The system includes default templates for:
- Generic Terms of Service
- GDPR-compliant Terms of Service
- Generic Privacy Policy
- GDPR-compliant Privacy Policy
- CCPA-compliant Privacy Policy

### Custom Templates

Create your own templates:

```bash
POST /api/legal/templates
Body: {
  "template_id": "my-custom-tos",
  "document_type": "terms_of_service",
  "jurisdiction": "generic",
  "name": "My Custom Terms",
  "description": "Custom terms template",
  "template_content": "Your custom template with {{variables}}",
  "required_variables": ["company_name", "service_name"]
}
```

### Template Variables

Templates use `{{variable_name}}` syntax for variable substitution.

**Common Variables:**
- `{{company_name}}` - Your company name
- `{{service_name}}` - Your service name
- `{{contact_email}}` - Contact email
- `{{company_address}}` - Company address
- `{{last_updated}}` - Auto-filled with current date

**GDPR-Specific Variables:**
- `{{dpo_email}}` - Data Protection Officer email
- `{{eu_representative}}` - EU representative information

**CCPA-Specific Variables:**
- `{{contact_phone}}` - Contact phone number
- `{{privacy_request_url}}` - URL for privacy requests
- `{{sell_personal_information_policy}}` - Policy on selling data

## 📡 API Reference

### List Templates

```
GET /api/legal/templates?document_type=privacy_policy&jurisdiction=gdpr
```

**Query Parameters:**
- `document_type` (optional): Filter by document type
- `jurisdiction` (optional): Filter by jurisdiction

**Response:**
```json
{
  "templates": [
    {
      "template_id": "privacy-gdpr-v1",
      "document_type": "privacy_policy",
      "jurisdiction": "gdpr",
      "name": "GDPR-Compliant Privacy Policy",
      "variables": ["company_name", "dpo_email", ...],
      "required_variables": ["company_name", "dpo_email"]
    }
  ]
}
```

### Get Template

```
GET /api/legal/templates/{template_id}
```

**Response:**
```json
{
  "template": {
    "template_id": "privacy-gdpr-v1",
    "document_type": "privacy_policy",
    "jurisdiction": "gdpr",
    "name": "GDPR-Compliant Privacy Policy",
    "template_content": "...",
    "variables": [...],
    "required_variables": [...]
  }
}
```

### Create Template

```
POST /api/legal/templates
```

**Request Body:**
```json
{
  "template_id": "my-template",
  "document_type": "privacy_policy",
  "jurisdiction": "generic",
  "name": "My Template",
  "description": "Custom template",
  "template_content": "Template content with {{variables}}",
  "required_variables": ["company_name"]
}
```

### Update Template

```
PUT /api/legal/templates/{template_id}
```

**Request Body:** Same as create, but only provided fields are updated

### Delete Template

```
DELETE /api/legal/templates/{template_id}
```

### Generate Document

```
POST /api/legal/documents/generate
```

**Request Body:**
```json
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
```

**Response:**
```json
{
  "document_id": "doc-123",
  "document_type": "privacy_policy",
  "jurisdiction": "gdpr",
  "template_id": "privacy-gdpr-v1",
  "content": "PRIVACY POLICY (GDPR Compliant)...",
  "variables_used": {...},
  "generated_at": "2024-01-15T10:00:00Z",
  "version": "1.0"
}
```

### Get Jurisdiction Requirements

```
GET /api/legal/jurisdictions/{jurisdiction}/requirements
```

**Response:**
```json
{
  "jurisdiction": "gdpr",
  "requirements": {
    "name": "General Data Protection Regulation",
    "region": "European Union",
    "key_requirements": [...],
    "required_sections": [...]
  }
}
```

### List Jurisdictions

```
GET /api/legal/jurisdictions
```

**Response:**
```json
{
  "jurisdictions": [
    {
      "value": "gdpr",
      "name": "General Data Protection Regulation",
      "region": "European Union"
    },
    {
      "value": "ccpa",
      "name": "California Consumer Privacy Act",
      "region": "California, USA"
    }
  ]
}
```

## 🔍 Examples

### Example 1: GDPR Privacy Policy

```python
import requests

response = requests.post(
    'http://localhost:5000/api/legal/documents/generate',
    json={
        'document_type': 'privacy_policy',
        'jurisdiction': 'gdpr',
        'variables': {
            'company_name': 'My Company Ltd.',
            'service_name': 'My SaaS Platform',
            'company_address': '123 Business St, London, UK',
            'dpo_email': 'dpo@mycompany.com',
            'eu_representative': 'EU Rep Ltd., Brussels, Belgium',
            'personal_data_collected': 'Name, email, IP address, usage data',
            'processing_purposes': 'Service delivery, customer support, analytics'
        }
    }
)

document = response.json()
print(document['content'])
```

### Example 2: CCPA Privacy Policy

```python
response = requests.post(
    'http://localhost:5000/api/legal/documents/generate',
    json={
        'document_type': 'privacy_policy',
        'jurisdiction': 'ccpa',
        'variables': {
            'company_name': 'My Company Inc.',
            'contact_email': 'privacy@mycompany.com',
            'contact_phone': '1-800-123-4567',
            'privacy_request_url': 'https://mycompany.com/privacy-request',
            'ccpa_categories_collected': 'Identifiers, commercial information, internet activity',
            'business_purposes': 'Service delivery, marketing, analytics',
            'sell_personal_information_policy': 'do not'  # or 'may'
        }
    }
)

document = response.json()
print(document['content'])
```

### Example 3: Custom Template

```python
# Create custom template
template_response = requests.post(
    'http://localhost:5000/api/legal/templates',
    json={
        'template_id': 'my-custom-tos',
        'document_type': 'terms_of_service',
        'jurisdiction': 'generic',
        'name': 'My Custom Terms',
        'template_content': '''
TERMS OF SERVICE

{{service_name}} Terms of Service

1. ACCEPTANCE
By using {{service_name}}, you agree to these terms.

2. SERVICE
{{service_description}}

Contact: {{contact_email}}
        ''',
        'required_variables': ['service_name', 'contact_email']
    }
)

# Use custom template
doc_response = requests.post(
    'http://localhost:5000/api/legal/documents/generate',
    json={
        'document_type': 'terms_of_service',
        'jurisdiction': 'generic',
        'template_id': 'my-custom-tos',
        'variables': {
            'service_name': 'My Service',
            'service_description': 'A cloud-based platform',
            'contact_email': 'support@example.com'
        }
    }
)
```

## 🎨 Best Practices

### Template Design

1. **Clear Structure**: Use numbered sections and clear headings
2. **Plain Language**: Write in clear, understandable language
3. **Complete Coverage**: Include all required sections for jurisdiction
4. **Variable Names**: Use descriptive variable names
5. **Required Variables**: Mark critical variables as required

### Document Generation

1. **Required Variables**: Always provide required variables
2. **Review Generated Content**: Always review generated documents
3. **Legal Review**: Have documents reviewed by legal counsel
4. **Keep Updated**: Update documents when laws change
5. **Version Control**: Track document versions

### Compliance

1. **Know Your Jurisdiction**: Use appropriate jurisdiction templates
2. **Multiple Jurisdictions**: Generate separate documents for different jurisdictions
3. **Regular Updates**: Review and update documents regularly
4. **Legal Consultation**: Consult legal professionals for complex cases
5. **Documentation**: Keep records of generated documents

## 🐛 Troubleshooting

### Missing Required Variables

**Issue**: Error about missing required variables
**Solution**: Check template requirements and provide all required variables

### Template Not Found

**Issue**: Template ID not found
**Solution**: Verify template ID exists, or use default template by omitting template_id

### Jurisdiction Mismatch

**Issue**: Template jurisdiction doesn't match request
**Solution**: Use a template matching the requested jurisdiction

### Invalid Template

**Issue**: Template validation fails
**Solution**: Check template syntax, ensure variables use {{variable}} format

## 📈 Production Considerations

### Legal Disclaimer

**Important**: Generated documents are templates and should be reviewed by legal professionals. The generator provides starting points but does not constitute legal advice.

### Template Maintenance

- Keep templates updated with legal changes
- Review templates regularly
- Update required variables as needed
- Archive old template versions

### Document Storage

- Store generated documents securely
- Track document versions
- Maintain audit trail
- Link documents to user agreements

---

**Questions?** Check [GitHub Discussions](https://github.com/your-repo/ai-agent-connector/discussions) or open an issue!

**Legal Notice**: This tool generates template documents and is not a substitute for legal advice. Always consult qualified legal professionals.

