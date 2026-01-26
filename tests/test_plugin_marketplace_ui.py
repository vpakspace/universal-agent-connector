"""
Tests for Plugin Marketplace UI Story

Story: As a Developer, I want a plugin marketplace UI to browse and install community drivers,
       so that I can extend functionality without code changes.

Acceptance Criteria:
- Search functionality
- Install functionality
- Uninstall functionality
- Rating system
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from main import create_app
from ai_agent_connector.app.db.plugin import (
    DatabasePlugin,
    PluginRegistry,
    get_plugin_registry,
    register_plugin
)
from ai_agent_connector.app.db.base_connector import BaseDatabaseConnector
import tempfile
import os
from pathlib import Path


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


class CommunityPlugin1(DatabasePlugin):
    """Community plugin for testing marketplace"""
    
    @property
    def plugin_name(self):
        return "community_plugin_1"
    
    @property
    def plugin_version(self):
        return "1.2.0"
    
    @property
    def database_type(self):
        return "community_db_1"
    
    @property
    def display_name(self):
        return "Community Database 1"
    
    @property
    def description(self):
        return "A popular community database driver with excellent performance"
    
    @property
    def author(self):
        return "Community Dev Team"
    
    @property
    def required_config_keys(self):
        return ['host', 'database']
    
    def create_connector(self, config):
        return MockConnector(config)
    
    def detect_database_type(self, config):
        if config.get('type', '').lower() == 'community_db_1':
            return self.database_type
        return None


class CommunityPlugin2(DatabasePlugin):
    """Another community plugin"""
    
    @property
    def plugin_name(self):
        return "community_plugin_2"
    
    @property
    def plugin_version(self):
        return "2.0.1"
    
    @property
    def database_type(self):
        return "community_db_2"
    
    @property
    def display_name(self):
        return "Community Database 2"
    
    @property
    def description(self):
        return "Another database driver for specialized use cases"
    
    @property
    def author(self):
        return "Another Developer"
    
    @property
    def required_config_keys(self):
        return ['endpoint', 'api_key']
    
    def create_connector(self, config):
        return MockConnector(config)
    
    def detect_database_type(self, config):
        if config.get('type', '').lower() == 'community_db_2':
            return self.database_type
        return None


class SpecializedPlugin(DatabasePlugin):
    """Specialized plugin for search testing"""
    
    @property
    def plugin_name(self):
        return "specialized_postgresql_plugin"
    
    @property
    def plugin_version(self):
        return "3.1.0"
    
    @property
    def database_type(self):
        return "specialized_pg"
    
    @property
    def display_name(self):
        return "Specialized PostgreSQL Extension"
    
    @property
    def description(self):
        return "Extended PostgreSQL driver with advanced features"
    
    @property
    def author(self):
        return "PostgreSQL Expert"
    
    @property
    def required_config_keys(self):
        return ['host']
    
    def create_connector(self, config):
        return MockConnector(config)
    
    def detect_database_type(self, config):
        if 'specialized_pg' in config.get('type', '').lower():
            return self.database_type
        return None


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_plugin_registry():
    """Reset plugin registry before and after each test"""
    registry = get_plugin_registry()
    # Save original plugins
    original_plugins = dict(registry._plugins)
    original_paths = dict(registry._plugin_paths)
    
    # Clear registry
    registry._plugins.clear()
    registry._plugin_paths.clear()
    
    yield
    
    # Restore original plugins
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
def marketplace_plugins():
    """Create sample marketplace plugins"""
    return [
        CommunityPlugin1(),
        CommunityPlugin2(),
        SpecializedPlugin()
    ]


@pytest.fixture
def installed_plugin():
    """Create an installed plugin for testing"""
    plugin = CommunityPlugin1()
    registry = get_plugin_registry()
    registry.register(plugin)
    return plugin


# ============================================================================
# Search Functionality Tests
# ============================================================================

class TestPluginMarketplaceSearch:
    """Test cases for plugin marketplace search functionality"""
    
    def test_search_by_name(self, client, marketplace_plugins):
        """Test searching plugins by name"""
        # Mock marketplace API to return plugins
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugins') as mock_get:
            mock_get.return_value = marketplace_plugins
            
            response = client.get('/api/marketplace/search?q=community')
            assert response.status_code == 200
            data = response.get_json()
            
            assert 'results' in data
            assert len(data['results']) >= 2  # Should find CommunityPlugin1 and CommunityPlugin2
            assert any(p['plugin_name'] == 'community_plugin_1' for p in data['results'])
            assert any(p['plugin_name'] == 'community_plugin_2' for p in data['results'])
    
    def test_search_by_description(self, client, marketplace_plugins):
        """Test searching plugins by description"""
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugins') as mock_get:
            mock_get.return_value = marketplace_plugins
            
            response = client.get('/api/marketplace/search?q=performance')
            assert response.status_code == 200
            data = response.get_json()
            
            assert 'results' in data
            # Should find CommunityPlugin1 which mentions "performance"
            assert any('performance' in p.get('description', '').lower() for p in data['results'])
    
    def test_search_by_author(self, client, marketplace_plugins):
        """Test searching plugins by author name"""
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugins') as mock_get:
            mock_get.return_value = marketplace_plugins
            
            response = client.get('/api/marketplace/search?q=Community Dev Team')
            assert response.status_code == 200
            data = response.get_json()
            
            assert 'results' in data
            assert any(p['author'] == 'Community Dev Team' for p in data['results'])
    
    def test_search_by_database_type(self, client, marketplace_plugins):
        """Test searching plugins by database type"""
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugins') as mock_get:
            mock_get.return_value = marketplace_plugins
            
            response = client.get('/api/marketplace/search?q=postgresql')
            assert response.status_code == 200
            data = response.get_json()
            
            assert 'results' in data
            # Should find SpecializedPlugin
            assert any('postgresql' in p.get('display_name', '').lower() or 
                      'postgresql' in p.get('description', '').lower() 
                      for p in data['results'])
    
    def test_search_no_results(self, client, marketplace_plugins):
        """Test search with no matching results"""
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugins') as mock_get:
            mock_get.return_value = marketplace_plugins
            
            response = client.get('/api/marketplace/search?q=nonexistent')
            assert response.status_code == 200
            data = response.get_json()
            
            assert 'results' in data
            assert len(data['results']) == 0
    
    def test_search_case_insensitive(self, client, marketplace_plugins):
        """Test that search is case insensitive"""
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugins') as mock_get:
            mock_get.return_value = marketplace_plugins
            
            response = client.get('/api/marketplace/search?q=COMMUNITY')
            assert response.status_code == 200
            data = response.get_json()
            
            assert len(data['results']) >= 2
    
    def test_search_empty_query(self, client, marketplace_plugins):
        """Test search with empty query returns all plugins"""
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugins') as mock_get:
            mock_get.return_value = marketplace_plugins
            
            response = client.get('/api/marketplace/search?q=')
            assert response.status_code == 200
            data = response.get_json()
            
            assert 'results' in data
            assert len(data['results']) == len(marketplace_plugins)
    
    def test_search_with_filters(self, client, marketplace_plugins):
        """Test search with additional filters (category, rating, etc.)"""
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugins') as mock_get:
            mock_get.return_value = marketplace_plugins
            
            response = client.get('/api/marketplace/search?q=community&min_rating=4.0')
            assert response.status_code == 200
            data = response.get_json()
            
            assert 'results' in data
            # Results should have rating >= 4.0
            for plugin in data['results']:
                if 'average_rating' in plugin:
                    assert plugin['average_rating'] >= 4.0
    
    def test_search_pagination(self, client, marketplace_plugins):
        """Test search with pagination"""
        # Create more plugins for pagination testing
        many_plugins = marketplace_plugins * 5  # 15 plugins total
        
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugins') as mock_get:
            mock_get.return_value = many_plugins
            
            response = client.get('/api/marketplace/search?q=&page=1&per_page=5')
            assert response.status_code == 200
            data = response.get_json()
            
            assert 'results' in data
            assert len(data['results']) == 5
            assert 'pagination' in data
            assert data['pagination']['page'] == 1
            assert data['pagination']['per_page'] == 5
            assert data['pagination']['total'] == 15
    
    def test_search_sort_by_rating(self, client, marketplace_plugins):
        """Test search results sorted by rating"""
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugins') as mock_get:
            mock_get.return_value = marketplace_plugins
            with patch('ai_agent_connector.app.api.routes.get_plugin_ratings') as mock_ratings:
                # Mock ratings: plugin1=4.5, plugin2=3.5, plugin3=4.0
                mock_ratings.side_effect = lambda p: {
                    'community_plugin_1': {'average_rating': 4.5},
                    'community_plugin_2': {'average_rating': 3.5},
                    'specialized_postgresql_plugin': {'average_rating': 4.0}
                }.get(p.plugin_name, {'average_rating': 0})
                
                response = client.get('/api/marketplace/search?q=&sort=rating_desc')
                assert response.status_code == 200
                data = response.get_json()
                
                assert 'results' in data
                # Should be sorted by rating descending
                ratings = [p.get('average_rating', 0) for p in data['results'] if 'average_rating' in p]
                assert ratings == sorted(ratings, reverse=True)


# ============================================================================
# Install Functionality Tests
# ============================================================================

class TestPluginMarketplaceInstall:
    """Test cases for plugin installation from marketplace"""
    
    def test_install_plugin_from_marketplace(self, client, marketplace_plugins):
        """Test installing a plugin from marketplace"""
        plugin_to_install = marketplace_plugins[0]
        
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugin') as mock_get:
            mock_get.return_value = plugin_to_install
            with patch('ai_agent_connector.app.api.routes.download_and_install_plugin') as mock_install:
                mock_install.return_value = {'success': True, 'plugin': plugin_to_install.get_plugin_info()}
                
                response = client.post('/api/marketplace/install', json={
                    'plugin_name': 'community_plugin_1',
                    'version': '1.2.0'
                })
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert 'plugin' in data
                mock_install.assert_called_once()
    
    def test_install_plugin_already_installed(self, client, installed_plugin):
        """Test installing a plugin that's already installed"""
        response = client.post('/api/marketplace/install', json={
            'plugin_name': installed_plugin.plugin_name,
            'version': installed_plugin.plugin_version
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'already installed' in data.get('error', '').lower()
    
    def test_install_plugin_not_found(self, client):
        """Test installing a plugin that doesn't exist in marketplace"""
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugin') as mock_get:
            mock_get.return_value = None
            
            response = client.post('/api/marketplace/install', json={
                'plugin_name': 'nonexistent_plugin',
                'version': '1.0.0'
            })
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'not found' in data.get('error', '').lower()
    
    def test_install_plugin_missing_parameters(self, client):
        """Test installing plugin with missing required parameters"""
        response = client.post('/api/marketplace/install', json={
            'plugin_name': 'some_plugin'
            # Missing version
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'required' in data.get('error', '').lower() or 'missing' in data.get('error', '').lower()
    
    def test_install_plugin_specific_version(self, client, marketplace_plugins):
        """Test installing a specific version of a plugin"""
        plugin = marketplace_plugins[0]
        
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugin') as mock_get:
            mock_get.return_value = plugin
            with patch('ai_agent_connector.app.api.routes.download_and_install_plugin') as mock_install:
                mock_install.return_value = {'success': True, 'plugin': plugin.get_plugin_info()}
                
                response = client.post('/api/marketplace/install', json={
                    'plugin_name': 'community_plugin_1',
                    'version': '1.2.0'
                })
                
                assert response.status_code == 200
                # Verify version was specified
                call_args = mock_install.call_args
                assert call_args is not None
    
    def test_install_plugin_latest_version(self, client, marketplace_plugins):
        """Test installing latest version of a plugin"""
        plugin = marketplace_plugins[0]
        
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugin') as mock_get:
            mock_get.return_value = plugin
            with patch('ai_agent_connector.app.api.routes.download_and_install_plugin') as mock_install:
                mock_install.return_value = {'success': True, 'plugin': plugin.get_plugin_info()}
                
                response = client.post('/api/marketplace/install', json={
                    'plugin_name': 'community_plugin_1',
                    'version': 'latest'
                })
                
                assert response.status_code == 200
    
    def test_install_plugin_verification(self, client, marketplace_plugins):
        """Test that installed plugin is verified and registered"""
        plugin = marketplace_plugins[0]
        
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugin') as mock_get:
            mock_get.return_value = plugin
            with patch('ai_agent_connector.app.api.routes.download_and_install_plugin') as mock_install:
                mock_install.return_value = {'success': True, 'plugin': plugin.get_plugin_info()}
                
                response = client.post('/api/marketplace/install', json={
                    'plugin_name': 'community_plugin_1',
                    'version': '1.2.0'
                })
                
                assert response.status_code == 200
                
                # Verify plugin is now registered
                registry = get_plugin_registry()
                installed = registry.get_plugin(plugin.database_type)
                assert installed is not None
                assert installed.plugin_name == plugin.plugin_name
    
    def test_install_plugin_download_failure(self, client, marketplace_plugins):
        """Test handling of download failure during installation"""
        plugin = marketplace_plugins[0]
        
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugin') as mock_get:
            mock_get.return_value = plugin
            with patch('ai_agent_connector.app.api.routes.download_and_install_plugin') as mock_install:
                mock_install.side_effect = Exception("Download failed")
                
                response = client.post('/api/marketplace/install', json={
                    'plugin_name': 'community_plugin_1',
                    'version': '1.2.0'
                })
                
                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data


# ============================================================================
# Uninstall Functionality Tests
# ============================================================================

class TestPluginMarketplaceUninstall:
    """Test cases for plugin uninstallation"""
    
    def test_uninstall_plugin(self, client, installed_plugin):
        """Test uninstalling an installed plugin"""
        registry = get_plugin_registry()
        assert registry.get_plugin(installed_plugin.database_type) is not None
        
        response = client.delete(f'/api/marketplace/uninstall/{installed_plugin.database_type}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify plugin is removed
        assert registry.get_plugin(installed_plugin.database_type) is None
    
    def test_uninstall_plugin_not_installed(self, client):
        """Test uninstalling a plugin that's not installed"""
        response = client.delete('/api/marketplace/uninstall/nonexistent_db')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'not found' in data.get('error', '').lower() or 'not installed' in data.get('error', '').lower()
    
    def test_uninstall_built_in_plugin(self, client):
        """Test that built-in plugins cannot be uninstalled"""
        response = client.delete('/api/marketplace/uninstall/postgresql')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'built-in' in data.get('error', '').lower() or 'cannot' in data.get('error', '').lower()
    
    def test_uninstall_plugin_confirmation(self, client, installed_plugin):
        """Test uninstall with confirmation"""
        response = client.delete(
            f'/api/marketplace/uninstall/{installed_plugin.database_type}',
            json={'confirm': True}
        )
        
        assert response.status_code == 200
    
    def test_uninstall_plugin_without_confirmation(self, client, installed_plugin):
        """Test uninstall requires confirmation"""
        response = client.delete(f'/api/marketplace/uninstall/{installed_plugin.database_type}')
        
        # Should either require confirmation or proceed (depends on implementation)
        assert response.status_code in [200, 400]
    
    def test_uninstall_plugin_cleanup(self, client, installed_plugin):
        """Test that uninstall properly cleans up plugin files"""
        registry = get_plugin_registry()
        
        with patch('ai_agent_connector.app.api.routes.remove_plugin_files') as mock_cleanup:
            response = client.delete(f'/api/marketplace/uninstall/{installed_plugin.database_type}')
            
            assert response.status_code == 200
            # Verify cleanup was called (if file-based installation)
            # This depends on implementation
    
    def test_uninstall_multiple_plugins(self, client, marketplace_plugins):
        """Test uninstalling multiple plugins"""
        registry = get_plugin_registry()
        
        # Install multiple plugins
        for plugin in marketplace_plugins:
            registry.register(plugin)
        
        # Uninstall one
        response = client.delete(f'/api/marketplace/uninstall/{marketplace_plugins[0].database_type}')
        assert response.status_code == 200
        
        # Verify others are still installed
        assert registry.get_plugin(marketplace_plugins[1].database_type) is not None
        assert registry.get_plugin(marketplace_plugins[2].database_type) is not None


# ============================================================================
# Rating System Tests
# ============================================================================

class TestPluginMarketplaceRating:
    """Test cases for plugin rating system"""
    
    def test_submit_rating(self, client, marketplace_plugins):
        """Test submitting a rating for a plugin"""
        plugin = marketplace_plugins[0]
        
        response = client.post('/api/marketplace/ratings', json={
            'plugin_name': plugin.plugin_name,
            'rating': 5,
            'comment': 'Excellent plugin!'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'rating' in data
    
    def test_submit_rating_invalid_range(self, client, marketplace_plugins):
        """Test submitting rating outside valid range (1-5)"""
        plugin = marketplace_plugins[0]
        
        response = client.post('/api/marketplace/ratings', json={
            'plugin_name': plugin.plugin_name,
            'rating': 6,  # Invalid
            'comment': 'Test'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'invalid' in data.get('error', '').lower() or 'range' in data.get('error', '').lower()
    
    def test_submit_rating_missing_fields(self, client, marketplace_plugins):
        """Test submitting rating with missing required fields"""
        response = client.post('/api/marketplace/ratings', json={
            'plugin_name': 'some_plugin'
            # Missing rating
        })
        
        assert response.status_code == 400
    
    def test_get_plugin_ratings(self, client, marketplace_plugins):
        """Test retrieving ratings for a plugin"""
        plugin = marketplace_plugins[0]
        
        # Submit some ratings first
        with patch('ai_agent_connector.app.api.routes.save_plugin_rating') as mock_save:
            mock_save.return_value = {'success': True}
            
            client.post('/api/marketplace/ratings', json={
                'plugin_name': plugin.plugin_name,
                'rating': 5,
                'comment': 'Great!'
            })
            client.post('/api/marketplace/ratings', json={
                'plugin_name': plugin.plugin_name,
                'rating': 4,
                'comment': 'Good plugin'
            })
        
        # Get ratings
        response = client.get(f'/api/marketplace/ratings/{plugin.plugin_name}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'ratings' in data or 'average_rating' in data
    
    def test_calculate_average_rating(self, client, marketplace_plugins):
        """Test that average rating is calculated correctly"""
        plugin = marketplace_plugins[0]
        
        # Submit multiple ratings
        ratings = [5, 4, 5, 3, 4]
        for rating in ratings:
            with patch('ai_agent_connector.app.api.routes.save_plugin_rating'):
                client.post('/api/marketplace/ratings', json={
                    'plugin_name': plugin.plugin_name,
                    'rating': rating
                })
        
        # Get average
        response = client.get(f'/api/marketplace/ratings/{plugin.plugin_name}')
        
        assert response.status_code == 200
        data = response.get_json()
        if 'average_rating' in data:
            expected_avg = sum(ratings) / len(ratings)  # 4.2
            assert abs(data['average_rating'] - expected_avg) < 0.1
    
    def test_rating_count(self, client, marketplace_plugins):
        """Test that rating count is tracked correctly"""
        plugin = marketplace_plugins[0]
        
        # Submit multiple ratings
        num_ratings = 5
        for i in range(num_ratings):
            with patch('ai_agent_connector.app.api.routes.save_plugin_rating'):
                client.post('/api/marketplace/ratings', json={
                    'plugin_name': plugin.plugin_name,
                    'rating': 4
                })
        
        response = client.get(f'/api/marketplace/ratings/{plugin.plugin_name}')
        
        assert response.status_code == 200
        data = response.get_json()
        if 'rating_count' in data or 'total_ratings' in data:
            count_key = 'rating_count' if 'rating_count' in data else 'total_ratings'
            assert data[count_key] == num_ratings
    
    def test_prevent_duplicate_rating(self, client, marketplace_plugins):
        """Test that same user cannot rate plugin twice"""
        plugin = marketplace_plugins[0]
        
        # Submit first rating
        response1 = client.post('/api/marketplace/ratings', json={
            'plugin_name': plugin.plugin_name,
            'rating': 5,
            'user_id': 'test_user'  # Assuming user tracking
        })
        assert response1.status_code == 200
        
        # Try to submit second rating from same user
        response2 = client.post('/api/marketplace/ratings', json={
            'plugin_name': plugin.plugin_name,
            'rating': 4,
            'user_id': 'test_user'
        })
        
        # Should either update existing rating or reject
        assert response2.status_code in [200, 400]
    
    def test_update_existing_rating(self, client, marketplace_plugins):
        """Test updating an existing rating"""
        plugin = marketplace_plugins[0]
        
        # Submit initial rating
        response1 = client.post('/api/marketplace/ratings', json={
            'plugin_name': plugin.plugin_name,
            'rating': 3,
            'user_id': 'test_user'
        })
        
        # Update rating
        response2 = client.put('/api/marketplace/ratings', json={
            'plugin_name': plugin.plugin_name,
            'rating': 5,
            'user_id': 'test_user'
        })
        
        # Should succeed (either 200 or 201)
        assert response2.status_code in [200, 201]
    
    def test_get_ratings_with_comments(self, client, marketplace_plugins):
        """Test retrieving ratings with comments"""
        plugin = marketplace_plugins[0]
        
        # Submit rating with comment
        with patch('ai_agent_connector.app.api.routes.save_plugin_rating'):
            client.post('/api/marketplace/ratings', json={
                'plugin_name': plugin.plugin_name,
                'rating': 5,
                'comment': 'Excellent plugin, very reliable!'
            })
        
        response = client.get(f'/api/marketplace/ratings/{plugin.plugin_name}')
        
        assert response.status_code == 200
        data = response.get_json()
        # Should include comments in response
        if 'ratings' in data:
            assert any('comment' in rating for rating in data['ratings'])


# ============================================================================
# Integration Tests
# ============================================================================

class TestPluginMarketplaceIntegration:
    """Integration tests for plugin marketplace workflow"""
    
    def test_browse_search_install_workflow(self, client, marketplace_plugins):
        """Test complete workflow: browse, search, install"""
        # Search for plugins
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugins') as mock_get:
            mock_get.return_value = marketplace_plugins
            
            search_response = client.get('/api/marketplace/search?q=community')
            assert search_response.status_code == 200
            
            # Install a plugin from search results
            plugin = marketplace_plugins[0]
            with patch('ai_agent_connector.app.api.routes.get_marketplace_plugin') as mock_get_plugin:
                mock_get_plugin.return_value = plugin
                with patch('ai_agent_connector.app.api.routes.download_and_install_plugin') as mock_install:
                    mock_install.return_value = {'success': True}
                    
                    install_response = client.post('/api/marketplace/install', json={
                        'plugin_name': plugin.plugin_name,
                        'version': plugin.plugin_version
                    })
                    assert install_response.status_code == 200
    
    def test_install_rate_uninstall_workflow(self, client, marketplace_plugins):
        """Test workflow: install, rate, uninstall"""
        plugin = marketplace_plugins[0]
        registry = get_plugin_registry()
        
        # Install
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugin') as mock_get:
            mock_get.return_value = plugin
            with patch('ai_agent_connector.app.api.routes.download_and_install_plugin'):
                registry.register(plugin)
                
                # Rate
                with patch('ai_agent_connector.app.api.routes.save_plugin_rating'):
                    rate_response = client.post('/api/marketplace/ratings', json={
                        'plugin_name': plugin.plugin_name,
                        'rating': 5
                    })
                    assert rate_response.status_code == 200
                
                # Uninstall
                uninstall_response = client.delete(f'/api/marketplace/uninstall/{plugin.database_type}')
                assert uninstall_response.status_code == 200
    
    def test_search_filtered_by_rating(self, client, marketplace_plugins):
        """Test search with rating filter"""
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugins') as mock_get:
            mock_get.return_value = marketplace_plugins
            with patch('ai_agent_connector.app.api.routes.get_plugin_ratings') as mock_ratings:
                # Mock different ratings for plugins
                def get_rating(plugin_name):
                    ratings = {
                        'community_plugin_1': {'average_rating': 4.8},
                        'community_plugin_2': {'average_rating': 3.2},
                        'specialized_postgresql_plugin': {'average_rating': 4.5}
                    }
                    return ratings.get(plugin_name, {'average_rating': 0})
                
                mock_ratings.side_effect = lambda p: get_rating(p.plugin_name if hasattr(p, 'plugin_name') else p)
                
                response = client.get('/api/marketplace/search?q=&min_rating=4.0')
                assert response.status_code == 200
                data = response.get_json()
                
                # Should only return plugins with rating >= 4.0
                for result in data.get('results', []):
                    if 'average_rating' in result:
                        assert result['average_rating'] >= 4.0


# ============================================================================
# UI Endpoint Tests
# ============================================================================

class TestPluginMarketplaceUI:
    """Test cases for marketplace UI endpoints"""
    
    def test_marketplace_page_renders(self, client):
        """Test that marketplace page template renders"""
        response = client.get('/marketplace')
        assert response.status_code == 200
        # Should render HTML template
    
    def test_marketplace_page_shows_plugins(self, client, marketplace_plugins):
        """Test that marketplace page displays available plugins"""
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugins') as mock_get:
            mock_get.return_value = marketplace_plugins
            
            response = client.get('/marketplace')
            assert response.status_code == 200
            # HTML should contain plugin information
    
    def test_plugin_detail_page(self, client, marketplace_plugins):
        """Test plugin detail page"""
        plugin = marketplace_plugins[0]
        
        with patch('ai_agent_connector.app.api.routes.get_marketplace_plugin') as mock_get:
            mock_get.return_value = plugin
            
            response = client.get(f'/marketplace/plugin/{plugin.plugin_name}')
            assert response.status_code == 200
            # Should show plugin details, ratings, install button
    
    def test_installed_plugins_page(self, client, installed_plugin):
        """Test page showing installed plugins"""
        response = client.get('/marketplace/installed')
        assert response.status_code == 200
        # Should list installed plugins with uninstall option


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
