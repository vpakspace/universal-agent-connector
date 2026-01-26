# Legal Documents Generator Test Cases

Comprehensive test cases for legal documents generator feature.

## Test Coverage

### Unit Tests (`test_legal_documents.py`)

#### LegalTemplate Tests

1. **Template Creation**
   - ✅ Create template
   - ✅ Extract variables from template
   - ✅ Extract variables without duplicates
   - ✅ Convert template to dictionary
   - ✅ Create template from dictionary

#### DocumentGenerationRequest Tests

1. **Request Creation**
   - ✅ Create request
   - ✅ Convert request to dictionary

#### GeneratedDocument Tests

1. **Document Creation**
   - ✅ Create generated document
   - ✅ Convert document to dictionary

#### LegalDocumentGenerator Tests

1. **Initialization**
   - ✅ Generator initializes with default templates
   - ✅ Default templates include required variables
   - ✅ Default templates extract variables correctly

2. **Template Management**
   - ✅ Register custom template
   - ✅ Get template by ID
   - ✅ Get template not found
   - ✅ List all templates
   - ✅ List templates filtered by type
   - ✅ List templates filtered by jurisdiction
   - ✅ List templates filtered by both

3. **Document Generation**
   - ✅ Generate document with template ID
   - ✅ Generate document with default template
   - ✅ Generate document with custom template
   - ✅ Generate document includes last_updated
   - ✅ Missing required variables error
   - ✅ Template type mismatch error
   - ✅ Template jurisdiction mismatch error
   - ✅ Template not found error

4. **Template Rendering**
   - ✅ Render template with variables
   - ✅ Render template with None value
   - ✅ Render template with non-string value

5. **Template Validation**
   - ✅ Validate template with all variables
   - ✅ Validate template with missing variables

6. **Jurisdiction Requirements**
   - ✅ Get GDPR requirements
   - ✅ Get generic requirements
   - ✅ Get unknown jurisdiction (returns generic)

### Integration Tests (`test_legal_documents_api.py`)

#### API Endpoint Tests

1. **Template Management**
   - ✅ List templates
   - ✅ List templates filtered by type
   - ✅ List templates filtered by jurisdiction
   - ✅ List templates filtered by both
   - ✅ Get template by ID
   - ✅ Get template not found
   - ✅ Create template
   - ✅ Create template missing template_id
   - ✅ Create duplicate template
   - ✅ Update template
   - ✅ Update template not found
   - ✅ Delete template
   - ✅ Delete template not found
   - ✅ Delete default template forbidden

2. **Document Generation**
   - ✅ Generate document with template ID
   - ✅ Generate document without template ID
   - ✅ Generate document with custom template
   - ✅ Generate document missing document_type
   - ✅ Generate document missing jurisdiction
   - ✅ Generate document missing required variables

3. **Jurisdiction Support**
   - ✅ List jurisdictions
   - ✅ Get jurisdiction requirements
   - ✅ Get unknown jurisdiction requirements

4. **Template Validation**
   - ✅ Validate template
   - ✅ Validate template with missing variables
   - ✅ Validate template missing content

## Test Scenarios

### Scenario 1: Generate GDPR Privacy Policy

**Setup:**
- Use default GDPR privacy policy template
- Provide required variables

**Steps:**
1. Generate document with GDPR template
2. Verify document contains GDPR-specific content
3. Check all variables are substituted
4. Verify required sections are present

**Expected:**
- Document generated successfully
- Contains GDPR-specific sections
- All variables replaced
- Includes data subject rights

### Scenario 2: Create Custom Template

**Setup:**
- Create custom template with variables

**Steps:**
1. Create custom template
2. Verify template is stored
3. Generate document using custom template
4. Check variables are substituted

**Expected:**
- Template created successfully
- Template can be retrieved
- Document generated correctly
- Variables replaced

### Scenario 3: Multi-Jurisdiction Support

**Setup:**
- Templates for different jurisdictions

