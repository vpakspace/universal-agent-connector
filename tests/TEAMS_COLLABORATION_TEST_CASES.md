# Teams & Collaboration Stories - Complete Test Cases

This document lists all test cases for the 4 Teams & Collaboration stories.

## Test File
**`tests/test_teams_collaboration_stories.py`** - 66 comprehensive test cases

---

## Story 1: Team Management (12 tests)

### Basic Functionality
1. **test_create_team** - Create a team with name, description, and tags
2. **test_list_teams** - List all teams
3. **test_get_team** - Get a specific team
4. **test_update_team** - Update team details
5. **test_delete_team** - Delete a team
6. **test_assign_agent_to_team** - Assign an agent to a team
7. **test_filter_teams_by_tags** - Filter teams by tags

### Edge Cases
8. **test_team_isolation** - Verify teams have isolated agents
9. **test_team_database_configs** - Verify teams can have isolated database configurations

### Additional Scenarios
10. **test_team_creator_is_admin** - Team creator is automatically added as admin
11. **test_team_member_count** - Team member count tracking
12. **test_team_agent_assignment_multiple** - Assigning multiple agents to a team

---

## Story 2: Query Sharing (13 tests)

### Basic Functionality
1. **test_share_query_result** - Share a query result with link
2. **test_get_shared_query** - Get shared query via link
3. **test_share_with_password** - Password-protected shares
4. **test_share_expiration** - Share expiration handling
5. **test_share_access_limit** - Access count limits
6. **test_list_shared_queries** - List shared queries for an agent
7. **test_delete_shared_query** - Delete a shared query
8. **test_get_share_stats** - Get share statistics

### Edge Cases
9. **test_share_unauthorized_access** - Only creator can delete
10. **test_share_metadata** - Share with metadata

### Additional Scenarios
11. **test_share_link_format** - Verify share link format
12. **test_share_access_count_increment** - Access count increments correctly
13. **test_share_clear_expired** - Clearing expired shares

---

## Story 3: Role-Based Access (11 tests)

### Basic Functionality
1. **test_add_team_member** - Add a member to a team
2. **test_remove_team_member** - Remove a member from a team
3. **test_update_member_role** - Update a member's role
4. **test_role_hierarchy** - Verify role hierarchy (viewer < editor < admin)
5. **test_filter_teams_by_user** - Filter teams by user membership

### Edge Cases
6. **test_viewer_cannot_edit** - Viewers have limited permissions
7. **test_editor_can_edit_but_not_admin** - Editors have edit but not admin permissions
8. **test_invalid_role** - Handle invalid role assignment

### Additional Scenarios
9. **test_member_cannot_remove_self** - Member removal scenarios
10. **test_role_update_same_role** - Updating role to same role
11. **test_non_member_permission_check** - Permission check for non-members

---

## Story 4: Query Tagging (19 tests)

### Basic Functionality
1. **test_create_tag** - Create a tag with name, color, description
2. **test_list_tags** - List all tags
3. **test_tag_query** - Tag a query with multiple tags
4. **test_search_tagged_queries** - Search queries by single tag
5. **test_search_by_multiple_tags** - Search by multiple tags (AND logic)
6. **test_search_by_query_text** - Search by query text
7. **test_get_query_tags** - Get tags for a query
8. **test_remove_tag_from_query** - Remove a tag from a query
9. **test_delete_tag** - Delete a tag (removes from all queries)
10. **test_tag_usage_tracking** - Verify tag usage is tracked

### Edge Cases
11. **test_auto_create_tag** - Tags are auto-created when tagging queries
12. **test_tag_search_case_insensitive** - Tag search is case insensitive
13. **test_update_query_tags** - Update tags on existing query
14. **test_query_execution_tracking** - Query execution is tracked

### Additional Scenarios
15. **test_tag_with_special_characters** - Tags with special characters
16. **test_tag_color_format** - Tag color format validation
17. **test_search_with_no_results** - Search that returns no results
18. **test_tag_removal_updates_usage** - Removing tag updates usage count
19. **test_query_type_filtering** - Filtering queries by query type

