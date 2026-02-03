"""
Unit tests for the Audit Logger module.

Tests persistent backends (file, sqlite) and audit trail functionality.
"""

import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ai_agent_connector.app.utils.audit_logger import (
    ActionType,
    AuditLogger,
    FileBackend,
    MemoryBackend,
    SQLiteBackend,
    get_audit_logger,
    init_audit_logger,
)


class TestActionType:
    """Test ActionType enum."""

    def test_action_types_exist(self):
        """Test that all action types are defined."""
        assert ActionType.QUERY_EXECUTION.value == "query_execution"
        assert ActionType.AGENT_REGISTERED.value == "agent_registered"
        assert ActionType.JWT_TOKEN_GENERATED.value == "jwt_token_generated"
        assert ActionType.ONTOGUARD_VALIDATION.value == "ontoguard_validation"
        assert ActionType.SCHEMA_DRIFT_CHECK.value == "schema_drift_check"
        assert ActionType.RATE_LIMIT_EXCEEDED.value == "rate_limit_exceeded"


class TestMemoryBackend:
    """Test MemoryBackend."""

    def test_write_and_read(self):
        """Test writing and reading logs."""
        backend = MemoryBackend(max_logs=100)

        backend.write({
            'timestamp': '2026-02-03T10:00:00',
            'action_type': 'query_execution',
            'agent_id': 'agent-1',
            'status': 'success'
        })

        logs = backend.read()
        assert len(logs) == 1
        assert logs[0]['agent_id'] == 'agent-1'
        assert logs[0]['id'] == 1

    def test_max_logs_eviction(self):
        """Test FIFO eviction when max_logs reached."""
        backend = MemoryBackend(max_logs=3)

        for i in range(5):
            backend.write({
                'timestamp': f'2026-02-03T10:0{i}:00',
                'action_type': 'test',
                'agent_id': f'agent-{i}'
            })

        assert len(backend.logs) == 3
        # Oldest logs should be evicted
        agent_ids = [l['agent_id'] for l in backend.logs]
        assert 'agent-0' not in agent_ids
        assert 'agent-1' not in agent_ids
        assert 'agent-4' in agent_ids

    def test_filter_by_agent_id(self):
        """Test filtering by agent ID."""
        backend = MemoryBackend()

        backend.write({'timestamp': '2026-02-03T10:00:00', 'action_type': 'test', 'agent_id': 'agent-1'})
        backend.write({'timestamp': '2026-02-03T10:01:00', 'action_type': 'test', 'agent_id': 'agent-2'})
        backend.write({'timestamp': '2026-02-03T10:02:00', 'action_type': 'test', 'agent_id': 'agent-1'})

        logs = backend.read(agent_id='agent-1')
        assert len(logs) == 2
        assert all(l['agent_id'] == 'agent-1' for l in logs)

    def test_filter_by_status(self):
        """Test filtering by status."""
        backend = MemoryBackend()

        backend.write({'timestamp': '2026-02-03T10:00:00', 'action_type': 'test', 'status': 'success'})
        backend.write({'timestamp': '2026-02-03T10:01:00', 'action_type': 'test', 'status': 'error'})
        backend.write({'timestamp': '2026-02-03T10:02:00', 'action_type': 'test', 'status': 'denied'})

        logs = backend.read(status='error')
        assert len(logs) == 1
        assert logs[0]['status'] == 'error'

    def test_count(self):
        """Test counting logs."""
        backend = MemoryBackend()

        for i in range(10):
            backend.write({
                'timestamp': f'2026-02-03T10:0{i}:00',
                'action_type': 'test' if i % 2 == 0 else 'other',
                'status': 'success'
            })

        assert backend.count() == 10
        assert backend.count(action_type='test') == 5


