# Teams & Collaboration Stories - Test Summary

This document summarizes the test cases for the 4 Teams & Collaboration stories.

## Stories Implemented

1. **Story 1**: As an Organization Admin, I want to create teams with isolated database connections and agents, so that different departments can operate independently.

2. **Story 2**: As a Team Member, I want to share query results with colleagues via a link, so that insights are easily distributed.

3. **Story 3**: As an Admin, I want to assign role-based access (viewer, editor, admin) to team members, so that permissions are granular.

4. **Story 4**: As a User, I want to tag queries with labels (e.g., "marketing," "finance"), so that activity is organized and searchable.

## Test Coverage Summary

| Story | Test Cases | Status |
|-------|-----------|--------|
| Story 1: Team Management | 7 tests | ✅ Complete |
| Story 1: Edge Cases | 2 tests | ✅ Complete |
| Story 1: Additional Scenarios | 3 tests | ✅ Complete |
| Story 2: Query Sharing | 8 tests | ✅ Complete |
| Story 2: Edge Cases | 2 tests | ✅ Complete |
| Story 2: Additional Scenarios | 3 tests | ✅ Complete |
| Story 3: Role-Based Access | 5 tests | ✅ Complete |
| Story 3: Edge Cases | 3 tests | ✅ Complete |
| Story 3: Additional Scenarios | 3 tests | ✅ Complete |
| Story 4: Query Tagging | 10 tests | ✅ Complete |
| Story 4: Edge Cases | 4 tests | ✅ Complete |
| Story 4: Additional Scenarios | 5 tests | ✅ Complete |
| Integration Tests | 1 test | ✅ Complete |
| Complex Workflows | 4 tests | ✅ Complete |
| Error Handling Tests | 5 tests | ✅ Complete |
| **Total** | **66 tests** | ✅ **Complete** |

## Test File

**`tests/test_teams_collaboration_stories.py`** - Comprehensive integration tests for all teams and collaboration features.

## API Endpoints

### Story 1: Team Management

- **POST** `/api/admin/teams` - Create team
- **GET** `/api/admin/teams` - List teams (with filtering)
- **GET** `/api/admin/teams/<team_id>` - Get team
- **PUT** `/api/admin/teams/<team_id>` - Update team
- **DELETE** `/api/admin/teams/<team_id>` - Delete team
- **POST** `/api/admin/teams/<team_id>/members` - Add team member
- **DELETE** `/api/admin/teams/<team_id>/members/<user_id>` - Remove team member
- **PUT** `/api/admin/teams/<team_id>/members/<user_id>/role` - Update member role
- **POST** `/api/admin/teams/<team_id>/agents/<agent_id>` - Assign agent to team

### Story 2: Query Sharing

- **POST** `/api/agents/<agent_id>/queries/share` - Share query result
- **GET** `/api/shared/<share_id>` - Get shared query (public access)
- **GET** `/api/agents/<agent_id>/queries/shares` - List shared queries
- **DELETE** `/api/agents/<agent_id>/queries/shares/<share_id>` - Delete share
- **GET** `/api/shared/<share_id>/stats` - Get share statistics

### Story 3: Role-Based Access

- Uses team management endpoints with role assignment
- Role hierarchy: VIEWER < EDITOR < ADMIN
- Permission checking via `team_manager.check_permission()`

### Story 4: Query Tagging

- **POST** `/api/admin/tags` - Create tag
- **GET** `/api/admin/tags` - List tags
- **POST** `/api/agents/<agent_id>/queries/tag` - Tag a query
- **GET** `/api/agents/<agent_id>/queries/search` - Search tagged queries
- **GET** `/api/agents/<agent_id>/queries/<query_id>/tags` - Get query tags
- **DELETE** `/api/agents/<agent_id>/queries/<query_id>/tags/<tag_name>` - Remove tag from query
- **DELETE** `/api/admin/tags/<tag_name>` - Delete tag
- **GET** `/api/admin/tags/statistics` - Get tag statistics

## Running the Tests

```bash
# Run all teams & collaboration story tests
pytest tests/test_teams_collaboration_stories.py -v

# Run specific story tests
pytest tests/test_teams_collaboration_stories.py::TestStory1_TeamManagement -v
pytest tests/test_teams_collaboration_stories.py::TestStory2_QuerySharing -v
pytest tests/test_teams_collaboration_stories.py::TestStory3_RoleBasedAccess -v
pytest tests/test_teams_collaboration_stories.py::TestStory4_QueryTagging -v

# Run edge cases
pytest tests/test_teams_collaboration_stories.py -k "EdgeCases" -v

# Run integration tests
pytest tests/test_teams_collaboration_stories.py::TestIntegration_AllFeatures -v
```

## Implementation Details

### Team Manager (`teams.py`)

- Team creation with isolated resources
- Member management with roles
- Agent assignment to teams
- Database configuration per team
- Role-based permission checking
- Tag-based team organization

### Query Sharing Manager (`query_sharing.py`)

- Shareable link generation
- Password protection
- Expiration dates
- Access count limits
- Public/private shares
- Metadata support
- Access statistics

### Query Tagging Manager (`query_tagging.py`)

- Tag creation and management
- Query tagging with multiple tags
- Tag-based search (AND logic)
- Text search in queries
- Auto-creation of tags
- Usage tracking
- Tag statistics

## Example Usage

### 1. Create Team and Add Members

```bash
# Create team
POST /api/admin/teams
{
  "name": "Marketing Team",
  "description": "Marketing department",
  "tags": ["marketing"]
}

# Add member with role
POST /api/admin/teams/{team_id}/members
{
  "user_id": "user-1",
  "role": "editor"
}
```

### 2. Share Query Result

```bash
POST /api/agents/{agent_id}/queries/share
{
  "query": "SELECT * FROM users",
  "query_type": "SELECT",
  "result": [...],
  "expires_in_hours": 24,
  "is_public": true
}

# Access via link
GET /api/shared/{share_id}
```

### 3. Tag Queries

```bash
# Create tag
POST /api/admin/tags
{
  "name": "marketing",
  "color": "#FF5733"
}

# Tag query
POST /api/agents/{agent_id}/queries/tag
{
  "query": "SELECT * FROM users",
  "query_type": "SELECT",
  "tags": ["marketing", "finance"]
}

# Search by tags
GET /api/agents/{agent_id}/queries/search?tags=marketing,finance
```

## Test Categories

### ✅ Basic Functionality Tests
- Core feature operations
- API endpoint interactions
- Data flow and responses
- Success scenarios

### ✅ Edge Case Tests
- Resource isolation
- Permission boundaries
- Password protection
- Expiration handling
- Access limits
- Auto-creation
- Case sensitivity

### ✅ Integration Tests
- Multi-feature workflows
- Feature interactions
- End-to-end scenarios

### ✅ Error Handling
- Not found scenarios
- Unauthorized access
- Invalid inputs
- Permission violations

## Notes

- Teams provide complete resource isolation (agents, databases)
- Query sharing supports password protection and expiration
- Role-based access uses hierarchical permissions (viewer < editor < admin)
- Query tagging supports auto-creation and multi-tag search
- All features integrate seamlessly with existing agent and query systems
- Team isolation ensures departments can operate independently
- Share links are publicly accessible (unless password-protected)
- Tags are automatically created when used in queries
- Tag search uses AND logic (query must have all specified tags)

