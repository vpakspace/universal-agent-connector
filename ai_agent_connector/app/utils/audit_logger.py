"""
Audit logging system for tracking queries and agent actions.

Supports multiple backends:
- Memory (default, limited buffer)
- File (JSON Lines, append-only)
- SQLite (structured queries)
"""

import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..utils.helpers import get_timestamp


class ActionType(Enum):
    """Types of actions that can be logged"""
    QUERY_EXECUTION = "query_execution"
    NATURAL_LANGUAGE_QUERY = "natural_language_query"
    AGENT_REGISTERED = "agent_registered"
    AGENT_REVOKED = "agent_revoked"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    PERMISSION_SET = "permission_set"
    PERMISSION_LISTED = "permission_listed"
    TABLES_LISTED = "tables_listed"
    AGENT_VIEWED = "agent_viewed"
    AGENTS_LISTED = "agents_listed"
    # JWT Authentication
    JWT_TOKEN_GENERATED = "jwt_token_generated"
    JWT_TOKEN_REVOKED = "jwt_token_revoked"
    # OntoGuard
    ONTOGUARD_VALIDATION = "ontoguard_validation"
    ONTOGUARD_DENIED = "ontoguard_denied"
    # Schema Drift
    SCHEMA_DRIFT_CHECK = "schema_drift_check"
    SCHEMA_DRIFT_CRITICAL = "schema_drift_critical"
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


