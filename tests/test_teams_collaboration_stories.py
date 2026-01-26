"""
Integration tests for Teams & Collaboration Stories

Story 1: As an Organization Admin, I want to create teams with isolated database connections and agents,
         so that different departments can operate independently.

Story 2: As a Team Member, I want to share query results with colleagues via a link,
         so that insights are easily distributed.

Story 3: As an Admin, I want to assign role-based access (viewer, editor, admin) to team members,
         so that permissions are granular.

Story 4: As a User, I want to tag queries with labels (e.g., "marketing," "finance"),
         so that activity is organized and searchable.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from main import create_app
from ai_agent_connector.app.api.routes import (
    agent_registry, access_control, team_manager,
    query_sharing_manager, query_tagging_manager
)
from ai_agent_connector.app.permissions import Permission
from ai_agent_connector.app.utils.encryption import reset_encryptor
from ai_agent_connector.app.utils.teams import TeamRole


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    team_manager._teams.clear()
    team_manager._user_teams.clear()
    team_manager._agent_teams.clear()
    query_sharing_manager._shares.clear()
    query_tagging_manager._tags.clear()
    query_tagging_manager._tagged_queries.clear()
    query_tagging_manager._tag_index.clear()
    yield
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    team_manager._teams.clear()
    team_manager._user_teams.clear()
    team_manager._agent_teams.clear()
    query_sharing_manager._shares.clear()
    query_tagging_manager._tags.clear()
    query_tagging_manager._tagged_queries.clear()
    query_tagging_manager._tag_index.clear()


@pytest.fixture
def client():
    """Create test client"""
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def admin_agent():
    """Create an admin agent"""
    result = agent_registry.register_agent(
        agent_id='admin-agent',
        agent_info={'name': 'Admin Agent'},
        credentials={'api_key': 'admin-key', 'api_secret': 'admin-secret'}
    )
    access_control.grant_permission('admin-agent', Permission.ADMIN)
    return {'agent_id': 'admin-agent', 'api_key': result['api_key']}


@pytest.fixture
def test_agent():
    """Create a test agent"""
    result = agent_registry.register_agent(
        agent_id='test-agent',
        agent_info={'name': 'Test Agent'},
        credentials={'api_key': 'test-key', 'api_secret': 'test-secret'}
    )
    access_control.grant_permission('test-agent', Permission.READ)
    return {'agent_id': 'test-agent', 'api_key': result['api_key']}


class TestStory1_TeamManagement:
    """Story 1: Teams with isolated database connections and agents"""
    
    def test_create_team(self, client, admin_agent):
        """Test creating a team"""
        payload = {
            'name': 'Marketing Team',
            'description': 'Marketing department team',
            'tags': ['marketing', 'sales']
        }
        
        response = client.post(
            '/api/admin/teams',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'team' in data
        assert data['team']['name'] == 'Marketing Team'
        assert data['team']['description'] == 'Marketing department team'
        assert 'marketing' in data['team']['tags']
        assert data['team']['created_by'] == 'admin-agent'
        # Creator should be added as admin
        assert len(data['team']['members']) == 1
    
    def test_list_teams(self, client, admin_agent):
        """Test listing teams"""
        # Create some teams
        team1 = team_manager.create_team('Team 1', 'admin-agent', tags=['marketing'])
        team2 = team_manager.create_team('Team 2', 'admin-agent', tags=['finance'])
        
        response = client.get(
            '/api/admin/teams',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'teams' in data
        assert len(data['teams']) >= 2
    
    def test_get_team(self, client, admin_agent):
        """Test getting a specific team"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        
        response = client.get(
            f'/api/admin/teams/{team.team_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['team_id'] == team.team_id
        assert data['name'] == 'Test Team'
    
    def test_update_team(self, client, admin_agent):
        """Test updating a team"""
        team = team_manager.create_team('Old Name', 'admin-agent')
        
        payload = {
            'name': 'New Name',
            'description': 'Updated description',
            'tags': ['updated']
        }
        
        response = client.put(
            f'/api/admin/teams/{team.team_id}',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['team']['name'] == 'New Name'
        assert data['team']['description'] == 'Updated description'
    
    def test_delete_team(self, client, admin_agent):
        """Test deleting a team"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        
        response = client.delete(
            f'/api/admin/teams/{team.team_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify team is deleted
        assert team_manager.get_team(team.team_id) is None
    
    def test_assign_agent_to_team(self, client, admin_agent):
        """Test assigning an agent to a team"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        agent = agent_registry.register_agent(
            agent_id='team-agent',
            agent_info={'name': 'Team Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'}
        )
        
        response = client.post(
            f'/api/admin/teams/{team.team_id}/agents/team-agent',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify agent is assigned
        assert team_manager.get_team_for_agent('team-agent') == team.team_id
        assert 'team-agent' in team.agent_ids
    
    def test_filter_teams_by_tags(self, client, admin_agent):
        """Test filtering teams by tags"""
        team1 = team_manager.create_team('Marketing', 'admin-agent', tags=['marketing'])
        team2 = team_manager.create_team('Finance', 'admin-agent', tags=['finance'])
        
        response = client.get(
            '/api/admin/teams?tags=marketing',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all('marketing' in t['tags'] for t in data['teams'])


class TestStory2_QuerySharing:
    """Story 2: Share query results via links"""
    
    def test_share_query_result(self, client, test_agent):
        """Test sharing a query result"""
        payload = {
            'query': 'SELECT * FROM users',
            'query_type': 'SELECT',
            'result': [{'id': 1, 'name': 'John'}],
            'is_public': True,
            'expires_in_hours': 24
        }
        
        response = client.post(
            '/api/agents/test-agent/queries/share',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'share' in data
        assert 'share_link' in data
        assert data['share']['query'] == 'SELECT * FROM users'
        assert data['share']['is_public'] is True
    
    def test_get_shared_query(self, client, test_agent):
        """Test getting a shared query via link"""
        share = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM users',
            query_type='SELECT',
            result=[{'id': 1, 'name': 'John'}],
            shared_by='test-agent',
            is_public=True
        )
        
        response = client.get(f'/api/shared/{share.share_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['query'] == 'SELECT * FROM users'
        assert data['result'] == [{'id': 1, 'name': 'John'}]
    
    def test_share_with_password(self, client, test_agent):
        """Test password-protected share"""
        share = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM users',
            query_type='SELECT',
            result=[{'id': 1}],
            shared_by='test-agent',
            password='secret123'
        )
        
        # Try without password (should fail)
        response = client.get(f'/api/shared/{share.share_id}')
        assert response.status_code == 404
        
        # Try with correct password
        response = client.get(f'/api/shared/{share.share_id}?password=secret123')
        assert response.status_code == 200
        
        # Try with wrong password
        response = client.get(f'/api/shared/{share.share_id}?password=wrong')
        assert response.status_code == 404
    
    def test_share_expiration(self, client, test_agent):
        """Test share expiration"""
        from datetime import datetime, timedelta
        
        share = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM users',
            query_type='SELECT',
            result=[{'id': 1}],
            shared_by='test-agent',
            expires_in_hours=-1  # Already expired
        )
        
        # Should not be accessible
        response = client.get(f'/api/shared/{share.share_id}')
        assert response.status_code == 404
    
    def test_share_access_limit(self, client, test_agent):
        """Test share access limit"""
        share = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM users',
            query_type='SELECT',
            result=[{'id': 1}],
            shared_by='test-agent',
            max_access_count=2
        )
        
        # First access
        response = client.get(f'/api/shared/{share.share_id}')
        assert response.status_code == 200
        
        # Second access
        response = client.get(f'/api/shared/{share.share_id}')
        assert response.status_code == 200
        
        # Third access should fail
        response = client.get(f'/api/shared/{share.share_id}')
        assert response.status_code == 404
    
    def test_list_shared_queries(self, client, test_agent):
        """Test listing shared queries"""
        share1 = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM users',
            query_type='SELECT',
            result=[{'id': 1}],
            shared_by='test-agent'
        )
        share2 = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM orders',
            query_type='SELECT',
            result=[{'id': 1}],
            shared_by='test-agent'
        )
        
        response = client.get(
            '/api/agents/test-agent/queries/shares',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['shares']) >= 2
    
    def test_delete_shared_query(self, client, test_agent):
        """Test deleting a shared query"""
        share = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM users',
            query_type='SELECT',
            result=[{'id': 1}],
            shared_by='test-agent'
        )
        
        response = client.delete(
            f'/api/agents/test-agent/queries/shares/{share.share_id}',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify share is deleted
        assert query_sharing_manager.get_share(share.share_id) is None
    
    def test_get_share_stats(self, client, test_agent):
        """Test getting share statistics"""
        share = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM users',
            query_type='SELECT',
            result=[{'id': 1}],
            shared_by='test-agent',
            max_access_count=10
        )
        
        # Access it once
        client.get(f'/api/shared/{share.share_id}')
        
        response = client.get(f'/api/shared/{share.share_id}/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['access_count'] == 1
        assert data['max_access_count'] == 10


class TestStory3_RoleBasedAccess:
    """Story 3: Role-based access control for teams"""
    
    def test_add_team_member(self, client, admin_agent):
        """Test adding a member to a team"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        
        payload = {
            'user_id': 'user-1',
            'role': 'editor'
        }
        
        response = client.post(
            f'/api/admin/teams/{team.team_id}/members',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify member was added
        assert team.has_member('user-1')
        assert team.get_member_role('user-1') == TeamRole.EDITOR
    
    def test_remove_team_member(self, client, admin_agent):
        """Test removing a member from a team"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        team.add_member('user-1', TeamRole.EDITOR)
        
        response = client.delete(
            f'/api/admin/teams/{team.team_id}/members/user-1',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify member was removed
        assert not team.has_member('user-1')
    
    def test_update_member_role(self, client, admin_agent):
        """Test updating a member's role"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        team.add_member('user-1', TeamRole.VIEWER)
        
        payload = {'role': 'admin'}
        
        response = client.put(
            f'/api/admin/teams/{team.team_id}/members/user-1/role',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify role was updated
        assert team.get_member_role('user-1') == TeamRole.ADMIN
    
    def test_role_hierarchy(self, client, admin_agent):
        """Test role hierarchy (viewer < editor < admin)"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        
        # Add members with different roles
        team.add_member('viewer-user', TeamRole.VIEWER)
        team.add_member('editor-user', TeamRole.EDITOR)
        team.add_member('admin-user', TeamRole.ADMIN)
        
        # Check permissions
        assert team.check_permission(team.team_id, 'viewer-user', TeamRole.VIEWER)
        assert not team.check_permission(team.team_id, 'viewer-user', TeamRole.EDITOR)
        assert not team.check_permission(team.team_id, 'viewer-user', TeamRole.ADMIN)
        
        assert team.check_permission(team.team_id, 'editor-user', TeamRole.VIEWER)
        assert team.check_permission(team.team_id, 'editor-user', TeamRole.EDITOR)
        assert not team.check_permission(team.team_id, 'editor-user', TeamRole.ADMIN)
        
        assert team.check_permission(team.team_id, 'admin-user', TeamRole.VIEWER)
        assert team.check_permission(team.team_id, 'admin-user', TeamRole.EDITOR)
        assert team.check_permission(team.team_id, 'admin-user', TeamRole.ADMIN)
    
    def test_filter_teams_by_user(self, client, admin_agent):
        """Test filtering teams by user membership"""
        team1 = team_manager.create_team('Team 1', 'admin-agent')
        team2 = team_manager.create_team('Team 2', 'admin-agent')
        
        team1.add_member('user-1', TeamRole.VIEWER)
        
        response = client.get(
            '/api/admin/teams?user_id=user-1',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all('user-1' in t['members'] for t in data['teams'])


class TestStory4_QueryTagging:
    """Story 4: Tag queries with labels"""
    
    def test_create_tag(self, client, admin_agent):
        """Test creating a tag"""
        payload = {
            'name': 'marketing',
            'color': '#FF5733',
            'description': 'Marketing-related queries'
        }
        
        response = client.post(
            '/api/admin/tags',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'tag' in data
        assert data['tag']['name'] == 'marketing'
        assert data['tag']['color'] == '#FF5733'
    
    def test_list_tags(self, client, admin_agent):
        """Test listing tags"""
        query_tagging_manager.create_tag('marketing', 'admin-agent')
        query_tagging_manager.create_tag('finance', 'admin-agent')
        
        response = client.get(
            '/api/admin/tags',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'tags' in data
        assert len(data['tags']) >= 2
    
    def test_tag_query(self, client, test_agent):
        """Test tagging a query"""
        payload = {
            'query': 'SELECT * FROM users',
            'query_type': 'SELECT',
            'tags': ['marketing', 'finance']
        }
        
        response = client.post(
            '/api/agents/test-agent/queries/tag',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'tagged_query' in data
        assert 'marketing' in data['tagged_query']['tags']
        assert 'finance' in data['tagged_query']['tags']
    
    def test_search_tagged_queries(self, client, test_agent):
        """Test searching tagged queries"""
        # Tag some queries
        query1 = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['marketing']
        )
        query2 = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM orders', 'SELECT', ['finance']
        )
        query3 = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM products', 'SELECT', ['marketing', 'sales']
        )
        
        # Search by single tag
        response = client.get(
            '/api/agents/test-agent/queries/search?tags=marketing',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['queries']) >= 2
        assert all('marketing' in q['tags'] for q in data['queries'])
    
    def test_search_by_multiple_tags(self, client, test_agent):
        """Test searching by multiple tags (AND logic)"""
        query1 = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['marketing', 'finance']
        )
        query2 = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM orders', 'SELECT', ['marketing']
        )
        
        # Search for queries with both tags
        response = client.get(
            '/api/agents/test-agent/queries/search?tags=marketing,finance',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        # Should only return query1 (has both tags)
        assert len(data['queries']) >= 1
        assert all('marketing' in q['tags'] and 'finance' in q['tags'] for q in data['queries'])
    
    def test_search_by_query_text(self, client, test_agent):
        """Test searching by query text"""
        query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['marketing']
        )
        query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM orders', 'SELECT', ['marketing']
        )
        
        response = client.get(
            '/api/agents/test-agent/queries/search?search_text=users',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all('users' in q['query'].lower() for q in data['queries'])
    
    def test_get_query_tags(self, client, test_agent):
        """Test getting tags for a query"""
        tagged_query = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['marketing', 'finance']
        )
        
        response = client.get(
            f'/api/agents/test-agent/queries/{tagged_query.query_id}/tags',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'marketing' in data['tags']
        assert 'finance' in data['tags']
    
    def test_remove_tag_from_query(self, client, test_agent):
        """Test removing a tag from a query"""
        tagged_query = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['marketing', 'finance']
        )
        
        response = client.delete(
            f'/api/agents/test-agent/queries/{tagged_query.query_id}/tags/marketing',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify tag was removed
        tags = query_tagging_manager.get_query_tags(tagged_query.query_id)
        assert 'marketing' not in tags
        assert 'finance' in tags
    
    def test_delete_tag(self, client, admin_agent):
        """Test deleting a tag"""
        query_tagging_manager.create_tag('marketing', 'admin-agent')
        tagged_query = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['marketing']
        )
        
        response = client.delete(
            '/api/admin/tags/marketing',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify tag was removed from query
        tags = query_tagging_manager.get_query_tags(tagged_query.query_id)
        assert 'marketing' not in tags
    
    def test_tag_usage_tracking(self, client, admin_agent):
        """Test that tag usage is tracked"""
        tag = query_tagging_manager.create_tag('marketing', 'admin-agent')
        
        initial_count = tag.usage_count
        
        # Tag a query
        query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['marketing']
        )
        
        # Usage count should increase
        updated_tag = query_tagging_manager.get_tag('marketing')
        assert updated_tag.usage_count == initial_count + 1
    
    def test_get_tag_statistics(self, client, admin_agent):
        """Test getting tag statistics"""
        query_tagging_manager.create_tag('marketing', 'admin-agent')
        query_tagging_manager.create_tag('finance', 'admin-agent')
        
        query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['marketing']
        )
        query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM orders', 'SELECT', ['marketing', 'finance']
        )
        
        response = client.get(
            '/api/admin/tags/statistics',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_tags' in data
        assert 'total_tagged_queries' in data
        assert 'most_used_tags' in data
        assert data['total_tagged_queries'] >= 2


class TestIntegration_AllFeatures:
    """Integration tests combining all features"""
    
    def test_complete_workflow_team_sharing_tagging(self, client, admin_agent, test_agent):
        """Test complete workflow: create team → share query → tag query"""
        # Step 1: Create team
        response = client.post(
            '/api/admin/teams',
            json={'name': 'Marketing Team', 'tags': ['marketing']},
            headers={'X-API-Key': admin_agent['api_key']}
        )
        assert response.status_code == 201
        team_id = response.get_json()['team']['team_id']
        
        # Step 2: Add member to team
        response = client.post(
            f'/api/admin/teams/{team_id}/members',
            json={'user_id': 'test-agent', 'role': 'editor'},
            headers={'X-API-Key': admin_agent['api_key']}
        )
        assert response.status_code == 200
        
        # Step 3: Share query result
        response = client.post(
            '/api/agents/test-agent/queries/share',
            json={
                'query': 'SELECT * FROM users',
                'query_type': 'SELECT',
                'result': [{'id': 1}],
                'is_public': True
            },
            headers={'X-API-Key': test_agent['api_key']}
        )
        assert response.status_code == 201
        share_id = response.get_json()['share']['share_id']
        
        # Step 4: Tag query
        response = client.post(
            '/api/agents/test-agent/queries/tag',
            json={
                'query': 'SELECT * FROM users',
                'query_type': 'SELECT',
                'tags': ['marketing', 'users']
            },
            headers={'X-API-Key': test_agent['api_key']}
        )
        assert response.status_code == 200
        
        # Step 5: Search tagged queries
        response = client.get(
            '/api/agents/test-agent/queries/search?tags=marketing',
            headers={'X-API-Key': test_agent['api_key']}
        )
        assert response.status_code == 200
        assert len(response.get_json()['queries']) >= 1
        
        # Step 6: Access shared query
        response = client.get(f'/api/shared/{share_id}')
        assert response.status_code == 200


class TestStory1_EdgeCases:
    """Story 1: Team Management - Edge Cases"""
    
    def test_team_isolation(self, client, admin_agent):
        """Test that teams have isolated agents"""
        team1 = team_manager.create_team('Team 1', 'admin-agent')
        team2 = team_manager.create_team('Team 2', 'admin-agent')
        
        agent1 = agent_registry.register_agent(
            agent_id='agent-1',
            agent_info={'name': 'Agent 1'},
            credentials={'api_key': 'key1', 'api_secret': 'secret1'}
        )
        agent2 = agent_registry.register_agent(
            agent_id='agent-2',
            agent_info={'name': 'Agent 2'},
            credentials={'api_key': 'key2', 'api_secret': 'secret2'}
        )
        
        team_manager.assign_agent_to_team('agent-1', team1.team_id)
        team_manager.assign_agent_to_team('agent-2', team2.team_id)
        
        # Verify isolation
        assert team_manager.get_team_for_agent('agent-1') == team1.team_id
        assert team_manager.get_team_for_agent('agent-2') == team2.team_id
        assert team_manager.get_team_for_agent('agent-1') != team2.team_id
    
    def test_team_database_configs(self, client, admin_agent):
        """Test that teams can have isolated database configurations"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        
        db_config = {
            'host': 'db.example.com',
            'database': 'team_db',
            'user': 'team_user'
        }
        
        team_manager.add_database_config(team.team_id, db_config)
        
        configs = team_manager.get_team_database_configs(team.team_id)
        assert len(configs) == 1
        assert configs[0]['database'] == 'team_db'


class TestStory2_EdgeCases:
    """Story 2: Query Sharing - Edge Cases"""
    
    def test_share_unauthorized_access(self, client, test_agent):
        """Test that only share creator can delete"""
        share = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM users',
            query_type='SELECT',
            result=[{'id': 1}],
            shared_by='test-agent'
        )
        
        # Try to delete as different agent
        other_agent = agent_registry.register_agent(
            agent_id='other-agent',
            agent_info={'name': 'Other'},
            credentials={'api_key': 'other-key', 'api_secret': 'other-secret'}
        )
        access_control.grant_permission('other-agent', Permission.READ)
        
        response = client.delete(
            f'/api/agents/other-agent/queries/shares/{share.share_id}',
            headers={'X-API-Key': other_agent['api_key']}
        )
        
        # Should fail or return 404
        assert response.status_code in [403, 404]
    
    def test_share_metadata(self, client, test_agent):
        """Test share with metadata"""
        share = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM users',
            query_type='SELECT',
            result=[{'id': 1}],
            shared_by='test-agent',
            metadata={'description': 'User data', 'department': 'marketing'}
        )
        
        response = client.get(f'/api/shared/{share.share_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['metadata']['description'] == 'User data'
        assert data['metadata']['department'] == 'marketing'


class TestStory3_EdgeCases:
    """Story 3: Role-Based Access - Edge Cases"""
    
    def test_viewer_cannot_edit(self, client, admin_agent):
        """Test that viewers have limited permissions"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        team.add_member('viewer-user', TeamRole.VIEWER)
        
        # Viewer should only have VIEWER permissions
        assert team.check_permission(team.team_id, 'viewer-user', TeamRole.VIEWER)
        assert not team.check_permission(team.team_id, 'viewer-user', TeamRole.EDITOR)
        assert not team.check_permission(team.team_id, 'viewer-user', TeamRole.ADMIN)
    
    def test_editor_can_edit_but_not_admin(self, client, admin_agent):
        """Test that editors have edit but not admin permissions"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        team.add_member('editor-user', TeamRole.EDITOR)
        
        assert team.check_permission(team.team_id, 'editor-user', TeamRole.VIEWER)
        assert team.check_permission(team.team_id, 'editor-user', TeamRole.EDITOR)
        assert not team.check_permission(team.team_id, 'editor-user', TeamRole.ADMIN)
    
    def test_invalid_role(self, client, admin_agent):
        """Test invalid role assignment"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        
        payload = {
            'user_id': 'user-1',
            'role': 'invalid-role'
        }
        
        response = client.post(
            f'/api/admin/teams/{team.team_id}/members',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 400


class TestStory4_EdgeCases:
    """Story 4: Query Tagging - Edge Cases"""
    
    def test_auto_create_tag(self, client, test_agent):
        """Test that tags are auto-created when tagging queries"""
        # Tag query with non-existent tag
        tagged_query = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['new-tag']
        )
        
        # Tag should be auto-created
        tag = query_tagging_manager.get_tag('new-tag')
        assert tag is not None
        assert tag.usage_count == 1
    
    def test_tag_search_case_insensitive(self, client, test_agent):
        """Test tag search is case insensitive"""
        query_tagging_manager.create_tag('Marketing', 'admin-agent')
        query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['Marketing']
        )
        
        # Search with different case
        results = query_tagging_manager.search_queries(tags=['marketing'])
        assert len(results) >= 1
    
    def test_update_query_tags(self, client, test_agent):
        """Test updating tags on existing query"""
        tagged_query = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['marketing']
        )
        
        # Update tags
        updated = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['finance'],
            query_id=tagged_query.query_id
        )
        
        assert 'finance' in updated.tags
        assert 'marketing' not in updated.tags
    
    def test_query_execution_tracking(self, client, test_agent):
        """Test that query execution is tracked"""
        tagged_query = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['marketing']
        )
        
        initial_count = tagged_query.execution_count
        
        # Record execution
        query_tagging_manager.record_query_execution(tagged_query.query_id)
        
        # Count should increase
        updated = query_tagging_manager._tagged_queries.get(tagged_query.query_id)
        assert updated.execution_count == initial_count + 1
        assert updated.last_executed_at is not None


