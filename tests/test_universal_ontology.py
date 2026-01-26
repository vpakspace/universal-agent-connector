"""
Test Suite for Universal Ontology Adapter (JAG Universal)

Tests ontology parsing, tool generation, validation, and health checks
across multiple formats and domains.
"""

import pytest
import sys
import os
import tempfile
import yaml
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Check dependencies
try:
    import rdflib
    HAS_RDFLIB = True
except ImportError:
    HAS_RDFLIB = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from src.intelligence.ontology_adapter import (
    get_ontology_adapter,
    TurtleParser,
    YAMLParser,
    JSONLDParser
)
from src.intelligence.tool_registry import ToolRegistry, scan_ontology
from src.intelligence.validation_engine import ValidationEngine, AxiomValidator
from src.intelligence.ontology_validator import validate_ontology_health


@pytest.mark.skipif(not HAS_YAML, reason="Requires pyyaml")
class TestYAMLParser:
    """Test YAML ontology parser"""
    
    def test_parse_yaml_ontology(self, tmp_path):
        """Test parsing YAML ontology"""
        yaml_file = tmp_path / "test_ontology.yaml"
        yaml_content = """
classes:
  - uri: "http://example.org/Person"
    label: "Person"
    comment: "A human being"
    properties:
      - "name"
      - "age"
  
  - uri: "http://example.org/Organization"
    label: "Organization"
    comment: "A company or institution"

properties:
  - uri: "http://example.org/name"
    label: "name"
    domain: "http://example.org/Person"
    range: "http://www.w3.org/2001/XMLSchema#string"
  
  - uri: "http://example.org/age"
    label: "age"
    domain: "http://example.org/Person"
    range: "http://www.w3.org/2001/XMLSchema#integer"
"""
        yaml_file.write_text(yaml_content)
        
        parser = YAMLParser()
        ontology_data = parser.parse_ontology(str(yaml_file))
        
        assert ontology_data['format'] == 'yaml'
        assert 'data' in ontology_data
    
    def test_extract_classes_from_yaml(self, tmp_path):
        """Test extracting classes from YAML"""
        yaml_file = tmp_path / "test.yaml"
        yaml_content = """
classes:
  - uri: "http://example.org/Person"
    label: "Person"
    comment: "A person"
"""
        yaml_file.write_text(yaml_content)
        
        parser = YAMLParser()
        ontology_data = parser.parse_ontology(str(yaml_file))
        classes = parser.extract_classes(ontology_data)
        
        assert len(classes) == 1
        assert classes[0].label == "Person"
        assert classes[0].uri == "http://example.org/Person"


class TestToolRegistry:
    """Test dynamic tool registry"""
    
    @pytest.mark.skipif(not HAS_YAML, reason="Requires pyyaml")
    def test_generate_crud_tools(self, tmp_path):
        """Test CRUD tool generation"""
        yaml_file = tmp_path / "test.yaml"
        yaml_content = """
classes:
  - uri: "http://example.org/Person"
    label: "Person"
    comment: "A person"
    properties:
      - "name"
      - "age"

properties:
  - uri: "http://example.org/name"
    label: "name"
    domain: "http://example.org/Person"
    range: "string"
"""
        yaml_file.write_text(yaml_content)
        
        tools = scan_ontology(str(yaml_file), enable_crud=True, enable_queries=False)
        
        # Should generate CRUD tools
        tool_names = [t.tool_name for t in tools]
        assert "get_person" in tool_names
        assert "create_person" in tool_names
        assert "update_person" in tool_names
        assert "delete_person" in tool_names
        assert "list_persons" in tool_names
    
    @pytest.mark.skipif(not HAS_YAML, reason="Requires pyyaml")
    def test_generate_query_tools(self, tmp_path):
        """Test query tool generation"""
        yaml_file = tmp_path / "test.yaml"
        yaml_content = """
classes:
  - uri: "http://example.org/Person"
    label: "Person"

properties:
  - uri: "http://example.org/age"
    label: "age"
    domain: "http://example.org/Person"
    range: "integer"
"""
        yaml_file.write_text(yaml_content)
        
        tools = scan_ontology(str(yaml_file), enable_crud=False, enable_queries=True)
        
        # Should generate query tools
        tool_names = [t.tool_name for t in tools]
        assert any("age" in name for name in tool_names)


class TestValidationEngine:
    """Test validation engine"""
    
    def test_validate_age_constraint(self):
        """Test age constraint validation"""
        from src.intelligence.ontology_adapter import OntologyAxiom
        
        axioms = [
            OntologyAxiom(
                type="age_constraint",
                subject="http://example.org/Person",
                predicate="minAge",
                object="18",
                source="yaml"
            )
        ]
        
        validator = AxiomValidator(axioms)
        result = validator.validate_constraint("http://example.org/Person", "age", 25)
        
        assert result.is_valid
        
        # Test violation
        result2 = validator.validate_constraint("http://example.org/Person", "age", 15)
        assert not result2.is_valid
        assert len(result2.violations) > 0