class AuditBackend:
    """Base class for audit log backends"""

    def write(self, entry: Dict[str, Any]) -> None:
        raise NotImplementedError

    def read(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        status: Optional[str] = None,
        tenant_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def count(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        status: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> int:
        raise NotImplementedError

    def close(self) -> None:
        pass


class MemoryBackend(AuditBackend):
    """In-memory audit log storage (limited buffer)"""

    def __init__(self, max_logs: int = 10000):
        self.logs: List[Dict[str, Any]] = []
        self.max_logs = max_logs
        self._lock = threading.Lock()
        self._id_counter = 0

    def write(self, entry: Dict[str, Any]) -> None:
        with self._lock:
            self._id_counter += 1
            entry['id'] = self._id_counter
            self.logs.append(entry)

            # FIFO eviction
            if len(self.logs) > self.max_logs:
                self.logs.pop(0)

    def read(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        status: Optional[str] = None,
        tenant_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        with self._lock:
            filtered = self.logs.copy()

        if agent_id:
            filtered = [l for l in filtered if l.get('agent_id') == agent_id]
        if action_type:
            filtered = [l for l in filtered if l.get('action_type') == action_type]
        if status:
            filtered = [l for l in filtered if l.get('status') == status]
        if tenant_id:
            filtered = [l for l in filtered if l.get('tenant_id') == tenant_id]
        if start_date:
            start_str = start_date.isoformat()
            filtered = [l for l in filtered if l.get('timestamp', '') >= start_str]
        if end_date:
            end_str = end_date.isoformat()
            filtered = [l for l in filtered if l.get('timestamp', '') <= end_str]

        # Sort by timestamp descending
        filtered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return filtered[offset:offset + limit]

    def count(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        status: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> int:
        with self._lock:
            filtered = self.logs.copy()

        if agent_id:
            filtered = [l for l in filtered if l.get('agent_id') == agent_id]
        if action_type:
            filtered = [l for l in filtered if l.get('action_type') == action_type]
        if status:
            filtered = [l for l in filtered if l.get('status') == status]
        if tenant_id:
            filtered = [l for l in filtered if l.get('tenant_id') == tenant_id]

        return len(filtered)


class FileBackend(AuditBackend):
    """JSON Lines file-based audit log storage with rotation"""

    def __init__(
        self,
        log_dir: str = "logs/audit",
        max_file_size_mb: int = 100,
        max_files: int = 10
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.max_files = max_files
        self._lock = threading.Lock()
        self._current_file: Optional[Path] = None
        self._id_counter = self._load_last_id()

    def _get_current_file(self) -> Path:
        """Get or create current log file"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"audit_{today}.jsonl"

        # Check if rotation needed
        if log_file.exists() and log_file.stat().st_size >= self.max_file_size:
            # Create new file with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            log_file = self.log_dir / f"audit_{timestamp}.jsonl"

        return log_file

    def _load_last_id(self) -> int:
        """Load last ID from existing files"""
        max_id = 0
        for log_file in sorted(self.log_dir.glob("audit_*.jsonl"), reverse=True):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            max_id = max(max_id, entry.get('id', 0))
                        except json.JSONDecodeError:
                            continue
                if max_id > 0:
                    break
            except Exception:
                continue
        return max_id

    def _cleanup_old_files(self) -> None:
        """Remove oldest files if exceeding max_files"""
        files = sorted(self.log_dir.glob("audit_*.jsonl"))
        while len(files) > self.max_files:
            oldest = files.pop(0)
            try:
                oldest.unlink()
            except Exception:
                pass

    def write(self, entry: Dict[str, Any]) -> None:
        with self._lock:
            self._id_counter += 1
            entry['id'] = self._id_counter

            log_file = self._get_current_file()
            with open(log_file, 'a') as f:
                f.write(json.dumps(entry, default=str) + '\n')

            self._cleanup_old_files()

    def read(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        status: Optional[str] = None,
        tenant_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        results = []

        # Read from all files (newest first)
        files = sorted(self.log_dir.glob("audit_*.jsonl"), reverse=True)

        for log_file in files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())

                            # Apply filters
                            if agent_id and entry.get('agent_id') != agent_id:
                                continue
                            if action_type and entry.get('action_type') != action_type:
                                continue
                            if status and entry.get('status') != status:
                                continue
                            if tenant_id and entry.get('tenant_id') != tenant_id:
                                continue
                            if start_date:
                                ts = entry.get('timestamp', '')
                                if ts < start_date.isoformat():
                                    continue
                            if end_date:
                                ts = entry.get('timestamp', '')
                                if ts > end_date.isoformat():
                                    continue

                            results.append(entry)
                        except json.JSONDecodeError:
                            continue
            except Exception:
                continue

        # Sort by timestamp descending
        results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return results[offset:offset + limit]

    def count(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        status: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> int:
        count = 0

        for log_file in self.log_dir.glob("audit_*.jsonl"):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())

                            if agent_id and entry.get('agent_id') != agent_id:
                                continue
                            if action_type and entry.get('action_type') != action_type:
                                continue
                            if status and entry.get('status') != status:
                                continue
                            if tenant_id and entry.get('tenant_id') != tenant_id:
                                continue

                            count += 1
                        except json.JSONDecodeError:
                            continue
            except Exception:
                continue

        return count


class SQLiteBackend(AuditBackend):
    """SQLite-based audit log storage for structured queries"""

    def __init__(self, db_path: str = "logs/audit.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize database schema"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    agent_id TEXT,
                    user_id TEXT,
                    tenant_id TEXT,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    details TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_logs(timestamp DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_agent
                ON audit_logs(agent_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_action
                ON audit_logs(action_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_status
                ON audit_logs(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_tenant
                ON audit_logs(tenant_id)
            """)
            conn.commit()

            # Add tenant_id column if it doesn't exist (migration for existing DBs)
            try:
                conn.execute("SELECT tenant_id FROM audit_logs LIMIT 1")
            except sqlite3.OperationalError:
                conn.execute("ALTER TABLE audit_logs ADD COLUMN tenant_id TEXT")
                conn.commit()

    def write(self, entry: Dict[str, Any]) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO audit_logs
                    (timestamp, action_type, agent_id, user_id, tenant_id, status, error_message, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.get('timestamp'),
                    entry.get('action_type'),
                    entry.get('agent_id'),
                    entry.get('user_id'),
                    entry.get('tenant_id'),
                    entry.get('status', 'success'),
                    entry.get('error_message'),
                    json.dumps(entry.get('details', {}))
                ))
                conn.commit()

    def read(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        status: Optional[str] = None,
        tenant_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params: List[Any] = []

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
        if action_type:
            query += " AND action_type = ?"
            params.append(action_type)
        if status:
            query += " AND status = ?"
            params.append(status)
        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        results = []
        for row in rows:
            entry = dict(row)
            # Parse details JSON
            if entry.get('details'):
                try:
                    entry['details'] = json.loads(entry['details'])
                except json.JSONDecodeError:
                    entry['details'] = {}
            results.append(entry)

        return results

    def count(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        status: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> int:
        query = "SELECT COUNT(*) FROM audit_logs WHERE 1=1"
        params: List[Any] = []

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
        if action_type:
            query += " AND action_type = ?"
            params.append(action_type)
        if status:
            query += " AND status = ?"
            params.append(status)
        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]

    def close(self) -> None:
        pass  # SQLite connections are managed per-operation


class AuditLogger:
    """
    Manages audit logs for system activity.

    Supports multiple backends:
    - memory: In-memory buffer (default, limited)
    - file: JSON Lines files with rotation
    - sqlite: SQLite database for structured queries
    """

    def __init__(
        self,
        backend: str = "memory",
        max_logs: int = 10000,
        log_dir: str = "logs/audit",
        db_path: str = "logs/audit.db",
        max_file_size_mb: int = 100,
        max_files: int = 10
    ):
        """
        Initialize audit logger.

        Args:
            backend: Backend type ('memory', 'file', 'sqlite')
            max_logs: Max logs for memory backend
            log_dir: Directory for file backend
            db_path: Database path for SQLite backend
            max_file_size_mb: Max file size before rotation (file backend)
            max_files: Max number of log files to keep (file backend)
        """
        self.backend_type = backend

        if backend == "file":
            self._backend = FileBackend(
                log_dir=log_dir,
                max_file_size_mb=max_file_size_mb,
                max_files=max_files
            )
        elif backend == "sqlite":
            self._backend = SQLiteBackend(db_path=db_path)
        else:
            self._backend = MemoryBackend(max_logs=max_logs)

        # Keep memory buffer for quick access
        self.logs: List[Dict[str, Any]] = []
        self.max_logs = max_logs

    def log(
        self,
        action_type: ActionType,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log an action.

        Args:
            action_type: Type of action being logged
            agent_id: Agent ID involved in the action
            user_id: User ID who performed the action
            tenant_id: Tenant ID for multi-tenancy support
            details: Additional details about the action
            status: Status of the action (success, error, denied)
            error_message: Error message if status is error

        Returns:
            Dict containing the log entry
        """
        log_entry = {
            'timestamp': get_timestamp(),
            'action_type': action_type.value,
            'agent_id': agent_id,
            'user_id': user_id,
            'tenant_id': tenant_id,
            'status': status,
            'details': details or {},
            'error_message': error_message
        }

        # Write to backend
        self._backend.write(log_entry)

        # Also keep in memory for quick access
        self.logs.append(log_entry)
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)

        return log_entry

    def get_logs(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[Union[ActionType, str]] = None,
        status: Optional[str] = None,
        tenant_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Retrieve audit logs with filtering.

        Args:
            agent_id: Filter by agent ID
            action_type: Filter by action type
            status: Filter by status
            tenant_id: Filter by tenant ID (for multi-tenancy)
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of logs to return
            offset: Number of logs to skip

        Returns:
            Dict containing filtered logs and metadata
        """
        action_type_str = None
        if action_type:
            action_type_str = action_type.value if isinstance(action_type, ActionType) else action_type

        logs = self._backend.read(
            agent_id=agent_id,
            action_type=action_type_str,
            status=status,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        total = self._backend.count(
            agent_id=agent_id,
            action_type=action_type_str,
            status=status,
            tenant_id=tenant_id
        )

        return {
            'logs': logs,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total
        }

    def get_log_by_id(self, log_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific log entry by ID.

        Args:
            log_id: Log entry ID

        Returns:
            Log entry or None if not found
        """
        # For memory backend, search in-memory
        for log in self.logs:
            if log.get('id') == log_id:
                return log

        # For persistent backends, search with limit 1
        if self.backend_type in ("file", "sqlite"):
            logs = self._backend.read(limit=10000)
            for log in logs:
                if log.get('id') == log_id:
                    return log

        return None

    def clear_logs(self) -> None:
        """Clear all logs (useful for testing)"""
        self.logs.clear()
        if isinstance(self._backend, MemoryBackend):
            self._backend.logs.clear()

    def get_statistics(
        self,
        agent_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get statistics about logged actions.

        Args:
            agent_id: Filter statistics by agent ID
            days: Number of days to include in statistics

        Returns:
            Dict containing statistics
        """
        start_date = datetime.now() - timedelta(days=days)

        logs = self._backend.read(
            agent_id=agent_id,
            start_date=start_date,
            limit=10000
        )

        stats = {
            'total_actions': len(logs),
            'period_days': days,
            'by_action_type': {},
            'by_status': {},
            'by_day': {},
            'recent_actions': []
        }

        # Count by action type
        for log in logs:
            action_type = log.get('action_type', 'unknown')
            stats['by_action_type'][action_type] = stats['by_action_type'].get(action_type, 0) + 1

        # Count by status
        for log in logs:
            status = log.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

        # Count by day
        for log in logs:
            ts = log.get('timestamp', '')[:10]  # YYYY-MM-DD
            stats['by_day'][ts] = stats['by_day'].get(ts, 0) + 1

        # Get recent actions (last 10)
        stats['recent_actions'] = logs[:10]

        return stats

    def export_logs(
        self,
        output_path: str,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "jsonl"
    ) -> int:
        """
        Export logs to a file.

        Args:
            output_path: Path to output file
            agent_id: Filter by agent ID
            start_date: Filter by start date
            end_date: Filter by end date
            format: Output format ('jsonl' or 'json')

        Returns:
            Number of logs exported
        """
        logs = self._backend.read(
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000000  # Export all
        )

        with open(output_path, 'w') as f:
            if format == "json":
                json.dump(logs, f, indent=2, default=str)
            else:  # jsonl
                for log in logs:
                    f.write(json.dumps(log, default=str) + '\n')

        return len(logs)

    def close(self) -> None:
        """Close backend connections"""
        self._backend.close()


# Global instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        # Default to file backend for persistence
        backend = os.environ.get('AUDIT_BACKEND', 'file')
        _audit_logger = AuditLogger(backend=backend)
    return _audit_logger


def init_audit_logger(
    backend: str = "file",
    **kwargs
) -> AuditLogger:
    """Initialize global audit logger with custom settings"""
    global _audit_logger
    _audit_logger = AuditLogger(backend=backend, **kwargs)
    return _audit_logger