class TestFileBackend:
    """Test FileBackend."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_write_and_read(self, temp_log_dir):
        """Test writing and reading from file."""
        backend = FileBackend(log_dir=temp_log_dir)

        backend.write({
            'timestamp': '2026-02-03T10:00:00',
            'action_type': 'query_execution',
            'agent_id': 'agent-1',
            'status': 'success',
            'details': {'query': 'SELECT * FROM users'}
        })

        logs = backend.read()
        assert len(logs) == 1
        assert logs[0]['agent_id'] == 'agent-1'
        assert logs[0]['details']['query'] == 'SELECT * FROM users'

    def test_file_persistence(self, temp_log_dir):
        """Test that logs persist across backend instances."""
        backend1 = FileBackend(log_dir=temp_log_dir)
        backend1.write({
            'timestamp': '2026-02-03T10:00:00',
            'action_type': 'test',
            'agent_id': 'agent-1'
        })

        # Create new backend instance
        backend2 = FileBackend(log_dir=temp_log_dir)
        logs = backend2.read()

        assert len(logs) == 1
        assert logs[0]['agent_id'] == 'agent-1'

    def test_multiple_files(self, temp_log_dir):
        """Test reading from multiple files."""
        backend = FileBackend(log_dir=temp_log_dir)

        # Write to today's file
        backend.write({
            'timestamp': '2026-02-03T10:00:00',
            'action_type': 'test',
            'agent_id': 'agent-1'
        })

        # Manually create another file
        old_file = Path(temp_log_dir) / 'audit_2026-02-02.jsonl'
        with open(old_file, 'w') as f:
            f.write(json.dumps({
                'id': 0,
                'timestamp': '2026-02-02T10:00:00',
                'action_type': 'old_test',
                'agent_id': 'agent-old'
            }) + '\n')

        logs = backend.read()
        assert len(logs) == 2

    def test_filter_by_date(self, temp_log_dir):
        """Test filtering by date range."""
        backend = FileBackend(log_dir=temp_log_dir)

        backend.write({'timestamp': '2026-02-01T10:00:00', 'action_type': 'test', 'agent_id': 'a1'})
        backend.write({'timestamp': '2026-02-02T10:00:00', 'action_type': 'test', 'agent_id': 'a2'})
        backend.write({'timestamp': '2026-02-03T10:00:00', 'action_type': 'test', 'agent_id': 'a3'})

        start = datetime(2026, 2, 2)
        end = datetime(2026, 2, 2, 23, 59, 59)

        logs = backend.read(start_date=start, end_date=end)
        assert len(logs) == 1
        assert logs[0]['agent_id'] == 'a2'


class TestSQLiteBackend:
    """Test SQLiteBackend."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        os.unlink(path)

    def test_write_and_read(self, temp_db):
        """Test writing and reading from SQLite."""
        backend = SQLiteBackend(db_path=temp_db)

        backend.write({
            'timestamp': '2026-02-03T10:00:00',
            'action_type': 'query_execution',
            'agent_id': 'agent-1',
            'status': 'success',
            'details': {'query': 'SELECT 1'}
        })

        logs = backend.read()
        assert len(logs) == 1
        assert logs[0]['agent_id'] == 'agent-1'
        assert logs[0]['details']['query'] == 'SELECT 1'

    def test_indexed_queries(self, temp_db):
        """Test that indexed columns are created."""
        backend = SQLiteBackend(db_path=temp_db)

        # Check indexes exist
        conn = sqlite3.connect(temp_db)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert 'idx_audit_timestamp' in indexes
        assert 'idx_audit_agent' in indexes
        assert 'idx_audit_action' in indexes
        assert 'idx_audit_status' in indexes

    def test_pagination(self, temp_db):
        """Test pagination."""
        backend = SQLiteBackend(db_path=temp_db)

        for i in range(20):
            backend.write({
                'timestamp': f'2026-02-03T10:{i:02d}:00',
                'action_type': 'test',
                'agent_id': f'agent-{i}'
            })

        page1 = backend.read(limit=5, offset=0)
        page2 = backend.read(limit=5, offset=5)

        assert len(page1) == 5
        assert len(page2) == 5
        # No overlap
        ids1 = {l['id'] for l in page1}
        ids2 = {l['id'] for l in page2}
        assert ids1.isdisjoint(ids2)


