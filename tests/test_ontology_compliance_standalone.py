"""
Standalone test script for JAG-003 Ontology Compliance (no pytest required)
Run with: python tests/test_ontology_compliance_standalone.py
"""

import sys
import os
import json
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ontology.compliance_guardrails import (
    OntologyValidator,
    ViolationSeverity
)
from src.reports.integrity_report_generator import (
    IntegrityReportGenerator,
    ReportPeriod
)


def test_forbidden_relationships():
    """Test that forbidden relationships are blocked"""
    print("Testing Forbidden Relationships...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_file = os.path.join(tmpdir, "rules.json")
        rules = {
            "Medication": {
                "forbidden_targets": ["SoftwareBug", "Vehicle"]
            },
            "Antibiotic": {
                "forbidden_targets": ["Virus", "ViralInfection"]
            }
        }
        
        with open(rules_file, 'w') as f:
            json.dump(rules, f)
        
        validator = OntologyValidator(rules_path=rules_file)
        
        # Test 1: Allowed relationship
        result1 = validator.validate_relationship("Medication", "Disease")
        if result1.is_compliant:
            print("  [PASS] Allowed relationship passes")
        else:
            print("  [FAIL] Allowed relationship should pass")
            return False
        
        # Test 2: Forbidden relationship
        result2 = validator.validate_relationship("Medication", "SoftwareBug")
        if not result2.is_compliant and len(result2.violations) > 0:
            print("  [PASS] Forbidden relationship blocked")
        else:
            print("  [FAIL] Forbidden relationship should be blocked")
            return False
        
        # Test 3: Antibiotic → Virus (impossible)
        result3 = validator.validate_relationship("Antibiotic", "Virus")
        if not result3.is_compliant:
            print("  [PASS] Antibiotic -> Virus blocked (impossible relationship)")
        else:
            print("  [FAIL] Antibiotic → Virus should be blocked")
            return False
    
    return True


def test_severity_levels():
    """Test severity level determination"""
    print("\nTesting Severity Levels...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_file = os.path.join(tmpdir, "rules.json")
        rules = {
            "Medication": {
                "forbidden_targets": ["SoftwareBug"]
            }
        }
        
        with open(rules_file, 'w') as f:
            json.dump(rules, f)
        
        validator = OntologyValidator(rules_path=rules_file)
        
        result = validator.validate_relationship("Medication", "SoftwareBug")
        
        if result.violations[0].severity == ViolationSeverity.CRITICAL:
            print("  [PASS] CRITICAL severity assigned")
        else:
            print(f"  [FAIL] Expected CRITICAL, got {result.violations[0].severity}")
            return False
    
    return True


def test_admin_override():
    """Test admin override with audit trail"""
    print("\nTesting Admin Override...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_file = os.path.join(tmpdir, "rules.json")
        rules = {
            "Medication": {
                "forbidden_targets": ["SoftwareBug"]
            }
        }
        
        with open(rules_file, 'w') as f:
            json.dump(rules, f)
        
        validator = OntologyValidator(rules_path=rules_file)
        
        result = validator.validate_relationship("Medication", "SoftwareBug")
        violation = result.violations[0]
        
        # Override
        validator.override_violation(
            violation=violation,
            override_reason="Research exception",
            override_by="admin_user"
        )
        
        if violation.overridden and violation.override_by == "admin_user":
            print("  [PASS] Admin override with audit trail")
        else:
            print("  [FAIL] Override should set overridden flag and audit info")
            return False
    
    return True


def test_compliance_score():
    """Test compliance score calculation"""
    print("\nTesting Compliance Score...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_file = os.path.join(tmpdir, "rules.json")
        rules = {
            "Medication": {
                "forbidden_targets": ["SoftwareBug"]
            }
        }
        
        with open(rules_file, 'w') as f:
            json.dump(rules, f)
        
        validator = OntologyValidator(rules_path=rules_file)
        
        # No violations = perfect score
        score1 = validator.get_compliance_score()
        if score1 == 1.0:
            print("  [PASS] Perfect score with no violations")
        else:
            print(f"  [FAIL] Expected 1.0, got {score1}")
            return False
        
        # Add violations
        validator.validate_relationship("Medication", "SoftwareBug")
        validator.validate_relationship("Medication", "SoftwareBug")
        
        score2 = validator.get_compliance_score()
        if score2 < 1.0:
            print("  [PASS] Score decreases with violations")
        else:
            print(f"  [FAIL] Score should be < 1.0, got {score2}")
            return False
    
    return True


def test_integrity_report():
    """Test integrity report generation"""
    print("\nTesting Integrity Report...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_file = os.path.join(tmpdir, "rules.json")
        rules = {
            "Medication": {
                "forbidden_targets": ["SoftwareBug"]
            }
        }
        
        with open(rules_file, 'w') as f:
            json.dump(rules, f)
        
        validator = OntologyValidator(rules_path=rules_file)
        
        # Create violations
        validator.validate_relationship("Medication", "SoftwareBug")
        
        generator = IntegrityReportGenerator(
            validator=validator,
            report_storage_path=os.path.join(tmpdir, "reports")
        )
        
        report = generator.generate_weekly_report()
        
        if report.violation_count > 0 and report.compliance_score < 1.0:
            print("  [PASS] Report generated with violations")
        else:
            print("  [FAIL] Report should show violations")
            return False
        
        # Test summary
        summary = generator.generate_summary(report)
        if "Semantic Integrity Report" in summary and "Compliance Score" in summary:
            print("  [PASS] Report summary generated")
        else:
            print("  [FAIL] Summary should contain key information")
            return False
        
        # Test save
        filepath = generator.save_report(report)
        if os.path.exists(filepath):
            print("  [PASS] Report saved to file")
        else:
            print("  [FAIL] Report file should be created")
            return False
    
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("JAG-003 Ontology Compliance Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("Forbidden Relationships", test_forbidden_relationships()))
    results.append(("Severity Levels", test_severity_levels()))
    results.append(("Admin Override", test_admin_override()))
    results.append(("Compliance Score", test_compliance_score()))
    results.append(("Integrity Report", test_integrity_report()))
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        if isinstance(result, tuple):
            passed, message = result
            status = "PASS" if passed else f"FAIL ({message})"
        else:
            passed = result
            status = "PASS" if passed else "FAIL"
        
        print(f"{name:30} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("All tests PASSED!")
        return 0
    else:
        print("Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

