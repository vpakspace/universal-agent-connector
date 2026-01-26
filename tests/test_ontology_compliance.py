"""
Test Suite for Ontology Compliance Guardrails (JAG-003)

Tests prevention of impossible relationships like:
- "Antibiotic treats Virus"
- "Software Bug caused by Medication"
- "Vehicle treats Disease"
"""

import pytest
import sys
import os
import json
import tempfile
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ontology.compliance_guardrails import (
    OntologyValidator,
    ComplianceViolation,
    ViolationSeverity,
    ComplianceResult
)
from src.reports.integrity_report_generator import (
    IntegrityReportGenerator,
    IntegrityReport,
    ReportPeriod
)


class TestOntologyValidator:
    """Test OntologyValidator"""
    
    @pytest.fixture
    def validator(self, tmp_path):
        """Create validator with temporary rules file"""
        rules_file = tmp_path / "forbidden_relationships.json"
        
        # Create test rules
        rules = {
            "Medication": {
                "allowed_targets": ["Disease", "Symptom", "Patient"],
                "forbidden_targets": ["SoftwareBug", "Vehicle", "Building"]
            },
            "Antibiotic": {
                "allowed_targets": ["BacterialInfection", "Disease"],
                "forbidden_targets": ["Virus", "ViralInfection", "SoftwareBug"]
            }
        }
        
        with open(rules_file, 'w') as f:
            json.dump(rules, f)
        
        return OntologyValidator(rules_path=str(rules_file))
    
    def test_validate_allowed_relationship(self, validator):
        """Test that allowed relationships pass validation"""
        result = validator.validate_relationship(
            source_type="Medication",
            target_type="Disease",
            relationship_type="TREATS"
        )
        
        assert result.is_compliant is True
        assert len(result.violations) == 0
        assert result.compliance_score == 1.0
    
    def test_validate_forbidden_relationship(self, validator):
        """Test that forbidden relationships are blocked"""
        result = validator.validate_relationship(
            source_type="Medication",
            target_type="SoftwareBug",
            relationship_type="CAUSES"
        )
        
        assert result.is_compliant is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == ViolationSeverity.CRITICAL
        assert result.compliance_score == 0.0
    
    def test_antibiotic_virus_blocked(self, validator):
        """Test that Antibiotic → Virus is blocked (impossible relationship)"""
        result = validator.validate_relationship(
            source_type="Antibiotic",
            target_type="Virus",
            relationship_type="TREATS"
        )
        
        assert result.is_compliant is False
        assert len(result.violations) == 1
        assert "Antibiotic" in result.violations[0].reason
        assert "Virus" in result.violations[0].reason
    
    def test_medication_softwarebug_blocked(self, validator):
        """Test that Medication → SoftwareBug is blocked"""
        result = validator.validate_relationship(
            source_type="Medication",
            target_type="SoftwareBug",
            relationship_type="CAUSES"
        )
        
        assert result.is_compliant is False
        assert result.violations[0].severity == ViolationSeverity.CRITICAL
    
    def test_severity_determination(self, validator):
        """Test severity determination for different violations"""
        # CRITICAL: Medication → SoftwareBug
        result1 = validator.validate_relationship("Medication", "SoftwareBug")
        assert result1.violations[0].severity == ViolationSeverity.CRITICAL
        
        # CRITICAL: Antibiotic → Virus
        result2 = validator.validate_relationship("Antibiotic", "Virus")
        assert result2.violations[0].severity == ViolationSeverity.CRITICAL
    
    def test_override_violation(self, validator):
        """Test admin override with audit trail"""
        result = validator.validate_relationship("Medication", "SoftwareBug")
        violation = result.violations[0]
        
        # Override with admin approval
        validator.override_violation(
            violation=violation,
            override_reason="Special case for research",
            override_by="admin_user"
        )
        
        assert violation.overridden is True
        assert violation.override_reason == "Special case for research"
        assert violation.override_by == "admin_user"
        assert violation.override_timestamp is not None
    
    def test_validate_batch(self, validator):
        """Test batch validation of multiple relationships"""
        relationships = [
            {"source_type": "Medication", "target_type": "Disease"},  # Allowed
            {"source_type": "Medication", "target_type": "SoftwareBug"},  # Forbidden
            {"source_type": "Antibiotic", "target_type": "Virus"},  # Forbidden
            {"source_type": "Antibiotic", "target_type": "BacterialInfection"}  # Allowed
        ]
        
        result = validator.validate_batch(relationships)
        
        assert result.total_relationships == 4
        assert result.violation_count == 2
        assert result.compliance_score < 1.0
        assert len(result.violations) == 2
    
    def test_get_violations(self, validator):
        """Test getting violations with filters"""
        # Create some violations
        validator.validate_relationship("Medication", "SoftwareBug")
        validator.validate_relationship("Antibiotic", "Virus")
        
        # Get all violations
        all_violations = validator.get_violations()
        assert len(all_violations) >= 2
        
        # Get only CRITICAL
        critical = validator.get_violations(severity=ViolationSeverity.CRITICAL)
        assert all(v.severity == ViolationSeverity.CRITICAL for v in critical)
    
    def test_get_compliance_score(self, validator):
        """Test compliance score calculation"""
        # No violations = perfect score
        score1 = validator.get_compliance_score()
        assert score1 == 1.0
        
        # Add violations
        validator.validate_relationship("Medication", "SoftwareBug")
        validator.validate_relationship("Medication", "Vehicle")
        
        score2 = validator.get_compliance_score()
        assert score2 < 1.0
        
        # Override one violation
        violations = validator.get_violations()
        validator.override_violation(violations[0], "Override", "admin")
        
        score3 = validator.get_compliance_score()
        assert score3 > score2  # Score should improve after override