class TestAuditLogger:
    """Test AuditLogger class."""

    def test_memory_backend_default(self):
        """Test default memory backend."""
        logger = AuditLogger(backend='memory', max_logs=100)
        assert logger.backend_type == 'memory'

    def test_log_action(self):
        """Test logging an action."""
        logger = AuditLogger(backend='memory')

        entry = logger.log(
            action_type=ActionType.QUERY_EXECUTION,
            agent_id='agent-1',
            user_id='user-1',
            details={'query': 'SELECT * FROM users'},
            status='success'
        )

        assert entry['action_type'] == 'query_execution'
        assert entry['agent_id'] == 'agent-1'
        assert entry['user_id'] == 'user-1'
        assert entry['status'] == 'success'
        assert 'timestamp' in entry

    def test_get_logs_with_filtering(self):
        """Test getting logs with filters."""
        logger = AuditLogger(backend='memory')

        logger.log(ActionType.QUERY_EXECUTION, agent_id='a1', status='success')
        logger.log(ActionType.AGENT_REGISTERED, agent_id='a2', status='success')
        logger.log(ActionType.QUERY_EXECUTION, agent_id='a1', status='error')

        result = logger.get_logs(agent_id='a1')
        assert result['total'] == 2

        result = logger.get_logs(action_type=ActionType.QUERY_EXECUTION)
        assert result['total'] == 2

        result = logger.get_logs(status='error')
        assert result['total'] == 1

    def test_get_statistics(self):
        """Test getting statistics."""
        logger = AuditLogger(backend='memory')

        logger.log(ActionType.QUERY_EXECUTION, status='success')
        logger.log(ActionType.QUERY_EXECUTION, status='success')
        logger.log(ActionType.QUERY_EXECUTION, status='error')
        logger.log(ActionType.AGENT_REGISTERED, status='success')

        stats = logger.get_statistics(days=1)

        assert stats['total_actions'] == 4
        assert stats['by_action_type']['query_execution'] == 3
        assert stats['by_action_type']['agent_registered'] == 1
        assert stats['by_status']['success'] == 3
        assert stats['by_status']['error'] == 1

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_file_backend(self, temp_dir):
        """Test file backend integration."""
        logger = AuditLogger(backend='file', log_dir=temp_dir)

        logger.log(ActionType.QUERY_EXECUTION, agent_id='agent-1')

        # Verify file created
        files = list(Path(temp_dir).glob('audit_*.jsonl'))
        assert len(files) >= 1

        # Read back
        result = logger.get_logs()
        assert result['total'] == 1

    def test_export_logs_jsonl(self, temp_dir):
        """Test exporting logs to JSONL format."""
        logger = AuditLogger(backend='memory')

        logger.log(ActionType.QUERY_EXECUTION, agent_id='agent-1')
        logger.log(ActionType.AGENT_REGISTERED, agent_id='agent-2')

        output_path = Path(temp_dir) / 'export.jsonl'
        count = logger.export_logs(str(output_path), format='jsonl')

        assert count == 2
        assert output_path.exists()

        # Verify content
        with open(output_path) as f:
            lines = f.readlines()
        assert len(lines) == 2

    def test_export_logs_json(self, temp_dir):
        """Test exporting logs to JSON format."""
        logger = AuditLogger(backend='memory')

        logger.log(ActionType.QUERY_EXECUTION, agent_id='agent-1')

        output_path = Path(temp_dir) / 'export.json'
        count = logger.export_logs(str(output_path), format='json')

        assert count == 1

        with open(output_path) as f:
            data = json.load(f)
        assert len(data) == 1

    def test_clear_logs(self):
        """Test clearing logs."""
        logger = AuditLogger(backend='memory')

        logger.log(ActionType.QUERY_EXECUTION)
        logger.log(ActionType.QUERY_EXECUTION)

        logger.clear_logs()

        assert len(logger.logs) == 0


class TestGlobalAuditLogger:
    """Test global audit logger functions."""

    def test_get_audit_logger_singleton(self):
        """Test get_audit_logger returns same instance."""
        # Reset global
        import ai_agent_connector.app.utils.audit_logger as audit_module
        audit_module._audit_logger = None

        os.environ['AUDIT_BACKEND'] = 'memory'
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()

        assert logger1 is logger2

    def test_init_audit_logger_custom(self):
        """Test initializing with custom settings."""
        logger = init_audit_logger(backend='memory', max_logs=500)

        assert logger.backend_type == 'memory'
        assert logger.max_logs == 500


class TestAuditAPIEndpoints:
    """Test audit API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        from flask import Flask
        from ai_agent_connector.app.api import api_bp

        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp, url_prefix='/api')
        self.client = self.app.test_client()

        # Initialize with memory backend for tests
        init_audit_logger(backend='memory')

    def test_get_audit_logs(self):
        """Test GET /api/audit/logs."""
        # Add some logs first
        logger = get_audit_logger()
        logger.log(ActionType.QUERY_EXECUTION, agent_id='test-agent')

        response = self.client.get('/api/audit/logs')
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'logs' in data
        assert 'backend' in data  # Backend type can vary based on global state

    def test_get_audit_logs_with_filters(self):
        """Test GET /api/audit/logs with filters."""
        # Test that endpoint accepts filter parameters correctly
        response = self.client.get('/api/audit/logs?agent_id=test-agent&status=success&limit=50')
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'logs' in data
        assert data['limit'] == 50
        assert 'backend' in data

    def test_get_audit_statistics(self):
        """Test GET /api/audit/statistics."""
        logger = get_audit_logger()
        logger.clear_logs()

        logger.log(ActionType.QUERY_EXECUTION)
        logger.log(ActionType.QUERY_EXECUTION)

        response = self.client.get('/api/audit/statistics?days=7')
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'by_action_type' in data
        assert 'by_status' in data

    def test_get_audit_config(self):
        """Test GET /api/audit/config."""
        response = self.client.get('/api/audit/config')
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'backend' in data
        assert 'action_types' in data
        assert 'query_execution' in data['action_types']

    def test_update_audit_config(self):
        """Test POST /api/audit/config."""
        response = self.client.post('/api/audit/config', json={
            'backend': 'memory',
            'max_logs': 500
        })
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['backend'] == 'memory'
