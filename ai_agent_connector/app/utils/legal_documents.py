"""
Legal Document Generator
Supports Terms of Service and Privacy Policy generation with customizable templates
and multi-jurisdiction compliance (GDPR, CCPA, etc.)
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import re


class Jurisdiction(Enum):
    """Supported jurisdictions"""
    GDPR = "gdpr"  # European Union
    CCPA = "ccpa"  # California, USA
    PIPEDA = "pipeda"  # Canada
    LGPD = "lgpd"  # Brazil
    PDPA = "pdpa"  # Singapore
    APPI = "appi"  # Japan
    AU_PRIVACY = "au_privacy"  # Australia
    GENERIC = "generic"  # Generic/default


class DocumentType(Enum):
    """Legal document types"""
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"


@dataclass
class LegalTemplate:
    """Legal document template"""
    template_id: str
    document_type: str
    jurisdiction: str
    name: str
    description: str
    template_content: str
    variables: List[str] = field(default_factory=list)
    required_variables: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LegalTemplate':
        """Create from dictionary"""
        return cls(**data)
    
    def extract_variables(self) -> List[str]:
        """Extract variables from template content"""
        # Look for {{variable}} patterns
        pattern = r'\{\{(\w+)\}\}'
        variables = re.findall(pattern, self.template_content)
        return list(set(variables))  # Remove duplicates


@dataclass
class DocumentGenerationRequest:
    """Request for document generation"""
    document_type: str
    jurisdiction: str
    template_id: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    custom_template: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class GeneratedDocument:
    """Generated legal document"""
    document_id: str
    document_type: str
    jurisdiction: str
    template_id: Optional[str]
    content: str
    variables_used: Dict[str, Any]
    generated_at: str
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class LegalDocumentGenerator:
    """Generator for legal documents"""
    
    def __init__(self):
        """Initialize legal document generator"""
        self.templates: Dict[str, LegalTemplate] = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default templates"""
        # Default Terms of Service templates
        self._add_default_terms_templates()
        
        # Default Privacy Policy templates
        self._add_default_privacy_templates()
    
    def _add_default_terms_templates(self):
        """Add default Terms of Service templates"""
        # Generic Terms of Service
        generic_tos = LegalTemplate(
            template_id="tos-generic-v1",
            document_type=DocumentType.TERMS_OF_SERVICE.value,
            jurisdiction=Jurisdiction.GENERIC.value,
            name="Generic Terms of Service",
            description="Generic terms of service template",
            template_content="""TERMS OF SERVICE

Last Updated: {{last_updated}}

1. ACCEPTANCE OF TERMS
By accessing and using {{service_name}} (the "Service"), you accept and agree to be bound by these Terms of Service.

2. DESCRIPTION OF SERVICE
{{service_name}} provides {{service_description}}.

3. USER ACCOUNTS
{{account_requirements}}

4. USER CONDUCT
Users agree not to use the Service for any unlawful purpose or in any way that could damage, disable, or impair the Service.

5. INTELLECTUAL PROPERTY
All content on {{service_name}} is the property of {{company_name}} and is protected by copyright laws.

6. LIMITATION OF LIABILITY
{{company_name}} shall not be liable for any indirect, incidental, special, or consequential damages.

7. TERMINATION
{{company_name}} reserves the right to terminate access to the Service at any time, without notice.

8. CHANGES TO TERMS
{{company_name}} reserves the right to modify these terms at any time.

9. CONTACT INFORMATION
For questions about these Terms, please contact us at {{contact_email}}.

{{company_name}}
{{company_address}}"""
        )
        generic_tos.variables = generic_tos.extract_variables()
        generic_tos.required_variables = ['service_name', 'company_name', 'contact_email']
        self.templates[generic_tos.template_id] = generic_tos
        
        # GDPR-compliant Terms of Service
        gdpr_tos = LegalTemplate(
            template_id="tos-gdpr-v1",
            document_type=DocumentType.TERMS_OF_SERVICE.value,
            jurisdiction=Jurisdiction.GDPR.value,
            name="GDPR-Compliant Terms of Service",
            description="Terms of service template compliant with GDPR",
            template_content="""TERMS OF SERVICE (GDPR Compliant)

Last Updated: {{last_updated}}

1. ACCEPTANCE OF TERMS
By accessing and using {{service_name}} (the "Service"), you accept and agree to be bound by these Terms of Service, in compliance with the General Data Protection Regulation (GDPR).

2. DATA PROTECTION
{{service_name}} processes personal data in accordance with GDPR. For details, please see our Privacy Policy.

3. YOUR RIGHTS UNDER GDPR
You have the right to:
- Access your personal data
- Rectify inaccurate data
- Erase your data (right to be forgotten)
- Restrict processing
- Data portability
- Object to processing

4. DATA PROCESSING
{{data_processing_description}}

5. THIRD-PARTY SERVICES
We may use third-party services that comply with GDPR requirements.

6. CROSS-BORDER DATA TRANSFERS
Data transfers outside the EU are subject to appropriate safeguards as required by GDPR.

7. CONTACT INFORMATION
For data protection inquiries, contact our Data Protection Officer at {{dpo_email}}.

{{company_name}}
{{company_address}}
EU Representative: {{eu_representative}}"""
        )
        gdpr_tos.variables = gdpr_tos.extract_variables()
        gdpr_tos.required_variables = ['service_name', 'company_name', 'dpo_email']
        self.templates[gdpr_tos.template_id] = gdpr_tos
    
    def _add_default_privacy_templates(self):
        """Add default Privacy Policy templates"""
        # Generic Privacy Policy
        generic_privacy = LegalTemplate(
            template_id="privacy-generic-v1",
            document_type=DocumentType.PRIVACY_POLICY.value,
            jurisdiction=Jurisdiction.GENERIC.value,
            name="Generic Privacy Policy",
            description="Generic privacy policy template",
            template_content="""PRIVACY POLICY

Last Updated: {{last_updated}}

1. INTRODUCTION
{{company_name}} ("we", "us", or "our") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and protect your personal information.

2. INFORMATION WE COLLECT
We collect the following types of information:
{{information_collected}}

3. HOW WE USE YOUR INFORMATION
We use your information to:
{{information_use}}

4. INFORMATION SHARING
{{information_sharing_policy}}

5. DATA SECURITY
We implement appropriate security measures to protect your personal information.

6. YOUR RIGHTS
You have the right to:
- Access your personal information
- Correct inaccurate information
- Request deletion of your information
- Opt-out of certain data uses

7. COOKIES
{{cookie_policy}}

8. CHILDREN'S PRIVACY
Our Service is not intended for children under {{minimum_age}} years of age.

9. CHANGES TO THIS POLICY
We may update this Privacy Policy from time to time.

10. CONTACT US
For privacy inquiries, contact us at {{contact_email}}.

{{company_name}}
{{company_address}}"""
        )
        generic_privacy.variables = generic_privacy.extract_variables()
        generic_privacy.required_variables = ['company_name', 'contact_email']
        self.templates[generic_privacy.template_id] = generic_privacy
        
        # GDPR-compliant Privacy Policy
        gdpr_privacy = LegalTemplate(
            template_id="privacy-gdpr-v1",
            document_type=DocumentType.PRIVACY_POLICY.value,
            jurisdiction=Jurisdiction.GDPR.value,
            name="GDPR-Compliant Privacy Policy",
            description="Privacy policy template compliant with GDPR",
            template_content="""PRIVACY POLICY (GDPR Compliant)

Last Updated: {{last_updated}}

1. DATA CONTROLLER
{{company_name}}, located at {{company_address}}, is the data controller for personal data processed through {{service_name}}.

2. DATA PROTECTION OFFICER
Our Data Protection Officer can be contacted at {{dpo_email}}.

3. LEGAL BASIS FOR PROCESSING
We process personal data based on:
- Consent (Article 6(1)(a) GDPR)
- Contract performance (Article 6(1)(b) GDPR)
- Legal obligation (Article 6(1)(c) GDPR)
- Legitimate interests (Article 6(1)(f) GDPR)

4. PERSONAL DATA WE COLLECT
{{personal_data_collected}}

5. PURPOSES OF PROCESSING
{{processing_purposes}}

6. DATA RETENTION
We retain personal data only for as long as necessary for the purposes outlined in this policy, or as required by law.

7. YOUR RIGHTS UNDER GDPR
You have the following rights:
- Right of access (Article 15)
- Right to rectification (Article 16)
- Right to erasure (Article 17)
- Right to restrict processing (Article 18)
- Right to data portability (Article 20)
- Right to object (Article 21)
- Rights related to automated decision-making (Article 22)

8. DATA TRANSFERS
Personal data may be transferred outside the EU/EEA with appropriate safeguards (Article 46 GDPR).

9. SECURITY MEASURES
We implement technical and organizational measures to protect personal data (Article 32 GDPR).

10. CONTACT AND COMPLAINTS
For data protection inquiries: {{dpo_email}}
For complaints, you may contact your local data protection authority.

{{company_name}}
{{company_address}}
EU Representative: {{eu_representative}}"""
        )
        gdpr_privacy.variables = gdpr_privacy.extract_variables()
        gdpr_privacy.required_variables = ['company_name', 'dpo_email', 'service_name']
        self.templates[gdpr_privacy.template_id] = gdpr_privacy
        
        # CCPA-compliant Privacy Policy
        ccpa_privacy = LegalTemplate(
            template_id="privacy-ccpa-v1",
            document_type=DocumentType.PRIVACY_POLICY.value,
            jurisdiction=Jurisdiction.CCPA.value,
            name="CCPA-Compliant Privacy Policy",
            description="Privacy policy template compliant with CCPA",
            template_content="""PRIVACY POLICY (CCPA Compliant)

Last Updated: {{last_updated}}

NOTICE AT COLLECTION FOR CALIFORNIA RESIDENTS

This Privacy Policy applies to California residents and complies with the California Consumer Privacy Act (CCPA).

1. INFORMATION WE COLLECT
We collect the following categories of personal information:
{{ccpa_categories_collected}}

2. SOURCES OF INFORMATION
{{information_sources}}

3. BUSINESS OR COMMERCIAL PURPOSES
We use personal information for:
{{business_purposes}}

4. SHARING PERSONAL INFORMATION
{{sharing_disclosure}}

5. YOUR CCPA RIGHTS
As a California resident, you have the right to:
- Know what personal information we collect (Section 1798.100)
- Know whether we sell or disclose personal information (Section 1798.115)
- Opt-out of the sale of personal information (Section 1798.120)
- Delete personal information (Section 1798.105)
- Non-discrimination (Section 1798.125)

6. HOW TO EXERCISE YOUR RIGHTS
To exercise your CCPA rights, contact us at:
Email: {{contact_email}}
Phone: {{contact_phone}}
Website: {{privacy_request_url}}

7. VERIFICATION
We may need to verify your identity before processing requests.

8. AUTHORIZED AGENTS
You may designate an authorized agent to make requests on your behalf.

9. DO NOT SELL MY PERSONAL INFORMATION
We {{sell_personal_information_policy}} sell personal information to third parties.

10. CONTACT US
{{company_name}}
{{company_address}}
Privacy Request: {{contact_email}}"""
        )
        ccpa_privacy.variables = ccpa_privacy.extract_variables()
        ccpa_privacy.required_variables = ['company_name', 'contact_email']
        self.templates[ccpa_privacy.template_id] = ccpa_privacy
    
    def register_template(self, template: LegalTemplate) -> None:
        """Register a custom template"""
        self.templates[template.template_id] = template
        template.updated_at = datetime.utcnow().isoformat()
    
    def get_template(self, template_id: str) -> Optional[LegalTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(
        self,
        document_type: Optional[str] = None,
        jurisdiction: Optional[str] = None
    ) -> List[LegalTemplate]:
        """List templates, optionally filtered by type and jurisdiction"""
        templates = list(self.templates.values())
        
        if document_type:
            templates = [t for t in templates if t.document_type == document_type]
        
        if jurisdiction:
            templates = [t for t in templates if t.jurisdiction == jurisdiction]
        
        return templates
    
    def generate_document(
        self,
        request: DocumentGenerationRequest,
        document_id: Optional[str] = None
    ) -> GeneratedDocument:
        """
        Generate a legal document
        
        Args:
            request: Document generation request
            document_id: Optional document ID, will be generated if not provided
            
        Returns:
            GeneratedDocument
        """
        import uuid
        
        # Get template
        if request.custom_template:
            template_content = request.custom_template
            template_id = None
        elif request.template_id:
            template = self.get_template(request.template_id)
            if not template:
                raise ValueError(f"Template {request.template_id} not found")
            
            # Validate document type and jurisdiction match
            if template.document_type != request.document_type:
                raise ValueError(f"Template type mismatch: template is {template.document_type}, requested {request.document_type}")
            
            if template.jurisdiction != request.jurisdiction:
                raise ValueError(f"Template jurisdiction mismatch: template is {template.jurisdiction}, requested {request.jurisdiction}")
            
            template_content = template.template_content
            template_id = request.template_id
            
            # Validate required variables
            missing_vars = set(template.required_variables) - set(request.variables.keys())
            if missing_vars:
                raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
        else:
            # Find default template
            templates = self.list_templates(request.document_type, request.jurisdiction)
            if not templates:
                raise ValueError(f"No template found for {request.document_type} in {request.jurisdiction}")
            
            template = templates[0]
            template_content = template.template_content
            template_id = template.template_id
            
            # Validate required variables
            missing_vars = set(template.required_variables) - set(request.variables.keys())
            if missing_vars:
                raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
        
        # Add default variables
        variables = {
            'last_updated': datetime.utcnow().strftime('%B %d, %Y'),
            **request.variables
        }
        
        # Render template
        content = self._render_template(template_content, variables)
        
        # Generate document ID
        if not document_id:
            document_id = str(uuid.uuid4())
        
        return GeneratedDocument(
            document_id=document_id,
            document_type=request.document_type,
            jurisdiction=request.jurisdiction,
            template_id=template_id,
            content=content,
            variables_used=variables,
            generated_at=datetime.utcnow().isoformat()
        )
    
    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render template with variables"""
        content = template
        
        for key, value in variables.items():
            # Handle None values
            if value is None:
                value = ""
            
            # Convert to string
            if not isinstance(value, str):
                value = str(value)
            
            # Replace {{variable}} with value
            content = content.replace(f"{{{{{key}}}}}", value)
        
        return content
    
    def validate_template(self, template_content: str, variables: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate that all template variables are provided
        
        Returns:
            Tuple of (is_valid, missing_variables)
        """
        pattern = r'\{\{(\w+)\}\}'
        template_vars = set(re.findall(pattern, template_content))
        provided_vars = set(variables.keys())
        
        missing = list(template_vars - provided_vars)
        return (len(missing) == 0, missing)
    
    def get_jurisdiction_requirements(self, jurisdiction: str) -> Dict[str, Any]:
        """
        Get compliance requirements for a jurisdiction
        
        Returns:
            Dictionary with jurisdiction requirements
        """
        requirements = {
            Jurisdiction.GDPR.value: {
                "name": "General Data Protection Regulation",
                "region": "European Union",
                "key_requirements": [
                    "Lawful basis for processing",
                    "Data subject rights (access, rectification, erasure, etc.)",
                    "Data Protection Officer (DPO) for certain organizations",
                    "Privacy by design and default",
                    "Data breach notification",
                    "Data processing agreements",
                    "Cross-border transfer safeguards"
                ],
                "required_sections": [
                    "Data controller identification",
                    "Legal basis for processing",
                    "Data subject rights",
                    "Data retention",
                    "Data transfers",
                    "Security measures"
                ]
            },
            Jurisdiction.CCPA.value: {
                "name": "California Consumer Privacy Act",
                "region": "California, USA",
                "key_requirements": [
                    "Notice at collection",
                    "Right to know",
                    "Right to delete",
                    "Right to opt-out of sale",
                    "Non-discrimination",
                    "Disclosure of information categories",
                    "Do Not Sell link"
                ],
                "required_sections": [
                    "Information categories collected",
                    "Sources of information",
                    "Business purposes",
                    "Sharing disclosure",
                    "Consumer rights",
                    "Opt-out mechanism"
                ]
            },
            Jurisdiction.PIPEDA.value: {
                "name": "Personal Information Protection and Electronic Documents Act",
                "region": "Canada",
                "key_requirements": [
                    "Consent for collection",
                    "Purpose limitation",
                    "Accuracy",
                    "Safeguards",
                    "Openness",
                    "Individual access",
                    "Challenging compliance"
                ],
                "required_sections": [
                    "Purpose of collection",
                    "Consent mechanism",
                    "Access rights",
                    "Security measures",
                    "Contact information"
                ]
            },
            Jurisdiction.GENERIC.value: {
                "name": "Generic",
                "region": "International",
                "key_requirements": [
                    "Basic privacy principles",
                    "Information collection disclosure",
                    "Data security",
                    "User rights"
                ],
                "required_sections": [
                    "Information collection",
                    "Information use",
                    "Data security",
                    "User rights",
                    "Contact information"
                ]
            }
        }
        
        return requirements.get(jurisdiction, requirements[Jurisdiction.GENERIC.value])


# Global instance
legal_generator = LegalDocumentGenerator()

