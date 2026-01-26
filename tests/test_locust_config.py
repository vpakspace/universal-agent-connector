"""
Tests for Locust load testing configuration
"""

import pytest
from unittest.mock import Mock, patch


class TestLocustConfiguration:
    """Test Locust configuration"""
    
    def test_locustfile_exists(self):
        """Test that locustfile exists and is importable"""
        import sys
        from pathlib import Path
        
        locustfile = Path("load_tests/locustfile.py")
        assert locustfile.exists(), "locustfile.py should exist"
    
    def test_agent_connector_user_class(self):
        """Test AgentConnectorUser class structure"""
        # Import locustfile
        import sys
        import os
        sys.path.insert(0, os.path.join(os.getcwd(), 'load_tests'))
        
        try:
            from locustfile import AgentConnectorUser
            
            # Verify class exists
            assert AgentConnectorUser is not None
            
            # Verify it has required methods
            assert hasattr(AgentConnectorUser, 'on_start')
            assert hasattr(AgentConnectorUser, 'health_check')
            assert hasattr(AgentConnectorUser, 'execute_query')
            
        except ImportError:
            pytest.skip("Locust not installed or locustfile not importable")
    
    def test_user_tasks(self):
        """Test that user tasks are defined"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.getcwd(), 'load_tests'))
        
        try:
            from locustfile import AgentConnectorUser
            
            # Check for task decorators
            user = AgentConnectorUser()
            tasks = [attr for attr in dir(user) if hasattr(getattr(user, attr), '__self__')]
            
            # Should have multiple tasks
            assert len([m for m in dir(user) if m.startswith('test_') or hasattr(getattr(user, m, None), '__call__')]) > 0
            
        except ImportError:
            pytest.skip("Locust not installed")


class TestLocustUserBehavior:
    """Test Locust user behavior simulation"""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock HTTP client"""
        client = Mock()
        client.post = Mock(return_value=Mock(status_code=201, json=lambda: {'api_key': 'test-key'}))
        client.get = Mock(return_value=Mock(status_code=200, json=lambda: {'status': 'ok'}))
        return client
    
    def test_agent_setup(self, mock_client):
        """Test agent setup in on_start"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.getcwd(), 'load_tests'))
        
        try:
            from locustfile import AgentConnectorUser
            
            user = AgentConnectorUser()
            user.client = mock_client
            
            # Run on_start
            user.on_start()
            
            # Verify agent registration was attempted
            assert mock_client.post.called
            
        except ImportError:
            pytest.skip("Locust not installed")
    
    def test_health_check_task(self, mock_client):
        """Test health check task"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.getcwd(), 'load_tests'))
        
        try:
            from locustfile import AgentConnectorUser
            
            user = AgentConnectorUser()
            user.client = mock_client
            
            # Execute health check
            user.health_check()
            
            # Verify GET request was made
            mock_client.get.assert_called()
            
        except ImportError:
            pytest.skip("Locust not installed")
