"""
Tests for version control system
"""

import pytest
from ai_agent_connector.app.utils.version_control import (
    ConfigurationVersionControl,
    ConfigurationVersion
)


class TestConfigurationVersion:
    """Tests for ConfigurationVersion"""
    
    def test_version_to_dict(self):
        """Test converting version to dictionary"""
        version = ConfigurationVersion(
            version=1,
            timestamp="2024-01-01T00:00:00Z",
            config={"model": "gpt-4"},
            description="Initial config",
            tags=["initial"]
        )
        
        result = version.to_dict()
        
        assert result['version'] == 1
        assert result['config']['model'] == "gpt-4"
        assert result['description'] == "Initial config"
        assert result['tags'] == ["initial"]
    
    def test_version_from_dict(self):
        """Test creating version from dictionary"""
        data = {
            'version': 2,
            'timestamp': '2024-01-01T00:00:00Z',
            'config': {'model': 'gpt-4'},
            'description': 'Updated',
            'tags': ['update']
        }
        
        version = ConfigurationVersion.from_dict(data)
        
        assert version.version == 2
        assert version.config['model'] == 'gpt-4'
        assert version.description == 'Updated'


class TestConfigurationVersionControl:
    """Tests for ConfigurationVersionControl"""
    
    def test_create_version(self):
        """Test creating a new version"""
        vc = ConfigurationVersionControl()
        config = {"model": "gpt-4", "temperature": 0.7}
        
        version = vc.create_version(
            agent_id="agent1",
            config=config,
            description="Initial config"
        )
        
        assert version.version == 1
        assert version.config == config
        assert version.description == "Initial config"
    
    def test_get_version_latest(self):
        """Test getting latest version"""
        vc = ConfigurationVersionControl()
        
        vc.create_version("agent1", {"model": "gpt-4"})
        vc.create_version("agent1", {"model": "gpt-3.5"})
        
        latest = vc.get_version("agent1")
        
        assert latest.version == 2
        assert latest.config["model"] == "gpt-3.5"
    
    def test_get_version_specific(self):
        """Test getting a specific version"""
        vc = ConfigurationVersionControl()
        
        vc.create_version("agent1", {"model": "gpt-4"})
        vc.create_version("agent1", {"model": "gpt-3.5"})
        
        v1 = vc.get_version("agent1", version=1)
        
        assert v1.version == 1
        assert v1.config["model"] == "gpt-4"
    
    def test_list_versions(self):
        """Test listing all versions"""
        vc = ConfigurationVersionControl()
        
        vc.create_version("agent1", {"model": "gpt-4"})
        vc.create_version("agent1", {"model": "gpt-3.5"})
        vc.create_version("agent1", {"model": "claude"})
        
        versions = vc.list_versions("agent1")
        
        assert len(versions) == 3
        assert versions[0].version == 3  # Newest first
        assert versions[2].version == 1
    
    def test_list_versions_with_limit(self):
        """Test listing versions with limit"""
        vc = ConfigurationVersionControl()
        
        for i in range(5):
            vc.create_version("agent1", {"model": f"model-{i}"})
        
        versions = vc.list_versions("agent1", limit=3)
        
        assert len(versions) == 3
        assert versions[0].version == 5
    
    def test_get_current_version(self):
        """Test getting current version number"""
        vc = ConfigurationVersionControl()
        
        vc.create_version("agent1", {"model": "gpt-4"})
        vc.create_version("agent1", {"model": "gpt-3.5"})
        
        current = vc.get_current_version("agent1")
        
        assert current == 2
    
    def test_rollback_to_version(self):
        """Test rolling back to a previous version"""
        vc = ConfigurationVersionControl()
        
        vc.create_version("agent1", {"model": "gpt-4"})
        vc.create_version("agent1", {"model": "gpt-3.5"})
        vc.create_version("agent1", {"model": "claude"})
        
        rollback = vc.rollback_to_version(
            agent_id="agent1",
            version=1,
            description="Rolling back"
        )
        
        assert rollback.version == 4  # New version created
        assert rollback.config["model"] == "gpt-4"  # From version 1
        assert "rollback" in rollback.tags
    
    def test_rollback_invalid_version(self):
        """Test rolling back to non-existent version"""
        vc = ConfigurationVersionControl()
        
        vc.create_version("agent1", {"model": "gpt-4"})
        
        with pytest.raises(ValueError):
            vc.rollback_to_version("agent1", version=99)
    
    def test_compare_versions(self):
        """Test comparing two versions"""
        vc = ConfigurationVersionControl()
        
        vc.create_version("agent1", {"model": "gpt-4", "temperature": 0.7})
        vc.create_version("agent1", {"model": "gpt-3.5", "temperature": 0.8})
        
        comparison = vc.compare_versions("agent1", version1=1, version2=2)
        
        assert comparison['version1'] == 1
        assert comparison['version2'] == 2
        assert len(comparison['changes']) == 2  # model and temperature changed
    
    def test_delete_agent_versions(self):
        """Test deleting all versions for an agent"""
        vc = ConfigurationVersionControl()
        
        vc.create_version("agent1", {"model": "gpt-4"})
        vc.create_version("agent2", {"model": "claude"})
        
        vc.delete_agent_versions("agent1")
        
        assert vc.get_version("agent1") is None
        assert vc.get_version("agent2") is not None
    
    def test_get_version_history_summary(self):
        """Test getting version history summary"""
        vc = ConfigurationVersionControl()
        
        vc.create_version("agent1", {"model": "gpt-4"}, description="Initial")
        vc.create_version("agent1", {"model": "gpt-3.5"}, description="Updated")
        
        summary = vc.get_version_history_summary("agent1")
        
        assert summary['agent_id'] == "agent1"
        assert summary['total_versions'] == 2
        assert summary['current_version'] == 2
        assert len(summary['versions']) == 2