class TestIntegration_ErrorHandling:
    """Integration tests for error handling"""
    
    def test_team_not_found(self, client, admin_agent):
        """Test handling of non-existent team"""
        response = client.get(
            '/api/admin/teams/nonexistent-id',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 404
    
    def test_share_not_found(self, client):
        """Test handling of non-existent share"""
        response = client.get('/api/shared/nonexistent-id')
        
        assert response.status_code == 404
    
    def test_tag_not_found(self, client, admin_agent):
        """Test handling of non-existent tag"""
        response = client.delete(
            '/api/admin/tags/nonexistent-tag',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 404
    
    def test_unauthorized_team_access(self, client, test_agent):
        """Test that non-admin cannot create teams"""
        response = client.post(
            '/api/admin/teams',
            json={'name': 'Test Team'},
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403
    
    def test_unauthorized_tag_creation(self, client, test_agent):
        """Test that non-admin cannot create tags"""
        response = client.post(
            '/api/admin/tags',
            json={'name': 'test-tag'},
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403


class TestStory1_AdditionalScenarios:
    """Story 1: Additional Team Management Scenarios"""
    
    def test_team_creator_is_admin(self, client, admin_agent):
        """Test that team creator is automatically added as admin"""
        response = client.post(
            '/api/admin/teams',
            json={'name': 'Test Team'},
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        team_id = response.get_json()['team']['team_id']
        
        team = team_manager.get_team(team_id)
        assert team.has_member('admin-agent')
        assert team.get_member_role('admin-agent') == TeamRole.ADMIN
    
    def test_team_member_count(self, client, admin_agent):
        """Test team member count tracking"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        team.add_member('user-1', TeamRole.VIEWER)
        team.add_member('user-2', TeamRole.EDITOR)
        
        response = client.get(
            f'/api/admin/teams/{team.team_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['member_count'] == 3  # creator + 2 members
    
    def test_team_agent_assignment_multiple(self, client, admin_agent):
        """Test assigning multiple agents to a team"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        
        agent1 = agent_registry.register_agent(
            agent_id='agent-1',
            agent_info={'name': 'Agent 1'},
            credentials={'api_key': 'key1', 'api_secret': 'secret1'}
        )
        agent2 = agent_registry.register_agent(
            agent_id='agent-2',
            agent_info={'name': 'Agent 2'},
            credentials={'api_key': 'key2', 'api_secret': 'secret2'}
        )
        
        team_manager.assign_agent_to_team('agent-1', team.team_id)
        team_manager.assign_agent_to_team('agent-2', team.team_id)
        
        assert len(team.agent_ids) == 2
        assert 'agent-1' in team.agent_ids
        assert 'agent-2' in team.agent_ids


class TestStory2_AdditionalScenarios:
    """Story 2: Additional Query Sharing Scenarios"""
    
    def test_share_link_format(self, client, test_agent):
        """Test share link format"""
        share = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM users',
            query_type='SELECT',
            result=[{'id': 1}],
            shared_by='test-agent'
        )
        
        share_link = query_sharing_manager.get_share_link(share.share_id)
        assert share.share_id in share_link
        assert '/api/shared/' in share_link
    
    def test_share_access_count_increment(self, client, test_agent):
        """Test that access count increments on each access"""
        share = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM users',
            query_type='SELECT',
            result=[{'id': 1}],
            shared_by='test-agent'
        )
        
        initial_count = share.access_count
        
        # Access multiple times
        client.get(f'/api/shared/{share.share_id}')
        client.get(f'/api/shared/{share.share_id}')
        
        updated_share = query_sharing_manager.get_share(share.share_id)
        assert updated_share.access_count == initial_count + 2
    
    def test_share_clear_expired(self, client, test_agent):
        """Test clearing expired shares"""
        # Create expired share
        from datetime import datetime, timedelta
        share = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM users',
            query_type='SELECT',
            result=[{'id': 1}],
            shared_by='test-agent',
            expires_in_hours=-1  # Already expired
        )
        
        count = query_sharing_manager.clear_expired_shares()
        assert count >= 1
        
        # Share should be removed
        assert query_sharing_manager.get_share(share.share_id) is None


class TestStory3_AdditionalScenarios:
    """Story 3: Additional Role-Based Access Scenarios"""
    
    def test_member_cannot_remove_self(self, client, admin_agent):
        """Test edge case: member removal scenarios"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        team.add_member('user-1', TeamRole.EDITOR)
        
        # Admin can remove any member
        success = team_manager.remove_team_member(team.team_id, 'user-1')
        assert success is True
        assert not team.has_member('user-1')
    
    def test_role_update_same_role(self, client, admin_agent):
        """Test updating role to same role"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        team.add_member('user-1', TeamRole.EDITOR)
        
        success = team_manager.update_member_role(team.team_id, 'user-1', TeamRole.EDITOR)
        assert success is True
        assert team.get_member_role('user-1') == TeamRole.EDITOR
    
    def test_non_member_permission_check(self, client, admin_agent):
        """Test permission check for non-member"""
        team = team_manager.create_team('Test Team', 'admin-agent')
        
        # Non-member should not have permissions
        assert not team.check_permission(team.team_id, 'non-member', TeamRole.VIEWER)
        assert not team.check_permission(team.team_id, 'non-member', TeamRole.EDITOR)
        assert not team.check_permission(team.team_id, 'non-member', TeamRole.ADMIN)


class TestStory4_AdditionalScenarios:
    """Story 4: Additional Query Tagging Scenarios"""
    
    def test_tag_with_special_characters(self, client, admin_agent):
        """Test tags with special characters"""
        tag = query_tagging_manager.create_tag(
            name='marketing-2024',
            created_by='admin-agent',
            description='Marketing queries for 2024'
        )
        
        assert tag.name == 'marketing-2024'
        
        # Tag a query with it
        tagged_query = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['marketing-2024']
        )
        
        assert 'marketing-2024' in tagged_query.tags
    
    def test_tag_color_format(self, client, admin_agent):
        """Test tag color format"""
        tag = query_tagging_manager.create_tag(
            name='marketing',
            created_by='admin-agent',
            color='#FF5733'
        )
        
        assert tag.color == '#FF5733'
    
    def test_search_with_no_results(self, client, test_agent):
        """Test search that returns no results"""
        response = client.get(
            '/api/agents/test-agent/queries/search?tags=nonexistent-tag',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['queries']) == 0
    
    def test_tag_removal_updates_usage(self, client, test_agent):
        """Test that removing tag from query updates usage count"""
        tag = query_tagging_manager.create_tag('marketing', 'admin-agent')
        tagged_query = query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['marketing']
        )
        
        initial_count = tag.usage_count
        
        # Remove tag
        query_tagging_manager.remove_tag_from_query(tagged_query.query_id, 'marketing')
        
        # Usage count should decrease
        updated_tag = query_tagging_manager.get_tag('marketing')
        assert updated_tag.usage_count == max(0, initial_count - 1)
    
    def test_query_type_filtering(self, client, test_agent):
        """Test filtering queries by query type"""
        query_tagging_manager.tag_query(
            'test-agent', 'SELECT * FROM users', 'SELECT', ['marketing']
        )
        query_tagging_manager.tag_query(
            'test-agent', 'INSERT INTO users', 'INSERT', ['marketing']
        )
        
        response = client.get(
            '/api/agents/test-agent/queries/search?query_type=SELECT',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all(q['query_type'] == 'SELECT' for q in data['queries'])


class TestIntegration_ComplexWorkflows:
    """Complex integration workflows"""
    
    def test_team_with_shared_and_tagged_queries(self, client, admin_agent, test_agent):
        """Test complete workflow: team → share → tag → search"""
        # Create team
        team = team_manager.create_team('Marketing Team', 'admin-agent')
        team.add_member('test-agent', TeamRole.EDITOR)
        
        # Share query
        share = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM users WHERE department = "marketing"',
            query_type='SELECT',
            result=[{'id': 1, 'name': 'John', 'department': 'marketing'}],
            shared_by='test-agent',
            metadata={'team_id': team.team_id}
        )
        
        # Tag query
        tagged_query = query_tagging_manager.tag_query(
            'test-agent',
            'SELECT * FROM users WHERE department = "marketing"',
            'SELECT',
            ['marketing', 'users', 'department']
        )
        
        # Search by tags
        results = query_tagging_manager.search_queries(
            tags=['marketing'],
            agent_id='test-agent'
        )
        
        assert len(results) >= 1
        assert any(r.query_id == tagged_query.query_id for r in results)
        
        # Access shared query
        shared = query_sharing_manager.get_share(share.share_id)
        assert shared is not None
        assert shared.metadata.get('team_id') == team.team_id
    
    def test_multiple_teams_isolation(self, client, admin_agent):
        """Test that multiple teams maintain isolation"""
        team1 = team_manager.create_team('Team 1', 'admin-agent')
        team2 = team_manager.create_team('Team 2', 'admin-agent')
        
        agent1 = agent_registry.register_agent(
            agent_id='agent-1',
            agent_info={'name': 'Agent 1'},
            credentials={'api_key': 'key1', 'api_secret': 'secret1'}
        )
        agent2 = agent_registry.register_agent(
            agent_id='agent-2',
            agent_info={'name': 'Agent 2'},
            credentials={'api_key': 'key2', 'api_secret': 'secret2'}
        )
        
        team_manager.assign_agent_to_team('agent-1', team1.team_id)
        team_manager.assign_agent_to_team('agent-2', team2.team_id)
        
        # Verify isolation
        assert team_manager.get_team_for_agent('agent-1') == team1.team_id
        assert team_manager.get_team_for_agent('agent-2') == team2.team_id
        
        # Verify agents are in correct teams
        assert 'agent-1' in team1.agent_ids
        assert 'agent-2' in team2.agent_ids
        assert 'agent-1' not in team2.agent_ids
        assert 'agent-2' not in team1.agent_ids
    
    def test_share_with_team_context(self, client, test_agent):
        """Test sharing query with team context in metadata"""
        share = query_sharing_manager.create_share(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            result=[{'id': 1, 'amount': 1000}],
            shared_by='test-agent',
            metadata={
                'team': 'Marketing Team',
                'department': 'Sales',
                'shared_via': 'team_link'
            }
        )
        
        shared = query_sharing_manager.get_share(share.share_id)
        assert shared.metadata['team'] == 'Marketing Team'
        assert shared.metadata['department'] == 'Sales'
    
    def test_tag_statistics_accuracy(self, client, admin_agent):
        """Test tag statistics are accurate"""
        # Create tags
        query_tagging_manager.create_tag('marketing', 'admin-agent')
        query_tagging_manager.create_tag('finance', 'admin-agent')
        query_tagging_manager.create_tag('sales', 'admin-agent')
        
        # Tag queries
        query_tagging_manager.tag_query('agent-1', 'SELECT * FROM users', 'SELECT', ['marketing'])
        query_tagging_manager.tag_query('agent-1', 'SELECT * FROM orders', 'SELECT', ['marketing', 'sales'])
        query_tagging_manager.tag_query('agent-1', 'SELECT * FROM accounts', 'SELECT', ['finance'])
        
        stats = query_tagging_manager.get_tag_statistics()
        
        assert stats['total_tags'] == 3
        assert stats['total_tagged_queries'] == 3
        
        # Marketing should be most used (2 queries)
        most_used = stats['most_used_tags']
        assert len(most_used) > 0
        marketing_tag = next((t for t in most_used if t['name'] == 'marketing'), None)
        assert marketing_tag is not None
        assert marketing_tag['usage_count'] == 2

