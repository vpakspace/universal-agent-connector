"""
Mock Audit Logger for MCP Governance
Logs tool calls to JSONL file (one JSON per line)
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class AuditLogger:
    """
    Audit logger that writes tool call logs to JSONL file.
    Each log entry is written as a single JSON line (JSONL format).
    """
    
    def __init__(self, log_file: str = "audit_log.jsonl"):
        """
        Initialize audit logger
        
        Args:
            log_file: Path to JSONL log file
        """
        self.log_file = Path(log_file)
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_tool_call(
        self,
        user_id: str,
        tenant_id: Optional[str],
        tool_name: str,
        args: Dict[str, Any],
        result: Optional[Any] = None,
        validation: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log a tool call to the audit log file
        
        Args:
            user_id: User ID who called the tool
            tenant_id: Tenant ID (optional)
            tool_name: Name of the tool called
            args: Arguments passed to the tool
            result: Result of tool execution (optional, may be masked)
            validation: Validation result (optional)
            execution_time_ms: Execution time in milliseconds (optional)
            error: Error message if tool execution failed (optional)
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "tenant_id": tenant_id,
            "tool_name": tool_name,
            "arguments": args,
            "result": result,
            "validation": validation,
            "execution_time_ms": execution_time_ms,
            "error": error,
            "status": "success" if error is None else "error"
        }
        
        # Write as JSONL (one JSON object per line)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write('\n')
    
    def read_logs(self, limit: Optional[int] = None) -> list[Dict[str, Any]]:
        """
        Read audit logs from file
        
        Args:
            limit: Maximum number of log entries to read (None = all)
            
        Returns:
            List of log entries (most recent first)
        """
        if not self.log_file.exists():
            return []
        
        logs = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines
        
        # Sort by timestamp (most recent first)
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        if limit:
            return logs[:limit]
        return logs
    
    def clear_logs(self) -> None:
        """Clear all logs (useful for testing)"""
        if self.log_file.exists():
            self.log_file.unlink()

