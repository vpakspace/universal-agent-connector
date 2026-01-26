"""
Tests for Automated Plugin Validation Story

Story: As a Contributor, I want automated plugin validation (security scan, API compatibility),
       so that my submission is approved quickly.

Acceptance Criteria:
- CI/CD pipeline
- Security checks
- Auto-testing
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from flask import Flask
from main import create_app
from ai_agent_connector.app.db.plugin import (
    DatabasePlugin,
    PluginRegistry,
    get_plugin_registry,
)
from ai_agent_connector.app.db.base_connector import BaseDatabaseConnector
import tempfile
import os
import json
from pathlib import Path
import ast
import subprocess


# ============================================================================
# Mock Plugin Classes for Testing
# ============================================================================

class MockConnector(BaseDatabaseConnector):
    """Mock connector for testing"""
    
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self._is_connected = False
    
    def connect(self):
        self._is_connected = True
        return True
    
    def disconnect(self):
        self._is_connected = False
    
    def execute_query(self, query, params=None, fetch=True, as_dict=False):
        if not self._is_connected:
            raise ConnectionError("Not connected")
        return [] if fetch else None
    
    @property
    def is_connected(self):
        return self._is_connected
    
    def get_database_info(self):
        return {'type': self.config.get('database_type', 'test_db'), 'version': '1.0.0'}


class ValidPlugin(DatabasePlugin):
    """Valid plugin for testing"""
    
    @property
    def plugin_name(self):
        return "valid_plugin"
    
    @property
    def plugin_version(self):
        return "1.0.0"
    
    @property
    def database_type(self):
        return "valid_db"
    
    @property
    def display_name(self):
        return "Valid Database"
    
    @property
    def description(self):
        return "A valid plugin"
    
    @property
    def author(self):
        return "Test Author"
    
    @property
    def required_config_keys(self):
        return ['host', 'database']
    
    def create_connector(self, config):
        return MockConnector(config)
    
    def detect_database_type(self, config):
        if config.get('type', '').lower() == 'valid_db':
            return self.database_type
        return None


class VulnerablePlugin(DatabasePlugin):
    """Plugin with potential security vulnerabilities"""
    
    @property
    def plugin_name(self):
        return "vulnerable_plugin"
    
    @property
    def plugin_version(self):
        return "1.0.0"
    
    @property
    def database_type(self):
        return "vulnerable_db"
    
    @property
    def display_name(self):
        return "Vulnerable Database"
    
    @property
    def required_config_keys(self):
        return ['host']
    
    def create_connector(self, config):
        # Contains potential security issue: eval usage
        import subprocess
        subprocess.call(config.get('command', 'ls'))  # Dangerous!
        return MockConnector(config)
    
    def detect_database_type(self, config):
        return self.database_type if config.get('type') == 'vulnerable_db' else None


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_plugin_registry():
    """Reset plugin registry before and after each test"""
    registry = get_plugin_registry()
    original_plugins = dict(registry._plugins)
    original_paths = dict(registry._plugin_paths)
    
    registry._plugins.clear()
    registry._plugin_paths.clear()
    
    yield
    
    registry._plugins.clear()
    registry._plugin_paths.clear()
    registry._plugins.update(original_plugins)
    registry._plugin_paths.update(original_paths)


@pytest.fixture
def client():
    """Create test client"""
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_plugin_file():
    """Create a sample plugin file for testing"""
    plugin_code = '''
from ai_agent_connector.app.db.plugin import DatabasePlugin
from ai_agent_connector.app.db.base_connector import BaseDatabaseConnector

class SampleConnector(BaseDatabaseConnector):
    def connect(self):
        return True
    
    def disconnect(self):
        pass
    
    def execute_query(self, query, params=None, fetch=True, as_dict=False):
        return []

class SamplePlugin(DatabasePlugin):
    @property
    def plugin_name(self):
        return "sample_plugin"
    
    @property
    def plugin_version(self):
        return "1.0.0"
    
    @property
    def database_type(self):
        return "sample_db"
    
    @property
    def display_name(self):
        return "Sample Database"
    
    @property
    def required_config_keys(self):
        return ['host']
    
    def create_connector(self, config):
        return SampleConnector(config)
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(plugin_code)
        temp_file = f.name
    
    yield temp_file
    
    os.unlink(temp_file)


@pytest.fixture
def vulnerable_plugin_file():
    """Create a plugin file with security vulnerabilities"""
    plugin_code = '''
import os
import subprocess
from ai_agent_connector.app.db.plugin import DatabasePlugin
from ai_agent_connector.app.db.base_connector import BaseDatabaseConnector

class VulnerableConnector(BaseDatabaseConnector):
    def connect(self):
        # Security issue: command injection
        command = self.config.get('command', 'ls')
        os.system(command)  # Dangerous!
        return True
    
    def disconnect(self):
        pass
    
    def execute_query(self, query, params=None, fetch=True, as_dict=False):
        # Security issue: eval usage
        result = eval(query)  # Dangerous!
        return result

class VulnerablePlugin(DatabasePlugin):
    @property
    def plugin_name(self):
        return "vulnerable_plugin"
    
    def create_connector(self, config):
        return VulnerableConnector(config)
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(plugin_code)
        temp_file = f.name
    
    yield temp_file
    
    os.unlink(temp_file)


# ============================================================================
# CI/CD Pipeline Tests
# ============================================================================

class TestPluginValidationCICD:
    """Test cases for CI/CD pipeline integration"""
    
    def test_validate_plugin_on_submission(self, client, sample_plugin_file):
        """Test that plugin validation is triggered on submission"""
        with open(sample_plugin_file, 'rb') as f:
            response = client.post('/api/plugins/validate/submit', 
                                 data={'plugin_file': f},
                                 content_type='multipart/form-data')
        
        assert response.status_code in [200, 202]  # Accepted for processing
        data = response.get_json()
        assert 'validation_id' in data or 'job_id' in data
        assert 'status' in data
    
    def test_validation_pipeline_status(self, client):
        """Test checking validation pipeline status"""
        validation_id = 'test-validation-123'
        
        with patch('ai_agent_connector.app.api.routes.get_validation_status') as mock_status:
            mock_status.return_value = {
                'validation_id': validation_id,
                'status': 'in_progress',
                'stages': {
                    'security_scan': 'completed',
                    'api_compatibility': 'in_progress',
                    'auto_tests': 'pending'
                }
            }
            
            response = client.get(f'/api/plugins/validate/status/{validation_id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'in_progress'
            assert 'stages' in data
    
    def test_validation_pipeline_completed(self, client):
        """Test validation pipeline completion"""
        validation_id = 'test-validation-123'
        
        with patch('ai_agent_connector.app.api.routes.get_validation_status') as mock_status:
            mock_status.return_value = {
                'validation_id': validation_id,
                'status': 'completed',
                'stages': {
                    'security_scan': 'passed',
                    'api_compatibility': 'passed',
                    'auto_tests': 'passed'
                },
                'results': {
                    'security_scan': {'vulnerabilities': 0, 'warnings': 2},
                    'api_compatibility': {'compatible': True, 'issues': []},
                    'auto_tests': {'passed': 10, 'failed': 0}
                }
            }
            
            response = client.get(f'/api/plugins/validate/status/{validation_id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'completed'
            assert all(stage == 'passed' for stage in data['stages'].values())
    
    def test_validation_pipeline_failed(self, client):
        """Test validation pipeline failure"""
        validation_id = 'test-validation-123'
        
        with patch('ai_agent_connector.app.api.routes.get_validation_status') as mock_status:
            mock_status.return_value = {
                'validation_id': validation_id,
                'status': 'failed',
                'stages': {
                    'security_scan': 'failed',
                    'api_compatibility': 'passed',
                    'auto_tests': 'pending'
                },
                'errors': ['Security scan found critical vulnerabilities']
            }
            
            response = client.get(f'/api/plugins/validate/status/{validation_id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'failed'
            assert 'errors' in data
    
    def test_validation_webhook_notification(self, client):
        """Test webhook notification on validation completion"""
        validation_id = 'test-validation-123'
        
        with patch('ai_agent_connector.app.api.routes.trigger_validation_webhook') as mock_webhook:
            mock_webhook.return_value = {'sent': True}
            
            response = client.post(f'/api/plugins/validate/{validation_id}/notify', json={
                'webhook_url': 'https://example.com/webhook'
            })
            
            assert response.status_code == 200
            mock_webhook.assert_called_once()
    
    def test_validation_logs_retrieval(self, client):
        """Test retrieving validation logs"""
        validation_id = 'test-validation-123'
        
        with patch('ai_agent_connector.app.api.routes.get_validation_logs') as mock_logs:
            mock_logs.return_value = {
                'logs': [
                    {'stage': 'security_scan', 'level': 'info', 'message': 'Scan started'},
                    {'stage': 'security_scan', 'level': 'warning', 'message': 'Minor issue found'},
                    {'stage': 'api_compatibility', 'level': 'info', 'message': 'Compatibility check passed'}
                ]
            }
            
            response = client.get(f'/api/plugins/validate/{validation_id}/logs')
            assert response.status_code == 200
            data = response.get_json()
            assert 'logs' in data
            assert len(data['logs']) > 0
    
    def test_validation_retry_failed_stage(self, client):
        """Test retrying a failed validation stage"""
        validation_id = 'test-validation-123'
        
        with patch('ai_agent_connector.app.api.routes.retry_validation_stage') as mock_retry:
            mock_retry.return_value = {'success': True, 'new_validation_id': 'test-validation-456'}
            
            response = client.post(f'/api/plugins/validate/{validation_id}/retry', json={
                'stage': 'auto_tests'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ============================================================================
# Security Check Tests
# ============================================================================

class TestPluginSecurityValidation:
    """Test cases for security scanning and validation"""
    
    def test_security_scan_dangerous_functions(self, client, vulnerable_plugin_file):
        """Test security scan detects dangerous functions (eval, exec, os.system)"""
        with patch('ai_agent_connector.app.api.routes.scan_plugin_security') as mock_scan:
            mock_scan.return_value = {
                'status': 'failed',
                'vulnerabilities': [
                    {
                        'type': 'dangerous_function',
                        'severity': 'high',
                        'function': 'eval',
                        'line': 15,
                        'message': 'Use of eval() detected'
                    },
                    {
                        'type': 'dangerous_function',
                        'severity': 'high',
                        'function': 'os.system',
                        'line': 10,
                        'message': 'Use of os.system() detected'
                    }
                ],
                'warnings': [],
                'score': 30  # Low security score
            }
            
            with open(vulnerable_plugin_file, 'rb') as f:
                response = client.post('/api/plugins/validate/security',
                                     data={'plugin_file': f},
                                     content_type='multipart/form-data')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'failed'
            assert len(data['vulnerabilities']) >= 2
    
    def test_security_scan_sql_injection(self, client):
        """Test security scan detects potential SQL injection"""
        plugin_code = '''
def execute_query(self, query, params=None):
    # Vulnerable: direct string concatenation
    sql = "SELECT * FROM users WHERE id = " + query  # SQL injection risk
    return self.connection.execute(sql)
'''
        
        with patch('ai_agent_connector.app.api.routes.scan_plugin_security') as mock_scan:
            mock_scan.return_value = {
                'status': 'failed',
                'vulnerabilities': [
                    {
                        'type': 'sql_injection',
                        'severity': 'critical',
                        'line': 3,
                        'message': 'Potential SQL injection: string concatenation in SQL query'
                    }
                ]
            }
            
            response = client.post('/api/plugins/validate/security',
                                 json={'plugin_code': plugin_code})
            
            assert response.status_code == 200
            data = response.get_json()
            assert any(v['type'] == 'sql_injection' for v in data.get('vulnerabilities', []))
    
    def test_security_scan_command_injection(self, client):
        """Test security scan detects command injection"""
        plugin_code = '''
import subprocess
def connect(self, config):
    host = config.get('host')
    subprocess.call(f"ping {host}")  # Command injection risk
'''
        
        with patch('ai_agent_connector.app.api.routes.scan_plugin_security') as mock_scan:
            mock_scan.return_value = {
                'status': 'warning',
                'vulnerabilities': [],
                'warnings': [
                    {
                        'type': 'command_injection',
                        'severity': 'medium',
                        'line': 4,
                        'message': 'Potential command injection: user input in subprocess call'
                    }
                ]
            }
            
            response = client.post('/api/plugins/validate/security',
                                 json={'plugin_code': plugin_code})
            
            assert response.status_code == 200
            data = response.get_json()
            assert any(w['type'] == 'command_injection' for w in data.get('warnings', []))
    
    def test_security_scan_hardcoded_secrets(self, client):
        """Test security scan detects hardcoded secrets"""
        plugin_code = '''
API_KEY = "sk-1234567890abcdef"
PASSWORD = "admin123"
DATABASE_URL = "postgresql://user:password@localhost/db"
'''
        
        with patch('ai_agent_connector.app.api.routes.scan_plugin_security') as mock_scan:
            mock_scan.return_value = {
                'status': 'failed',
                'vulnerabilities': [
                    {
                        'type': 'hardcoded_secret',
                        'severity': 'high',
                        'line': 2,
                        'message': 'Hardcoded API key detected'
                    },
                    {
                        'type': 'hardcoded_secret',
                        'severity': 'high',
                        'line': 3,
                        'message': 'Hardcoded password detected'
                    }
                ]
            }
            
            response = client.post('/api/plugins/validate/security',
                                 json={'plugin_code': plugin_code})
            
            assert response.status_code == 200
            data = response.get_json()
            assert len([v for v in data.get('vulnerabilities', []) if v['type'] == 'hardcoded_secret']) >= 2
    
    def test_security_scan_dependency_vulnerabilities(self, client):
        """Test security scan checks for vulnerable dependencies"""
        with patch('ai_agent_connector.app.api.routes.scan_plugin_dependencies') as mock_scan:
            mock_scan.return_value = {
                'status': 'warning',
                'vulnerabilities': [
                    {
                        'package': 'requests',
                        'version': '2.20.0',
                        'severity': 'high',
                        'cve': 'CVE-2020-25695',
                        'description': 'HTTP header injection vulnerability'
                    }
                ]
            }
            
            response = client.post('/api/plugins/validate/security/dependencies',
                                 json={'dependencies': {'requests': '2.20.0'}})
            
            assert response.status_code == 200
            data = response.get_json()
            assert len(data.get('vulnerabilities', [])) > 0
            assert data['vulnerabilities'][0]['severity'] == 'high'
    
    def test_security_scan_pass(self, client, sample_plugin_file):
        """Test security scan passes for clean plugin"""
        with patch('ai_agent_connector.app.api.routes.scan_plugin_security') as mock_scan:
            mock_scan.return_value = {
                'status': 'passed',
                'vulnerabilities': [],
                'warnings': [],
                'score': 95
            }
            
            with open(sample_plugin_file, 'rb') as f:
                response = client.post('/api/plugins/validate/security',
                                     data={'plugin_file': f},
                                     content_type='multipart/form-data')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'passed'
            assert len(data['vulnerabilities']) == 0
    
    def test_security_scan_severity_levels(self, client):
        """Test security scan categorizes issues by severity"""
        with patch('ai_agent_connector.app.api.routes.scan_plugin_security') as mock_scan:
            mock_scan.return_value = {
                'status': 'failed',
                'vulnerabilities': [
                    {'severity': 'critical', 'type': 'sql_injection'},
                    {'severity': 'high', 'type': 'eval_usage'},
                    {'severity': 'medium', 'type': 'weak_encryption'},
                    {'severity': 'low', 'type': 'deprecated_function'}
                ],
                'severity_summary': {
                    'critical': 1,
                    'high': 1,
                    'medium': 1,
                    'low': 1
                }
            }
            
            response = client.post('/api/plugins/validate/security',
                                 json={'plugin_code': 'test'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'severity_summary' in data
            assert data['severity_summary']['critical'] == 1


# ============================================================================
# API Compatibility Tests
# ============================================================================

class TestPluginAPICompatibility:
    """Test cases for API compatibility validation"""
    
    def test_api_compatibility_check_required_methods(self, client, sample_plugin_file):
        """Test API compatibility checks for required DatabasePlugin methods"""
        with patch('ai_agent_connector.app.api.routes.validate_api_compatibility') as mock_validate:
            mock_validate.return_value = {
                'compatible': True,
                'issues': [],
                'required_methods': {
                    'plugin_name': 'present',
                    'plugin_version': 'present',
                    'database_type': 'present',
                    'display_name': 'present',
                    'create_connector': 'present'
                }
            }
            
            with open(sample_plugin_file, 'rb') as f:
                response = client.post('/api/plugins/validate/api-compatibility',
                                     data={'plugin_file': f},
                                     content_type='multipart/form-data')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['compatible'] is True
            assert len(data['issues']) == 0
    
    def test_api_compatibility_missing_methods(self, client):
        """Test API compatibility detects missing required methods"""
        incomplete_plugin_code = '''
class IncompletePlugin(DatabasePlugin):
    @property
    def plugin_name(self):
        return "test"
    # Missing other required methods
'''
        
        with patch('ai_agent_connector.app.api.routes.validate_api_compatibility') as mock_validate:
            mock_validate.return_value = {
                'compatible': False,
                'issues': [
                    {
                        'type': 'missing_method',
                        'method': 'plugin_version',
                        'severity': 'error'
                    },
                    {
                        'type': 'missing_method',
                        'method': 'database_type',
                        'severity': 'error'
                    },
                    {
                        'type': 'missing_method',
                        'method': 'create_connector',
                        'severity': 'error'
                    }
                ]
            }
            
            response = client.post('/api/plugins/validate/api-compatibility',
                                 json={'plugin_code': incomplete_plugin_code})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['compatible'] is False
            assert len(data['issues']) >= 3
    
    def test_api_compatibility_signature_validation(self, client):
        """Test API compatibility validates method signatures"""
        with patch('ai_agent_connector.app.api.routes.validate_api_compatibility') as mock_validate:
            mock_validate.return_value = {
                'compatible': False,
                'issues': [
                    {
                        'type': 'signature_mismatch',
                        'method': 'create_connector',
                        'expected': 'create_connector(self, config: Dict[str, Any])',
                        'actual': 'create_connector(self, config, extra_param)',
                        'severity': 'error'
                    }
                ]
            }
            
            response = client.post('/api/plugins/validate/api-compatibility',
                                 json={'plugin_code': 'test'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert any(issue['type'] == 'signature_mismatch' for issue in data['issues'])
    
    def test_api_compatibility_connector_interface(self, client):
        """Test API compatibility checks connector implements BaseDatabaseConnector"""
        with patch('ai_agent_connector.app.api.routes.validate_api_compatibility') as mock_validate:
            mock_validate.return_value = {
                'compatible': False,
                'issues': [
                    {
                        'type': 'invalid_connector',
                        'message': 'Connector does not extend BaseDatabaseConnector',
                        'severity': 'error'
                    }
                ]
            }
            
            response = client.post('/api/plugins/validate/api-compatibility',
                                 json={'plugin_code': 'test'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert any(issue['type'] == 'invalid_connector' for issue in data['issues'])
    
    def test_api_compatibility_type_hints(self, client):
        """Test API compatibility validates type hints"""
        with patch('ai_agent_connector.app.api.routes.validate_api_compatibility') as mock_validate:
            mock_validate.return_value = {
                'compatible': True,
                'issues': [],
                'type_hints': {
                    'plugin_name': 'str',
                    'plugin_version': 'str',
                    'database_type': 'str',
                    'create_connector': 'BaseDatabaseConnector'
                },
                'warnings': []
            }
            
            response = client.post('/api/plugins/validate/api-compatibility',
                                 json={'plugin_code': 'test'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'type_hints' in data
    
    def test_api_compatibility_version_check(self, client):
        """Test API compatibility checks plugin SDK version compatibility"""
        with patch('ai_agent_connector.app.api.routes.validate_api_compatibility') as mock_validate:
            mock_validate.return_value = {
                'compatible': False,
                'issues': [
                    {
                        'type': 'version_incompatibility',
                        'plugin_sdk_version': '1.0.0',
                        'required_sdk_version': '2.0.0',
                        'severity': 'error',
                        'message': 'Plugin requires SDK version 2.0.0 or higher'
                    }
                ]
            }
            
            response = client.post('/api/plugins/validate/api-compatibility',
                                 json={
                                     'plugin_code': 'test',
                                     'sdk_version': '1.0.0'
                                 })
            
            assert response.status_code == 200
            data = response.get_json()
            assert any(issue['type'] == 'version_incompatibility' for issue in data['issues'])


# ============================================================================
# Auto-Testing Tests
# ============================================================================

class TestPluginAutoTesting:
    """Test cases for automated plugin testing"""
    
    def test_auto_test_plugin_creation(self, client, sample_plugin_file):
        """Test automated testing of plugin creation"""
        with patch('ai_agent_connector.app.api.routes.run_plugin_tests') as mock_tests:
            mock_tests.return_value = {
                'passed': True,
                'tests': [
                    {
                        'name': 'test_plugin_creation',
                        'status': 'passed',
                        'message': 'Plugin instance created successfully'
                    }
                ],
                'total': 1,
                'passed_count': 1,
                'failed_count': 0
            }
            
            with open(sample_plugin_file, 'rb') as f:
                response = client.post('/api/plugins/validate/auto-test',
                                     data={'plugin_file': f},
                                     content_type='multipart/form-data')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['passed'] is True
            assert data['passed_count'] == 1
    
    def test_auto_test_connector_functionality(self, client):
        """Test automated testing of connector methods"""
        with patch('ai_agent_connector.app.api.routes.run_plugin_tests') as mock_tests:
            mock_tests.return_value = {
                'passed': True,
                'tests': [
                    {
                        'name': 'test_connector_connect',
                        'status': 'passed'
                    },
                    {
                        'name': 'test_connector_disconnect',
                        'status': 'passed'
                    },
                    {
                        'name': 'test_connector_execute_query',
                        'status': 'passed'
                    },
                    {
                        'name': 'test_connector_get_database_info',
                        'status': 'passed'
                    }
                ],
                'total': 4,
                'passed_count': 4,
                'failed_count': 0
            }
            
            response = client.post('/api/plugins/validate/auto-test',
                                 json={'plugin_code': 'test'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['passed_count'] == 4
            assert data['failed_count'] == 0
    
    def test_auto_test_configuration_validation(self, client):
        """Test automated testing of configuration validation"""
        with patch('ai_agent_connector.app.api.routes.run_plugin_tests') as mock_tests:
            mock_tests.return_value = {
                'passed': True,
                'tests': [
                    {
                        'name': 'test_config_validation_valid',
                        'status': 'passed',
                        'message': 'Valid configuration accepted'
                    },
                    {
                        'name': 'test_config_validation_missing_required',
                        'status': 'passed',
                        'message': 'Missing required keys rejected'
                    },
                    {
                        'name': 'test_config_validation_optional_keys',
                        'status': 'passed',
                        'message': 'Optional keys handled correctly'
                    }
                ],
                'total': 3,
                'passed_count': 3
            }
            
            response = client.post('/api/plugins/validate/auto-test',
                                 json={'plugin_code': 'test'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['passed_count'] == 3
    
    def test_auto_test_error_handling(self, client):
        """Test automated testing of error handling"""
        with patch('ai_agent_connector.app.api.routes.run_plugin_tests') as mock_tests:
            mock_tests.return_value = {
                'passed': True,
                'tests': [
                    {
                        'name': 'test_error_handling_connection_failure',
                        'status': 'passed',
                        'message': 'Connection errors handled gracefully'
                    },
                    {
                        'name': 'test_error_handling_invalid_query',
                        'status': 'passed',
                        'message': 'Invalid queries handled correctly'
                    }
                ]
            }
            
            response = client.post('/api/plugins/validate/auto-test',
                                 json={'plugin_code': 'test'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['passed'] is True
    
    def test_auto_test_failure_reporting(self, client):
        """Test automated testing reports test failures"""
        with patch('ai_agent_connector.app.api.routes.run_plugin_tests') as mock_tests:
            mock_tests.return_value = {
                'passed': False,
                'tests': [
                    {
                        'name': 'test_connector_connect',
                        'status': 'passed'
                    },
                    {
                        'name': 'test_connector_execute_query',
                        'status': 'failed',
                        'error': 'Query execution returned unexpected format',
                        'traceback': 'File "test.py", line 42...'
                    }
                ],
                'total': 2,
                'passed_count': 1,
                'failed_count': 1
            }
            
            response = client.post('/api/plugins/validate/auto-test',
                                 json={'plugin_code': 'test'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['passed'] is False
            assert data['failed_count'] == 1
            assert any(t['status'] == 'failed' for t in data['tests'])
    
    def test_auto_test_performance_checks(self, client):
        """Test automated testing includes performance checks"""
        with patch('ai_agent_connector.app.api.routes.run_plugin_tests') as mock_tests:
            mock_tests.return_value = {
                'passed': True,
                'tests': [
                    {
                        'name': 'test_connection_time',
                        'status': 'passed',
                        'duration_ms': 150,
                        'threshold_ms': 1000
                    },
                    {
                        'name': 'test_query_execution_time',
                        'status': 'passed',
                        'duration_ms': 50,
                        'threshold_ms': 500
                    }
                ],
                'performance_metrics': {
                    'avg_connection_time_ms': 150,
                    'avg_query_time_ms': 50
                }
            }
            
            response = client.post('/api/plugins/validate/auto-test',
                                 json={'plugin_code': 'test'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'performance_metrics' in data
    
    def test_auto_test_coverage_report(self, client):
        """Test automated testing includes code coverage report"""
        with patch('ai_agent_connector.app.api.routes.run_plugin_tests') as mock_tests:
            mock_tests.return_value = {
                'passed': True,
                'coverage': {
                    'total': 85.5,
                    'statements': 100,
                    'covered': 85,
                    'missing': ['line_42', 'line_58'],
                    'branches': {
                        'total': 20,
                        'covered': 18
                    }
                }
            }
            
            response = client.post('/api/plugins/validate/auto-test',
                                 json={'plugin_code': 'test'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'coverage' in data
            assert data['coverage']['total'] >= 80  # Minimum coverage threshold


# ============================================================================
# Integration Tests
# ============================================================================

class TestPluginValidationIntegration:
    """Integration tests for complete validation workflow"""
    
    def test_complete_validation_workflow(self, client, sample_plugin_file):
        """Test complete validation workflow: security + API + tests"""
        validation_id = 'test-validation-123'
        
        with patch('ai_agent_connector.app.api.routes.submit_plugin_validation') as mock_submit:
            mock_submit.return_value = {'validation_id': validation_id}
            
            with open(sample_plugin_file, 'rb') as f:
                response = client.post('/api/plugins/validate/submit',
                                     data={'plugin_file': f},
                                     content_type='multipart/form-data')
                
                assert response.status_code in [200, 202]
                
                # Check status
                with patch('ai_agent_connector.app.api.routes.get_validation_status') as mock_status:
                    mock_status.return_value = {
                        'validation_id': validation_id,
                        'status': 'completed',
                        'stages': {
                            'security_scan': 'passed',
                            'api_compatibility': 'passed',
                            'auto_tests': 'passed'
                        },
                        'results': {
                            'security_scan': {'score': 95},
                            'api_compatibility': {'compatible': True},
                            'auto_tests': {'passed': 10, 'failed': 0}
                        }
                    }
                    
                    status_response = client.get(f'/api/plugins/validate/status/{validation_id}')
                    assert status_response.status_code == 200
                    status_data = status_response.get_json()
                    assert status_data['status'] == 'completed'
    
    def test_validation_with_security_failure(self, client, vulnerable_plugin_file):
        """Test validation workflow stops on security failure"""
        validation_id = 'test-validation-456'
        
        with patch('ai_agent_connector.app.api.routes.submit_plugin_validation') as mock_submit:
            mock_submit.return_value = {'validation_id': validation_id}
            
            with open(vulnerable_plugin_file, 'rb') as f:
                client.post('/api/plugins/validate/submit',
                          data={'plugin_file': f},
                          content_type='multipart/form-data')
                
                with patch('ai_agent_connector.app.api.routes.get_validation_status') as mock_status:
                    mock_status.return_value = {
                        'validation_id': validation_id,
                        'status': 'failed',
                        'stages': {
                            'security_scan': 'failed',
                            'api_compatibility': 'skipped',
                            'auto_tests': 'skipped'
                        },
                        'errors': ['Critical security vulnerabilities detected']
                    }
                    
                    status_response = client.get(f'/api/plugins/validate/status/{validation_id}')
                    status_data = status_response.get_json()
                    assert status_data['status'] == 'failed'
                    assert status_data['stages']['api_compatibility'] == 'skipped'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