---

## Integration Tests (14 tests)

### Basic Integration
1. **test_complete_workflow_team_sharing_tagging** - Complete workflow combining all features

### Error Handling
2. **test_team_not_found** - Handle non-existent team
3. **test_share_not_found** - Handle non-existent share
4. **test_tag_not_found** - Handle non-existent tag
5. **test_unauthorized_team_access** - Non-admin cannot create teams
6. **test_unauthorized_tag_creation** - Non-admin cannot create tags

### Complex Workflows
7. **test_team_with_shared_and_tagged_queries** - Team → share → tag → search workflow
8. **test_multiple_teams_isolation** - Multiple teams maintain isolation
9. **test_share_with_team_context** - Sharing with team context in metadata
10. **test_tag_statistics_accuracy** - Tag statistics are accurate

---

## Test Coverage Summary

| Category | Count |
|----------|-------|
| Story 1: Team Management | 12 tests |
| Story 2: Query Sharing | 13 tests |
| Story 3: Role-Based Access | 11 tests |
| Story 4: Query Tagging | 19 tests |
| Integration Tests | 5 tests |
| Complex Workflows | 4 tests |
| Error Handling | 5 tests |
| **Total** | **66 tests** |

---

## Running Tests

```bash
# Run all teams & collaboration tests
pytest tests/test_teams_collaboration_stories.py -v

# Run specific story tests
pytest tests/test_teams_collaboration_stories.py::TestStory1_TeamManagement -v
pytest tests/test_teams_collaboration_stories.py::TestStory1_EdgeCases -v
pytest tests/test_teams_collaboration_stories.py::TestStory2_QuerySharing -v
pytest tests/test_teams_collaboration_stories.py::TestStory2_EdgeCases -v
pytest tests/test_teams_collaboration_stories.py::TestStory3_RoleBasedAccess -v
pytest tests/test_teams_collaboration_stories.py::TestStory3_EdgeCases -v
pytest tests/test_teams_collaboration_stories.py::TestStory4_QueryTagging -v
pytest tests/test_teams_collaboration_stories.py::TestStory4_EdgeCases -v

# Run integration tests
pytest tests/test_teams_collaboration_stories.py::TestIntegration_AllFeatures -v
pytest tests/test_teams_collaboration_stories.py::TestIntegration_ErrorHandling -v

# Run only edge cases
pytest tests/test_teams_collaboration_stories.py -k "EdgeCases" -v
```

---

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
- Invalid inputs

### ✅ Integration Tests
- Multi-feature workflows
- Feature interactions
- End-to-end scenarios
- Error handling

---

## Key Test Scenarios Covered

### Team Management
- ✅ Team creation with metadata
- ✅ Team listing and filtering
- ✅ Agent assignment to teams
- ✅ Database configuration per team
- ✅ Team isolation verification
- ✅ Tag-based organization

### Query Sharing
- ✅ Shareable link generation
- ✅ Password protection
- ✅ Expiration dates
- ✅ Access count limits
- ✅ Public/private shares
- ✅ Metadata support
- ✅ Access statistics
- ✅ Unauthorized access prevention

### Role-Based Access
- ✅ Role assignment (viewer, editor, admin)
- ✅ Role hierarchy enforcement
- ✅ Permission checking
- ✅ Member management
- ✅ Role updates
- ✅ Invalid role handling

### Query Tagging
- ✅ Tag creation and management
- ✅ Multi-tag queries
- ✅ Tag-based search (AND logic)
- ✅ Text search in queries
- ✅ Auto-tag creation
- ✅ Usage tracking
- ✅ Tag statistics
- ✅ Tag removal
- ✅ Case-insensitive search

### Integration
- ✅ Complete workflows
- ✅ Feature interactions
- ✅ Error handling
- ✅ Permission enforcement

---

## Notes

- All tests use real component instances for integration testing
- Teams provide complete resource isolation
- Query sharing supports multiple security options
- Role-based access uses hierarchical permissions
- Query tagging supports flexible search and organization
- Edge cases ensure robust error handling
- Integration tests verify features work together seamlessly

