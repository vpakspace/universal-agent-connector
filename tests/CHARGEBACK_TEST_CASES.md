# Chargeback Test Cases

This document describes comprehensive test scenarios for the chargeback and cost allocation system.

## Test Categories

1. [Usage Recording](#usage-recording)
2. [Allocation Rules](#allocation-rules)
3. [Cost Allocation](#cost-allocation)
4. [Invoice Generation](#invoice-generation)
5. [Usage Summary](#usage-summary)
6. [API Endpoints](#api-endpoints)
7. [Edge Cases and Error Handling](#edge-cases-and-error-handling)

---

## Usage Recording

### Test Case: Record Basic Usage
**Objective**: Verify that basic usage records can be created

**Steps**:
1. Record usage with team_id, user_id, resource_type, quantity, cost_usd
2. Verify usage record is created with correct fields
3. Verify usage_id is auto-generated
4. Verify timestamp is set

**Expected Result**: Usage record created successfully with all fields populated

---

### Test Case: Record Usage with Metadata
**Objective**: Verify that metadata can be attached to usage records

**Steps**:
1. Record usage with metadata dictionary (e.g., query_id, database name)
2. Verify metadata is stored correctly
3. Retrieve usage record and verify metadata is preserved

**Expected Result**: Metadata is stored and retrieved correctly

---

### Test Case: Record Usage with Minimal Data
**Objective**: Verify that usage can be recorded with minimal required fields

**Steps**:
1. Record usage with only cost_usd
2. Verify record is created with defaults for optional fields
3. Verify resource_type defaults to "query"

**Expected Result**: Usage record created with defaults for optional fields

---

### Test Case: Multiple Usage Records
**Objective**: Verify that multiple usage records can be created independently

**Steps**:
1. Record multiple usage records with different attributes
2. Verify each has unique usage_id
3. Verify all records are stored independently

**Expected Result**: Multiple records created with unique IDs

---

## Allocation Rules

### Test Case: Create By-Usage Rule
**Objective**: Verify creation of allocation rule that allocates by actual usage

**Steps**:
1. Create allocation rule with type "by_usage"
2. Verify rule is stored with correct type
3. Verify rule is enabled by default

**Expected Result**: Rule created successfully

---

### Test Case: Create By-Team Rule
**Objective**: Verify creation of allocation rule that splits costs equally among team members

**Steps**:
1. Create allocation rule with type "by_team" and team_id
2. Verify rule is stored with team_id
3. Verify rule type is "by_team"

**Expected Result**: Rule created with team_id association

---

### Test Case: Create By-User Rule
**Objective**: Verify creation of allocation rule that allocates to specific users

**Steps**:
1. Create allocation rule with type "by_user" and user_ids list
2. Verify rule is stored with user_ids
3. Verify rule type is "by_user"

**Expected Result**: Rule created with user_ids list

---

### Test Case: Create Fixed Split Rule
**Objective**: Verify creation of allocation rule with fixed percentage split

**Steps**:
1. Create allocation rule with type "fixed_split" and split_percentages (e.g., team-1: 60%, team-2: 40%)
2. Verify rule is stored with split_percentages
3. Verify percentages are stored correctly

**Expected Result**: Rule created with split percentages

---

### Test Case: Create Equal Split Rule
**Objective**: Verify creation of allocation rule that splits costs equally among entities

**Steps**:
1. Create allocation rule with type "equal_split" and entity IDs
2. Verify rule is stored correctly
3. Verify rule type is "equal_split"

**Expected Result**: Rule created successfully

---

### Test Case: List Allocation Rules
**Objective**: Verify that allocation rules can be listed

**Steps**:
1. Create multiple allocation rules
2. List all rules
3. Verify all rules are returned
4. Filter by team_id
5. Filter by enabled_only=true
6. Verify filters work correctly

**Expected Result**: Rules listed correctly with filters applied

---

### Test Case: Get Allocation Rule by ID
**Objective**: Verify that a specific allocation rule can be retrieved by ID

**Steps**:
1. Create allocation rule
2. Get rule by ID
3. Verify rule details match
4. Attempt to get non-existent rule
5. Verify 404 error is returned

**Expected Result**: Rule retrieved correctly, non-existent rule returns 404

---

### Test Case: Update Allocation Rule
**Objective**: Verify that allocation rules can be updated

**Steps**:
1. Create allocation rule
2. Update rule name, description, enabled status
3. Verify updates are applied
4. Verify updated_at timestamp is updated

**Expected Result**: Rule updated successfully

---

### Test Case: Delete Allocation Rule
**Objective**: Verify that allocation rules can be deleted

**Steps**:
1. Create allocation rule
2. Delete rule by ID
3. Verify rule is removed
4. Attempt to delete non-existent rule
5. Verify appropriate response

**Expected Result**: Rule deleted successfully, non-existent rule returns appropriate error

---

## Cost Allocation

### Test Case: Allocate Costs By Usage (Default)
**Objective**: Verify default allocation method allocates costs by actual usage

**Steps**:
1. Create usage records for multiple teams/users
2. Allocate costs without specifying a rule (default behavior)
3. Verify each team/user gets allocated costs equal to their usage
4. Verify usage_records are linked to allocations

**Expected Result**: Costs allocated directly by usage, totals match

---

### Test Case: Allocate Costs By Team (Equal Split)
**Objective**: Verify that team-based allocation splits costs equally among team members

**Steps**:
1. Create usage records for a team with 2 users (user-1: $10, user-2: $20)
2. Create by_team allocation rule
3. Allocate costs using the rule
4. Verify each user gets equal share ($15 each)
5. Verify total allocated equals total usage ($30)

**Expected Result**: Costs split equally among team members

---

### Test Case: Allocate Costs By User
**Objective**: Verify that user-based allocation allocates costs to specific users

**Steps**:
1. Create usage records for multiple users
2. Create by_user allocation rule with specific user_ids
3. Allocate costs using the rule
4. Verify only specified users receive allocations
5. Verify each user's allocation matches their usage

**Expected Result**: Costs allocated only to specified users

---

### Test Case: Allocate Costs With Fixed Split
**Objective**: Verify that fixed split allocation distributes costs by percentages

**Steps**:
1. Create usage records with total cost of $100
2. Create fixed_split rule with 60/40 split (team-1: 60%, team-2: 40%)
3. Allocate costs using the rule
4. Verify team-1 gets $60, team-2 gets $40
5. Verify totals match

**Expected Result**: Costs allocated according to fixed percentages

---

### Test Case: Fixed Split Invalid Percentages
**Objective**: Verify that fixed split rule validates percentage sum equals 100%

**Steps**:
1. Create fixed_split rule with percentages that don't sum to 100% (e.g., 60% + 50% = 110%)
2. Attempt to allocate costs
3. Verify ValueError is raised
4. Verify error message indicates percentage sum issue

**Expected Result**: Allocation fails with appropriate error

---

### Test Case: Allocate Costs With Equal Split
**Objective**: Verify that equal split allocation divides costs equally among entities

**Steps**:
1. Create usage records with total cost of $150
2. Create equal_split rule with 3 entities
3. Allocate costs using the rule
4. Verify each entity gets $50
5. Verify totals match

**Expected Result**: Costs split equally among entities

---

### Test Case: Allocate Costs for Empty Period
**Objective**: Verify that allocating costs for a period with no usage returns empty list

**Steps**:
1. Create usage records outside the target period
2. Allocate costs for a period with no usage
3. Verify empty list is returned

**Expected Result**: Empty list returned, no allocations created

---

### Test Case: Allocate Costs Filtered by Team
**Objective**: Verify that allocation can be filtered by team

**Steps**:
1. Create usage records for multiple teams
2. Allocate costs filtered by specific team_id
3. Verify only allocations for that team are returned
4. Verify totals match team's usage

**Expected Result**: Only filtered team's allocations returned

---

### Test Case: Allocate Costs With Multiple Rules
**Objective**: Verify that multiple rules can be applied

**Steps**:
1. Create multiple allocation rules
2. Allocate costs without specifying a rule_id (uses all enabled rules)
3. Verify allocations are created according to all applicable rules

**Expected Result**: Allocations created for all applicable rules

---

## Invoice Generation

### Test Case: Generate Invoice from Allocated Costs
**Objective**: Verify that invoices can be generated from allocated costs

**Steps**:
1. Create usage records
2. Allocate costs
3. Generate invoice for period
4. Verify invoice is created with correct invoice_id and invoice_number
5. Verify line items are created
6. Verify totals match allocated costs

**Expected Result**: Invoice generated with correct line items and totals

---

### Test Case: Generate Invoice Auto-Allocates Costs
**Objective**: Verify that invoice generation automatically allocates costs if not provided

**Steps**:
1. Create usage records
2. Generate invoice without pre-allocating costs
3. Verify costs are automatically allocated
4. Verify invoice is generated from allocations

**Expected Result**: Costs automatically allocated and invoice generated

---

### Test Case: Generate Invoice with Custom Invoice Number
**Objective**: Verify that custom invoice numbers can be specified

**Steps**:
1. Create usage records and allocate costs
2. Generate invoice with custom invoice_number
3. Verify invoice uses the specified invoice_number

**Expected Result**: Invoice created with custom invoice number

---

### Test Case: Generate Invoice Filtered by Team/User
**Objective**: Verify that invoices can be generated for specific team or user

**Steps**:
1. Create usage records for multiple teams/users
2. Generate invoice filtered by team_id
3. Verify invoice only includes costs for that team
4. Generate invoice filtered by user_id
5. Verify invoice only includes costs for that user

**Expected Result**: Invoice filtered correctly by team/user

---

### Test Case: Generate Invoice Line Items by Resource Type
**Objective**: Verify that invoice line items are grouped by resource type

**Steps**:
1. Create usage records with different resource types (query, storage, compute)
2. Generate invoice
3. Verify line items are grouped by resource_type
4. Verify each line item has correct totals

**Expected Result**: Line items grouped by resource type

---

### Test Case: Invoice Status Management
**Objective**: Verify that invoice status can be updated

**Steps**:
1. Generate invoice (default status: draft)
2. Update status to "sent"
3. Verify status is updated
4. Update status to "paid"
5. Verify status is updated and paid_date is set
6. Verify updated_at timestamp is updated

**Expected Result**: Invoice status updated correctly, paid_date set when status is "paid"

---

### Test Case: List Invoices
**Objective**: Verify that invoices can be listed with filters

**Steps**:
1. Generate multiple invoices
2. List all invoices
3. Verify all invoices are returned, sorted by created_at (newest first)
4. Filter by team_id
5. Filter by user_id
6. Filter by status
7. Verify filters work correctly

**Expected Result**: Invoices listed correctly with filters applied

---

### Test Case: Get Invoice by ID
**Objective**: Verify that a specific invoice can be retrieved by ID

**Steps**:
1. Generate invoice
2. Get invoice by ID
3. Verify invoice details match
4. Attempt to get non-existent invoice
5. Verify 404 error is returned

**Expected Result**: Invoice retrieved correctly, non-existent invoice returns 404

---

## Usage Summary

### Test Case: Get Usage Summary by Period
**Objective**: Verify that usage summary can be retrieved for a period

**Steps**:
1. Create usage records with various resource types and agents
2. Get usage summary for the period
3. Verify total_cost_usd matches sum of all usage records
4. Verify total_quantity matches sum of all quantities
5. Verify record_count matches number of records

**Expected Result**: Summary statistics are accurate

---

### Test Case: Get Usage Summary Grouped by Resource Type
**Objective**: Verify that usage summary groups costs by resource type

**Steps**:
1. Create usage records with different resource types (query, storage, compute)
2. Get usage summary
3. Verify by_resource_type contains breakdown by type
4. Verify totals match individual resource type totals

**Expected Result**: Costs correctly grouped by resource type

---

### Test Case: Get Usage Summary Grouped by Agent
**Objective**: Verify that usage summary groups costs by agent

**Steps**:
1. Create usage records with different agent_ids
2. Get usage summary
3. Verify by_agent contains breakdown by agent
4. Verify totals match individual agent totals

**Expected Result**: Costs correctly grouped by agent

---

### Test Case: Get Usage Summary Filtered by Team
**Objective**: Verify that usage summary can be filtered by team

**Steps**:
1. Create usage records for multiple teams
2. Get usage summary filtered by team_id
3. Verify summary only includes records for that team
4. Verify totals match team's usage

**Expected Result**: Summary filtered correctly by team

---

### Test Case: Get Usage Summary Filtered by User
**Objective**: Verify that usage summary can be filtered by user

**Steps**:
1. Create usage records for multiple users
2. Get usage summary filtered by user_id
3. Verify summary only includes records for that user
4. Verify totals match user's usage

**Expected Result**: Summary filtered correctly by user

---

## API Endpoints

### Test Case: POST /api/chargeback/usage
**Objective**: Verify usage recording endpoint

**Steps**:
1. POST usage record with valid data
2. Verify 201 status code
3. Verify usage_record is returned
4. Test with minimal data
5. Test with invalid data (missing required fields)
6. Verify appropriate error responses

**Expected Result**: Usage recorded successfully via API

---

### Test Case: GET /api/chargeback/allocation-rules
**Objective**: Verify allocation rules listing endpoint

**Steps**:
1. Create multiple allocation rules
2. GET /api/chargeback/allocation-rules
3. Verify 200 status code
4. Verify rules list is returned
5. Test with query parameters (team_id, enabled_only)
6. Verify filters work correctly

**Expected Result**: Rules listed correctly via API

---

### Test Case: POST /api/chargeback/allocation-rules
**Objective**: Verify allocation rule creation endpoint

**Steps**:
1. POST new allocation rule with valid data
2. Verify 201 status code
3. Verify rule is created
4. Test with missing required fields
5. Verify appropriate error responses

**Expected Result**: Rule created successfully via API

---

### Test Case: GET /api/chargeback/allocation-rules/{rule_id}
**Objective**: Verify allocation rule retrieval endpoint

**Steps**:
1. Create allocation rule
2. GET rule by ID
3. Verify 200 status code
4. Verify rule details are returned
5. GET non-existent rule
6. Verify 404 status code

**Expected Result**: Rule retrieved correctly via API

---

### Test Case: PUT /api/chargeback/allocation-rules/{rule_id}
**Objective**: Verify allocation rule update endpoint

**Steps**:
1. Create allocation rule
2. PUT updated rule data
3. Verify 200 status code
4. Verify rule is updated
5. PUT to non-existent rule
6. Verify 404 status code

**Expected Result**: Rule updated successfully via API

---

### Test Case: DELETE /api/chargeback/allocation-rules/{rule_id}
**Objective**: Verify allocation rule deletion endpoint

**Steps**:
1. Create allocation rule
2. DELETE rule by ID
3. Verify 200 status code
4. Verify rule is deleted
5. DELETE non-existent rule
6. Verify appropriate response

**Expected Result**: Rule deleted successfully via API

---

### Test Case: POST /api/chargeback/allocate
**Objective**: Verify cost allocation endpoint

**Steps**:
1. Create usage records
2. POST allocation request with period_start and period_end
3. Verify 200 status code
4. Verify allocations are returned
5. Test with rule_id parameter
6. Test with team_id filter
7. Test with missing period
8. Verify appropriate error responses

**Expected Result**: Costs allocated successfully via API

---

### Test Case: POST /api/chargeback/invoices
**Objective**: Verify invoice generation endpoint

**Steps**:
1. Create usage records
2. POST invoice generation request
3. Verify 201 status code
4. Verify invoice is returned
5. Test with team_id/user_id filters
6. Test with custom invoice_number
7. Test with missing period
8. Verify appropriate error responses

**Expected Result**: Invoice generated successfully via API

---

### Test Case: GET /api/chargeback/invoices
**Objective**: Verify invoice listing endpoint

**Steps**:
1. Generate multiple invoices
2. GET /api/chargeback/invoices
3. Verify 200 status code
4. Verify invoices list is returned
5. Test with query parameters (team_id, user_id, status)
6. Verify filters work correctly

**Expected Result**: Invoices listed correctly via API

---

### Test Case: GET /api/chargeback/invoices/{invoice_id}
**Objective**: Verify invoice retrieval endpoint

**Steps**:
1. Generate invoice
2. GET invoice by ID
3. Verify 200 status code
4. Verify invoice details are returned
5. GET non-existent invoice
6. Verify 404 status code

**Expected Result**: Invoice retrieved correctly via API

---

### Test Case: PUT /api/chargeback/invoices/{invoice_id}/status
**Objective**: Verify invoice status update endpoint

**Steps**:
1. Generate invoice
2. PUT status update (e.g., "sent")
3. Verify 200 status code
4. Verify invoice status is updated
5. Test with invalid status
6. Test with non-existent invoice
7. Verify appropriate error responses

**Expected Result**: Invoice status updated successfully via API

---

### Test Case: GET /api/chargeback/usage/summary
**Objective**: Verify usage summary endpoint

**Steps**:
1. Create usage records
2. GET usage summary with period_start and period_end
3. Verify 200 status code
4. Verify summary is returned
5. Test with team_id/user_id filters
6. Test with missing period
7. Verify appropriate error responses

**Expected Result**: Usage summary retrieved correctly via API

---

## Edge Cases and Error Handling

### Test Case: Invalid Allocation Rule Type
**Objective**: Verify that invalid rule types are rejected

**Steps**:
1. Attempt to create allocation rule with invalid rule_type
2. Verify appropriate error is returned

**Expected Result**: Invalid rule type rejected with error

---

### Test Case: Fixed Split Percentages Don't Sum to 100%
**Objective**: Verify that fixed split rule validates percentage sum

**Steps**:
1. Create fixed_split rule with percentages summing to 110%
2. Attempt to allocate costs
3. Verify ValueError is raised

**Expected Result**: Allocation fails with validation error

---

### Test Case: Invoice Status Transition Validation
**Objective**: Verify that invalid status transitions are handled

**Steps**:
1. Generate invoice (status: draft)
2. Attempt to set invalid status
3. Verify appropriate error is returned

**Expected Result**: Invalid status transitions rejected

---

### Test Case: Allocate Costs with Disabled Rule
**Objective**: Verify that disabled rules are not applied

**Steps**:
1. Create allocation rule with enabled=False
2. Attempt to allocate costs
3. Verify rule is not applied

**Expected Result**: Disabled rules are skipped

---

### Test Case: Generate Invoice with No Usage
**Objective**: Verify that invoice generation handles periods with no usage

**Steps**:
1. Generate invoice for period with no usage records
2. Verify invoice is created with zero totals
3. Verify line items are empty or minimal

**Expected Result**: Invoice created with zero totals

---

### Test Case: Concurrent Usage Recording
**Objective**: Verify that concurrent usage recordings don't interfere

**Steps**:
1. Record multiple usage records concurrently (simulated)
2. Verify all records are created with unique IDs
3. Verify no data corruption occurs

**Expected Result**: Concurrent operations handled correctly

---

### Test Case: Large Number of Usage Records
**Objective**: Verify that system handles large volumes of usage records

**Steps**:
1. Create large number of usage records (e.g., 10,000)
2. Allocate costs for period
3. Generate invoice
4. Verify performance is acceptable
5. Verify results are accurate

**Expected Result**: System handles large volumes correctly

---

### Test Case: Date Range Edge Cases
**Objective**: Verify that date range filtering works correctly at boundaries

**Steps**:
1. Create usage records at period boundaries
2. Allocate costs with exact boundary dates
3. Verify records at boundaries are included correctly

**Expected Result**: Date range filtering works correctly at boundaries

---

### Test Case: Missing Optional Fields
**Objective**: Verify that missing optional fields are handled gracefully

**Steps**:
1. Create usage records with minimal data (only cost_usd)
2. Create allocation rules with minimal data
3. Verify defaults are applied correctly
4. Verify operations succeed

**Expected Result**: Missing optional fields handled with defaults

---

## Performance Tests

### Test Case: Allocate Costs Performance
**Objective**: Verify that cost allocation performs well with large datasets

**Steps**:
1. Create 1,000 usage records
2. Measure time to allocate costs
3. Verify allocation completes within acceptable time
4. Verify results are accurate

**Expected Result**: Allocation completes efficiently

---

### Test Case: Invoice Generation Performance
**Objective**: Verify that invoice generation performs well

**Steps**:
1. Create large number of allocations
2. Measure time to generate invoice
3. Verify invoice generation completes within acceptable time
4. Verify invoice is correct

**Expected Result**: Invoice generation completes efficiently

---

## Integration Tests

### Test Case: End-to-End Chargeback Flow
**Objective**: Verify complete chargeback workflow

**Steps**:
1. Record usage for multiple teams/users over a period
2. Create allocation rules
3. Allocate costs
4. Generate invoices
5. Update invoice statuses
6. Retrieve usage summaries
7. Verify all steps work together correctly

**Expected Result**: Complete workflow executes successfully

---

### Test Case: Multiple Periods
**Objective**: Verify that multiple billing periods can be handled independently

**Steps**:
1. Record usage for January
2. Allocate costs and generate invoice for January
3. Record usage for February
4. Allocate costs and generate invoice for February
5. Verify periods are handled independently
6. Verify summaries are correct for each period

**Expected Result**: Multiple periods handled correctly

---