**Steps:**
1. Generate GDPR privacy policy
2. Generate CCPA privacy policy
3. Generate generic privacy policy
4. Compare jurisdictions

**Expected:**
- Each jurisdiction has appropriate template
- Documents contain jurisdiction-specific content
- Requirements are documented

### Scenario 4: Template Validation

**Setup:**
- Template with variables
- Set of variables

**Steps:**
1. Validate template with all variables
2. Validate template with missing variables
3. Check validation results

**Expected:**
- Validation succeeds with all variables
- Validation fails with missing variables
- Missing variables are identified

### Scenario 5: Required Variables Enforcement

**Setup:**
- Template with required variables

**Steps:**
1. Generate document with all required variables
2. Try to generate with missing required variable
3. Verify error message

**Expected:**
- Generation succeeds with all variables
- Generation fails with missing variables
- Error message identifies missing variables

## Test Data

### Sample Templates

**Generic Privacy Policy:**
```json
{
  "template_id": "privacy-generic-v1",
  "document_type": "privacy_policy",
  "jurisdiction": "generic",
  "required_variables": ["company_name", "contact_email"]
}
```

**GDPR Privacy Policy:**
```json
{
  "template_id": "privacy-gdpr-v1",
  "document_type": "privacy_policy",
  "jurisdiction": "gdpr",
  "required_variables": ["company_name", "dpo_email", "service_name"]
}
```

### Sample Variables

**Generic:**
```json
{
  "company_name": "My Company Inc.",
  "contact_email": "privacy@example.com",
  "service_name": "My Service"
}
```

**GDPR:**
```json
{
  "company_name": "My Company Ltd.",
  "service_name": "My SaaS Platform",
  "dpo_email": "dpo@mycompany.com",
  "company_address": "123 Business St, London, UK",
  "eu_representative": "EU Rep Ltd., Brussels, Belgium"
}
```

## Edge Cases

1. **Missing Required Variables**
   - Generation fails
   - Error message identifies missing variables

2. **Template Not Found**
   - Error returned
   - Uses default template if available

3. **Type/Jurisdiction Mismatch**
   - Error returned
   - Clear error message

4. **Invalid Template Content**
   - Validation catches issues
   - Variable extraction works correctly

5. **Empty Variables**
   - Template renders with empty strings
   - None values handled

6. **Non-String Variables**
   - Variables converted to strings
   - Numbers, booleans work correctly

## Security Tests

1. **Template Injection**
   - Variables are escaped/rendered safely
   - No code execution from templates

2. **XSS Prevention**
   - Generated content is safe
   - Variables are properly handled

## Performance Tests

1. **Template Rendering**
   - Large templates render quickly
   - Many variables handled efficiently

2. **Template List**
   - Listing many templates is fast
   - Filtering is efficient

## Running Tests

### Unit Tests

```bash
python -m pytest tests/test_legal_documents.py -v
```

### Integration Tests

```bash
python -m pytest tests/test_legal_documents_api.py -v
```

### All Tests

```bash
python -m pytest tests/test_legal_documents.py tests/test_legal_documents_api.py -v
```

### With Coverage

```bash
python -m pytest tests/test_legal_documents.py tests/test_legal_documents_api.py \
    --cov=ai_agent_connector.app.utils.legal_documents \
    --cov-report=html \
    --cov-report=term
```

## Test Metrics

### Coverage Goals

- **Unit Tests**: >90% coverage
- **Integration Tests**: >80% coverage
- **Critical Paths**: 100% coverage

### Test Categories

- **Unit Tests**: 30+ test cases
- **Integration Tests**: 20+ test cases
- **Edge Cases**: 8+ test cases
- **Security Tests**: 2+ test cases

## Continuous Integration

Tests should run:
- On every commit
- Before merging PRs
- On scheduled basis (nightly)

## Test Maintenance

### When to Update Tests

1. New document types added
2. New jurisdictions added
3. Template system changes
4. API changes
5. Bug fixes

### Test Documentation

- Keep test cases documented
- Update when features change
- Document test data requirements
- Document test environment setup

