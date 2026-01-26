"""
Audit log export functionality for compliance
Supports CSV and JSON export formats
"""

from typing import Dict, List, Optional, Any, Iterator
from enum import Enum
import csv
import json
from io import StringIO
from datetime import datetime
from .audit_logger import AuditLogger, ActionType


class ExportFormat(Enum):
    """Export formats"""
    CSV = "csv"
    JSON = "json"


class AuditLogExporter:
    """
    Audit log exporter for compliance reporting.
    Exports audit logs in standard formats (CSV, JSON).
    """
    
    def __init__(self, audit_logger: AuditLogger):
        """
        Initialize audit log exporter.
        
        Args:
            audit_logger: AuditLogger instance
        """
        self.audit_logger = audit_logger
    
    def export_logs(
        self,
        format: ExportFormat,
        agent_id: Optional[str] = None,
        action_type: Optional[ActionType] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> str:
        """
        Export audit logs in specified format.
        
        Args:
            format: Export format (CSV or JSON)
            agent_id: Optional agent ID filter
            action_type: Optional action type filter
            status: Optional status filter
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            limit: Optional limit on number of records
            
        Returns:
            str: Exported data as string
        """
        # Get logs
        logs_data = self.audit_logger.get_logs(
            agent_id=agent_id,
            action_type=action_type,
            status=status,
            limit=limit or 10000,
            offset=0
        )
        
        logs = logs_data.get('logs', [])
        
        # Filter by date range if provided
        if start_date or end_date:
            logs = self._filter_by_date_range(logs, start_date, end_date)
        
        # Export in requested format
        if format == ExportFormat.CSV:
            return self._export_csv(logs)
        elif format == ExportFormat.JSON:
            return self._export_json(logs)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _filter_by_date_range(
        self,
        logs: List[Dict[str, Any]],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Filter logs by date range"""
        filtered = []
        
        for log in logs:
            timestamp = log.get('timestamp')
            if not timestamp:
                continue
            
            try:
                log_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                if start_date:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    if log_date < start:
                        continue
                
                if end_date:
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if log_date > end:
                        continue
                
                filtered.append(log)
            except:
                # Skip logs with invalid timestamps
                continue
        
        return filtered
    
    def _export_csv(self, logs: List[Dict[str, Any]]) -> str:
        """Export logs as CSV"""
        if not logs:
            return ""
        
        output = StringIO()
        
        # Get all unique keys from logs
        fieldnames = set()
        for log in logs:
            fieldnames.update(log.keys())
        
        # Standardize field order
        standard_fields = [
            'id', 'timestamp', 'action_type', 'agent_id', 'user_id',
            'status', 'error_message', 'details'
        ]
        
        # Add standard fields first, then any extras
        ordered_fields = [f for f in standard_fields if f in fieldnames]
        ordered_fields.extend(sorted(fieldnames - set(standard_fields)))
        
        writer = csv.DictWriter(output, fieldnames=ordered_fields, extrasaction='ignore')
        writer.writeheader()
        
        for log in logs:
            # Flatten details if present
            row = log.copy()
            if 'details' in row and isinstance(row['details'], dict):
                # Add details as separate columns or JSON string
                details_str = json.dumps(row['details'])
                row['details'] = details_str
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def _export_json(self, logs: List[Dict[str, Any]]) -> str:
        """Export logs as JSON"""
        # Create export structure
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_records': len(logs),
            'logs': logs
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    def export_summary_report(
        self,
        format: ExportFormat,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Export summary report of audit logs.
        
        Args:
            format: Export format (CSV or JSON)
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            
        Returns:
            str: Exported summary report
        """
        # Get all logs in date range
        logs_data = self.audit_logger.get_logs(limit=100000, offset=0)
        logs = logs_data.get('logs', [])
        
        if start_date or end_date:
            logs = self._filter_by_date_range(logs, start_date, end_date)
        
        # Generate summary
        summary = self._generate_summary(logs)
        
        if format == ExportFormat.CSV:
            return self._export_summary_csv(summary)
        elif format == ExportFormat.JSON:
            return self._export_summary_json(summary)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_summary(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from logs"""
        total = len(logs)
        
        # Count by action type
        action_counts = {}
        for log in logs:
            action = log.get('action_type', 'unknown')
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Count by status
        status_counts = {}
        for log in logs:
            status = log.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by agent
        agent_counts = {}
        for log in logs:
            agent = log.get('agent_id', 'unknown')
            if agent:
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        # Count errors
        error_count = sum(1 for log in logs if log.get('status') == 'error')
        
        return {
            'total_records': total,
            'date_range': {
                'start': logs[0].get('timestamp') if logs else None,
                'end': logs[-1].get('timestamp') if logs else None
            },
            'action_type_counts': action_counts,
            'status_counts': status_counts,
            'agent_counts': agent_counts,
            'error_count': error_count,
            'success_count': total - error_count,
            'error_rate': (error_count / total * 100) if total > 0 else 0
        }
    
    def _export_summary_csv(self, summary: Dict[str, Any]) -> str:
        """Export summary as CSV"""
        output = StringIO()
        
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Metric', 'Value'])
        
        # Basic stats
        writer.writerow(['Total Records', summary['total_records']])
        writer.writerow(['Error Count', summary['error_count']])
        writer.writerow(['Success Count', summary['success_count']])
        writer.writerow(['Error Rate (%)', f"{summary['error_rate']:.2f}"])
        
        # Action type counts
        writer.writerow([])
        writer.writerow(['Action Type', 'Count'])
        for action, count in summary['action_type_counts'].items():
            writer.writerow([action, count])
        
        # Status counts
        writer.writerow([])
        writer.writerow(['Status', 'Count'])
        for status, count in summary['status_counts'].items():
            writer.writerow([status, count])
        
        # Agent counts
        writer.writerow([])
        writer.writerow(['Agent ID', 'Count'])
        for agent, count in summary['agent_counts'].items():
            writer.writerow([agent, count])
        
        return output.getvalue()
    
    def _export_summary_json(self, summary: Dict[str, Any]) -> str:
        """Export summary as JSON"""
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'summary': summary
        }
        
        return json.dumps(export_data, indent=2, default=str)