class TestOntologyValidator:
    """Test ontology health validator"""
    
    def test_validate_ontology_health(self):
        """Test ontology health validation"""
        from src.intelligence.ontology_adapter import OntologyClass, OntologyProperty, OntologyAxiom
        
        classes = [
            OntologyClass(
                uri="http://example.org/Person",
                label="Person",
                parent_classes=[]
            )
        ]
        
        properties = [
            OntologyProperty(
                uri="http://example.org/name",
                label="name",
                domain="http://example.org/Person",
                range="string"
            )
        ]
        
        axioms = []
        
        report = validate_ontology_health(classes, properties, axioms)
        
        assert report.status in ["HEALTHY", "WARNING", "CRITICAL", "FAILED"]
        assert 0.0 <= report.mine_estimate <= 1.0
    
    def test_check_missing_inverse_properties(self):
        """Test detection of missing inverse properties"""
        from src.intelligence.ontology_adapter import OntologyProperty
        
        properties = [
            OntologyProperty(
                uri="http://example.org/worksFor",
                label="worksFor",
                domain="http://example.org/Person",
                range="http://example.org/Organization",
                inverse_property=None  # Missing inverse
            )
        ]
        
        from src.intelligence.ontology_validator import OntologyValidator
        validator = OntologyValidator()
        issues = validator._check_inverse_properties(properties)
        
        # Should detect missing inverse
        assert len(issues) > 0
        assert any("inverse" in issue.issue.lower() for issue in issues)


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.skipif(not HAS_YAML, reason="Requires pyyaml")
    def test_complete_workflow(self, tmp_path):
        """Test complete workflow: parse → generate tools → validate"""
        # Create test ontology
        yaml_file = tmp_path / "healthcare.yaml"
        yaml_content = """
classes:
  - uri: "http://hl7.org/fhir/Patient"
    label: "Patient"
    comment: "A patient in the healthcare system"
    properties:
      - "name"
      - "age"
      - "diagnosis"

properties:
  - uri: "http://hl7.org/fhir/name"
    label: "name"
    domain: "http://hl7.org/fhir/Patient"
    range: "string"
  
  - uri: "http://hl7.org/fhir/age"
    label: "age"
    domain: "http://hl7.org/fhir/Patient"
    range: "integer"
  
  - uri: "http://hl7.org/fhir/diagnosis"
    label: "diagnosis"
    domain: "http://hl7.org/fhir/Patient"
    range: "string"

axioms:
  - type: "age_constraint"
    subject: "http://hl7.org/fhir/Patient"
    predicate: "minAge"
    object: "0"
"""
        yaml_file.write_text(yaml_content)
        
        # Step 1: Parse ontology
        adapter = get_ontology_adapter(str(yaml_file))
        ontology_data = adapter.parse_ontology(str(yaml_file))
        classes = adapter.extract_classes(ontology_data)
        properties = adapter.extract_properties(ontology_data)
        axioms = adapter.extract_axioms(ontology_data)
        
        assert len(classes) > 0
        assert len(properties) > 0
        
        # Step 2: Generate tools
        tools = scan_ontology(str(yaml_file))
        assert len(tools) > 0
        
        # Step 3: Validate health
        report = validate_ontology_health(classes, properties, axioms)
        assert report.status in ["HEALTHY", "WARNING", "CRITICAL", "FAILED"]
    
    @pytest.mark.skipif(not HAS_YAML, reason="Requires pyyaml")
    def test_different_domains(self, tmp_path):
        """Test that different domain ontologies generate different tools"""
        # Healthcare ontology
        healthcare_file = tmp_path / "healthcare.yaml"
        healthcare_content = """
classes:
  - uri: "http://hl7.org/fhir/Patient"
    label: "Patient"
properties:
  - uri: "http://hl7.org/fhir/diagnosis"
    label: "diagnosis"
    domain: "http://hl7.org/fhir/Patient"
"""
        healthcare_file.write_text(healthcare_content)
        
        # Financial ontology
        financial_file = tmp_path / "financial.yaml"
        financial_content = """
classes:
  - uri: "http://xbrl.org/Account"
    label: "Account"
properties:
  - uri: "http://xbrl.org/balance"
    label: "balance"
    domain: "http://xbrl.org/Account"
"""
        financial_file.write_text(financial_content)
        
        # Generate tools for each
        healthcare_tools = scan_ontology(str(healthcare_file))
        financial_tools = scan_ontology(str(financial_file))
        
        # Should have different tools
        healthcare_names = {t.tool_name for t in healthcare_tools}
        financial_names = {t.tool_name for t in financial_tools}
        
        assert "patient" in str(healthcare_names).lower()
        assert "account" in str(financial_names).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