class TestIntegrityReportGenerator:
    """Test Integrity Report Generator"""
    
    @pytest.fixture
    def validator(self, tmp_path):
        """Create validator"""
        rules_file = tmp_path / "rules.json"
        rules = {
            "Medication": {
                "forbidden_targets": ["SoftwareBug", "Vehicle"]
            }
        }
        with open(rules_file, 'w') as f:
            json.dump(rules, f)
        return OntologyValidator(rules_path=str(rules_file))
    
    @pytest.fixture
    def report_generator(self, validator, tmp_path):
        """Create report generator"""
        return IntegrityReportGenerator(
            validator=validator,
            report_storage_path=str(tmp_path / "reports")
        )
    
    def test_generate_weekly_report(self, report_generator):
        """Test weekly report generation"""
        # Create some violations
        report_generator.validator.validate_relationship("Medication", "SoftwareBug")
        report_generator.validator.validate_relationship("Medication", "Vehicle")
        
        report = report_generator.generate_weekly_report()
        
        assert isinstance(report, IntegrityReport)
        assert report.period_type == ReportPeriod.WEEKLY
        assert report.violation_count >= 2
        assert report.compliance_score < 1.0
        assert "CRITICAL" in report.violations_by_severity
    
    def test_report_severity_breakdown(self, report_generator):
        """Test that report breaks down violations by severity"""
        # Create violations of different severities
        report_generator.validator.validate_relationship("Medication", "SoftwareBug")  # CRITICAL
        report_generator.validator.validate_relationship("Antibiotic", "Virus")  # CRITICAL
        
        report = report_generator.generate_weekly_report()
        
        assert report.violations_by_severity["CRITICAL"] >= 2
        assert len(report.critical_violations) >= 2
    
    def test_save_report(self, report_generator, tmp_path):
        """Test saving report to file"""
        report = report_generator.generate_weekly_report()
        
        filepath = report_generator.save_report(report)
        
        assert os.path.exists(filepath)
        
        # Verify JSON is valid
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert "compliance_score" in data
        assert "violations_by_severity" in data
    
    def test_generate_summary(self, report_generator):
        """Test human-readable summary generation"""
        report_generator.validator.validate_relationship("Medication", "SoftwareBug")
        
        report = report_generator.generate_weekly_report()
        summary = report_generator.generate_summary(report)
        
        assert "Semantic Integrity Report" in summary
        assert "Compliance Score" in summary
        assert "CRITICAL" in summary
        assert "Medication" in summary
        assert "SoftwareBug" in summary
    
    def test_report_json_export(self, report_generator):
        """Test report JSON export"""
        report = report_generator.generate_weekly_report()
        
        json_str = report.to_json()
        data = json.loads(json_str)
        
        assert "period_start" in data
        assert "period_end" in data
        assert "compliance_score" in data
        assert "violations_by_severity" in data
        assert "critical_violations" in data
    
    def test_custom_period_report(self, report_generator):
        """Test custom period report"""
        start_date = (datetime.utcnow() - timedelta(days=14)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        report = report_generator.generate_report(
            period_type=ReportPeriod.CUSTOM,
            start_date=start_date,
            end_date=end_date
        )
        
        assert report.period_type == ReportPeriod.CUSTOM
        assert report.period_start == start_date
        assert report.period_end == end_date
    
    def test_daily_report(self, report_generator):
        """Test daily report generation"""
        report = report_generator.generate_report(period_type=ReportPeriod.DAILY)
        
        assert report.period_type == ReportPeriod.DAILY
    
    def test_monthly_report(self, report_generator):
        """Test monthly report generation"""
        report = report_generator.generate_report(period_type=ReportPeriod.MONTHLY)
        
        assert report.period_type == ReportPeriod.MONTHLY


class TestIntegration:
    """Integration tests for complete workflow"""
    
    def test_complete_workflow(self, tmp_path):
        """Test complete workflow: validate → override → report"""
        from src.ontology.compliance_guardrails import OntologyValidator
        from src.reports.integrity_report_generator import IntegrityReportGenerator
        
        # Step 1: Create validator
        rules_file = tmp_path / "rules.json"
        rules = {
            "Medication": {
                "forbidden_targets": ["SoftwareBug"]
            }
        }
        with open(rules_file, 'w') as f:
            json.dump(rules, f)
        
        validator = OntologyValidator(rules_path=str(rules_file))
        
        # Step 2: Validate relationship (should fail)
        result = validator.validate_relationship("Medication", "SoftwareBug")
        assert result.is_compliant is False
        
        # Step 3: Override with admin approval
        violation = result.violations[0]
        validator.override_violation(
            violation=violation,
            override_reason="Research exception",
            override_by="admin"
        )
        
        # Step 4: Generate report
        generator = IntegrityReportGenerator(
            validator=validator,
            report_storage_path=str(tmp_path / "reports")
        )
        
        report = generator.generate_weekly_report()
        
        assert report.violation_count >= 1
        assert report.overridden_count >= 1
        
        # Step 5: Save report
        filepath = generator.save_report(report)
        assert os.path.exists(filepath)
    
    def test_compliance_score_calculation(self, tmp_path):
        """Test compliance score calculation: 1 - (violations / total_relationships)"""
        from src.ontology.compliance_guardrails import OntologyValidator
        
        rules_file = tmp_path / "rules.json"
        rules = {
            "Medication": {
                "forbidden_targets": ["SoftwareBug", "Vehicle"]
            }
        }
        with open(rules_file, 'w') as f:
            json.dump(rules, f)
        
        validator = OntologyValidator(rules_path=str(rules_file))
        
        # Create 10 relationships, 2 are violations
        relationships = [
            {"source_type": "Medication", "target_type": "Disease"} for _ in range(8)
        ] + [
            {"source_type": "Medication", "target_type": "SoftwareBug"},
            {"source_type": "Medication", "target_type": "Vehicle"}
        ]
        
        result = validator.validate_batch(relationships)
        
        # Compliance score = 1 - (2 violations / 10 total) = 0.8
        expected_score = 1.0 - (2.0 / 10.0)
        assert abs(result.compliance_score - expected_score) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

