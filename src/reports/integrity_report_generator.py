"""
Semantic Integrity Report Generator (JAG-003)

Generates weekly reports on ontology compliance violations.
Lists all violations found in database with severity levels.
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum

from ..ontology.compliance_guardrails import (
    OntologyValidator,
    ComplianceViolation,
    ViolationSeverity
)


class ReportPeriod(str, Enum):
    """Report period types"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class IntegrityReport:
    """Semantic integrity report"""
    period_start: str
    period_end: str
    period_type: ReportPeriod
    total_relationships: int
    violation_count: int
    compliance_score: float
    violations_by_severity: Dict[str, int] = field(default_factory=dict)
    critical_violations: List[Dict] = field(default_factory=list)
    high_violations: List[Dict] = field(default_factory=list)
    medium_violations: List[Dict] = field(default_factory=list)
    low_violations: List[Dict] = field(default_factory=list)
    overridden_count: int = 0
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        result = asdict(self)
        result["period_type"] = self.period_type.value
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Export as JSON string"""
        return json.dumps(self.to_dict(), indent=indent)


class IntegrityReportGenerator:
    """
    Generates semantic integrity reports.
    
    Creates weekly (or custom period) reports listing all compliance violations
    found in the database with severity breakdown.
    """
    
    def __init__(
        self,
        validator: Optional[OntologyValidator] = None,
        report_storage_path: Optional[str] = None
    ):
        """
        Initialize report generator.
        
        Args:
            validator: OntologyValidator instance (creates new if not provided)
            report_storage_path: Path to store reports (default: reports/ directory)
        """
        self.validator = validator or OntologyValidator()
        
        if report_storage_path is None:
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            report_storage_path = os.path.join(current_dir, "reports")
        
        self.report_storage_path = report_storage_path
        os.makedirs(self.report_storage_path, exist_ok=True)
    
    def generate_weekly_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> IntegrityReport:
        """
        Generate weekly semantic integrity report.
        
        Args:
            start_date: Start date (ISO format, default: 7 days ago)
            end_date: End date (ISO format, default: now)
            
        Returns:
            IntegrityReport object
        """
        if end_date is None:
            end_date = datetime.utcnow()
        else:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        if start_date is None:
            start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        # Get violations from validator
        all_violations = self.validator.get_violations(include_overridden=True)
        
        # Filter violations by date range
        period_violations = [
            v for v in all_violations
            if start_date <= datetime.fromisoformat(v.timestamp.replace('Z', '+00:00')) <= end_date
        ]
        
        # Count by severity
        violations_by_severity = {
            ViolationSeverity.CRITICAL.value: 0,
            ViolationSeverity.HIGH.value: 0,
            ViolationSeverity.MEDIUM.value: 0,
            ViolationSeverity.LOW.value: 0
        }
        
        critical = []
        high = []
        medium = []
        low = []
        overridden_count = 0
        
        for violation in period_violations:
            if violation.overridden:
                overridden_count += 1
                continue
            
            severity = violation.severity.value
            violations_by_severity[severity] += 1
            
            violation_dict = {
                "source_type": violation.source_type,
                "target_type": violation.target_type,
                "relationship_type": violation.relationship_type,
                "reason": violation.reason,
                "timestamp": violation.timestamp
            }
            
            if violation.severity == ViolationSeverity.CRITICAL:
                critical.append(violation_dict)
            elif violation.severity == ViolationSeverity.HIGH:
                high.append(violation_dict)
            elif violation.severity == ViolationSeverity.MEDIUM:
                medium.append(violation_dict)
            else:
                low.append(violation_dict)
        
        # Calculate compliance score
        total_relationships = len(period_violations) + 100  # Estimate (would come from actual DB)
        violation_count = len(period_violations) - overridden_count
        compliance_score = 1.0 - (violation_count / total_relationships) if total_relationships > 0 else 1.0
        
        report = IntegrityReport(
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat(),
            period_type=ReportPeriod.WEEKLY,
            total_relationships=total_relationships,
            violation_count=violation_count,
            compliance_score=compliance_score,
            violations_by_severity=violations_by_severity,
            critical_violations=critical,
            high_violations=high,
            medium_violations=medium,
            low_violations=low,
            overridden_count=overridden_count
        )
        
        return report
    
    def generate_report(
        self,
        period_type: ReportPeriod = ReportPeriod.WEEKLY,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> IntegrityReport:
        """
        Generate integrity report for specified period.
        
        Args:
            period_type: Type of report period
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            IntegrityReport object
        """
        if period_type == ReportPeriod.WEEKLY:
            return self.generate_weekly_report(start_date, end_date)
        elif period_type == ReportPeriod.DAILY:
            if end_date is None:
                end_date = datetime.utcnow()
            else:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            start_date = end_date - timedelta(days=1)
            return self.generate_weekly_report(
                start_date.isoformat(),
                end_date.isoformat()
            )
        elif period_type == ReportPeriod.MONTHLY:
            if end_date is None:
                end_date = datetime.utcnow()
            else:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            start_date = end_date - timedelta(days=30)
            return self.generate_weekly_report(
                start_date.isoformat(),
                end_date.isoformat()
            )
        else:
            # Custom period
            if not start_date or not end_date:
                raise ValueError("start_date and end_date required for custom period")
            return self.generate_weekly_report(start_date, end_date)
    
    def save_report(self, report: IntegrityReport, filename: Optional[str] = None) -> str:
        """
        Save report to file.
        
        Args:
            report: IntegrityReport to save
            filename: Optional filename (default: auto-generated)
            
        Returns:
            Path to saved report file
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"integrity_report_{timestamp}.json"
        
        filepath = os.path.join(self.report_storage_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report.to_json(indent=2))
        
        return filepath
    
    def generate_summary(self, report: IntegrityReport) -> str:
        """
        Generate human-readable summary of report.
        
        Args:
            report: IntegrityReport to summarize
            
        Returns:
            Formatted string summary
        """
        lines = [
            "=" * 70,
            "Semantic Integrity Report",
            "=" * 70,
            f"Period: {report.period_start} to {report.period_end}",
            f"Type: {report.period_type.value.upper()}",
            f"Generated: {report.generated_at}",
            "",
            "Summary:",
            f"  Total Relationships: {report.total_relationships}",
            f"  Violations: {report.violation_count}",
            f"  Overridden: {report.overridden_count}",
            f"  Compliance Score: {report.compliance_score:.3f}",
            "",
            "Violations by Severity:",
            f"  CRITICAL: {report.violations_by_severity.get('CRITICAL', 0)}",
            f"  HIGH: {report.violations_by_severity.get('HIGH', 0)}",
            f"  MEDIUM: {report.violations_by_severity.get('MEDIUM', 0)}",
            f"  LOW: {report.violations_by_severity.get('LOW', 0)}",
        ]
        
        if report.critical_violations:
            lines.append("")
            lines.append("CRITICAL Violations:")
            for v in report.critical_violations[:10]:  # Show first 10
                lines.append(
                    f"  - {v['source_type']} → {v['target_type']} "
                    f"({v['relationship_type']}): {v['reason']}"
                )
            if len(report.critical_violations) > 10:
                lines.append(f"  ... and {len(report.critical_violations) - 10} more")
        
        if report.high_violations:
            lines.append("")
            lines.append("HIGH Violations:")
            for v in report.high_violations[:5]:  # Show first 5
                lines.append(
                    f"  - {v['source_type']} → {v['target_type']} "
                    f"({v['relationship_type']})"
                )
            if len(report.high_violations) > 5:
                lines.append(f"  ... and {len(report.high_violations) - 5} more")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)

