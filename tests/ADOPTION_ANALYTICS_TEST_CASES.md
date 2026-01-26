# Adoption Analytics Test Cases

This document describes comprehensive test scenarios for the adoption analytics system.

## Test Categories

1. [Telemetry Tracking](#telemetry-tracking)
2. [Opt-In/Opt-Out](#opt-inopt-out)
3. [Daily Active Users (DAU)](#daily-active-users-dau)
4. [Query Patterns](#query-patterns)
5. [Feature Usage](#feature-usage)
6. [Data Export](#data-export)
7. [API Endpoints](#api-endpoints)
8. [Privacy & Anonymization](#privacy--anonymization)
9. [Edge Cases and Error Handling](#edge-cases-and-error-handling)

---

## Telemetry Tracking

### Test Case: Track Event with Valid Data
**Objective**: Verify that telemetry events can be tracked successfully

**Steps**:
1. Track an event with feature_type, user_id, agent_id
2. Verify event is stored
3. Verify event has correct structure (event_id, timestamp, etc.)
4. Verify IDs are anonymized

**Expected Result**: Event tracked successfully with anonymized IDs

---

### Test Case: Track Event with Metadata
**Objective**: Verify that events can include metadata

**Steps**:
1. Track an event with metadata dictionary
2. Verify metadata is stored correctly
3. Retrieve event and verify metadata is preserved

**Expected Result**: Metadata stored and retrieved correctly

---

### Test Case: Track Event When Telemetry Disabled
**Objective**: Verify that events are not tracked when telemetry is disabled

**Steps**:
1. Disable telemetry globally
2. Attempt to track an event
3. Verify event is not stored
4. Verify method returns None

**Expected Result**: Event not tracked, returns None

---

### Test Case: Track Event Generates Session ID
**Objective**: Verify that session IDs are auto-generated if not provided

**Steps**:
1. Track an event without session_id
2. Verify event has a session_id
3. Track another event without session_id
4. Verify session_ids are unique

**Expected Result**: Session IDs auto-generated and unique

---

### Test Case: Track Event Limits
**Objective**: Verify that event storage respects max_events limit

**Steps**:
1. Set max_events to 10
2. Track 15 events
3. Verify only 10 events are stored
4. Verify oldest events are removed (FIFO)

**Expected Result**: Only 10 most recent events stored

---

## Opt-In/Opt-Out

### Test Case: Opt-In to Telemetry
**Objective**: Verify that users can opt-in to telemetry

**Steps**:
1. Opt-in a user
2. Verify user is marked as opted-in
3. Track an event for the user
4. Verify event is tracked

**Expected Result**: User opted-in, events tracked

---

### Test Case: Opt-Out of Telemetry
**Objective**: Verify that users can opt-out of telemetry

**Steps**:
1. Opt-in a user
2. Track some events for the user
3. Opt-out the user
4. Verify user is marked as opted-out
5. Verify existing events are removed
6. Track new event for the user
7. Verify new event is not tracked

**Expected Result**: User opted-out, events not tracked after opt-out

---

### Test Case: Default Opt-In Status
**Objective**: Verify that users are opted-in by default

**Steps**:
1. Check opt-in status for a user who hasn't explicitly opted-in/out
2. Verify user is opted-in by default
3. Track an event for the user
4. Verify event is tracked

**Expected Result**: Users opted-in by default

---

### Test Case: Opt-In/Opt-Out Status Check
**Objective**: Verify that opt-in status can be checked

**Steps**:
1. Check status for opted-in user
2. Verify status is True
3. Opt-out the user
4. Check status again
5. Verify status is False

**Expected Result**: Status correctly reflects opt-in/opt-out state

---

## Daily Active Users (DAU)

### Test Case: Track DAU
**Objective**: Verify that daily active users are tracked correctly

**Steps**:
1. Track events for multiple users on the same day
2. Get DAU for that date
3. Verify DAU count matches number of unique users
4. Verify DAU records contain correct information

**Expected Result**: DAU tracked correctly per date

---

### Test Case: DAU Across Multiple Dates
**Objective**: Verify that DAU is tracked separately for each date

**Steps**:
1. Track events for users on date 1
2. Track events for users on date 2 (some same, some different)
3. Get DAU for date 1
4. Get DAU for date 2
5. Verify DAU counts are independent per date

**Expected Result**: DAU tracked independently per date

---

### Test Case: DAU Query Count
**Objective**: Verify that DAU tracks query count separately from feature count

**Steps**:
1. Track query execution events
2. Track non-query events (e.g., visualization)
3. Get DAU record
4. Verify query_count only includes query events
5. Verify feature_count includes all events

**Expected Result**: Query count and feature count tracked separately

---

### Test Case: Get DAU Timeseries
**Objective**: Verify that DAU timeseries data can be retrieved

**Steps**:
1. Track events across multiple dates
2. Get DAU timeseries for date range
3. Verify timeseries includes all dates in range
4. Verify DAU counts are correct for each date
5. Verify dates outside range are not included

**Expected Result**: Timeseries data correct for date range

---

### Test Case: Get DAU for Empty Date
**Objective**: Verify that DAU returns 0 for dates with no activity

**Steps**:
1. Get DAU for a date with no tracked events
2. Verify DAU is 0
3. Verify no error occurs

**Expected Result**: DAU returns 0 for empty dates

---

## Query Patterns

### Test Case: Track Query Pattern
**Objective**: Verify that query patterns can be tracked

**Steps**:
1. Track a query pattern (e.g., SELECT)
2. Verify pattern is stored
3. Verify pattern has correct type, count, execution time, success rate
4. Verify unique users are tracked

**Expected Result**: Query pattern tracked correctly

---

### Test Case: Track Query Pattern Updates Average
**Objective**: Verify that average execution time is calculated correctly

**Steps**:
1. Track query pattern with execution_time_ms=100
2. Track same pattern with execution_time_ms=200
3. Get pattern statistics
4. Verify avg_execution_time_ms is 150

**Expected Result**: Average execution time calculated correctly

---

### Test Case: Track Query Pattern Updates Success Rate
**Objective**: Verify that success rate is calculated correctly

**Steps**:
1. Track 3 successful queries
2. Track 1 failed query
3. Get pattern statistics
4. Verify success_rate is 0.75 (75%)

**Expected Result**: Success rate calculated correctly

---

### Test Case: Track Query Pattern Unique Users
**Objective**: Verify that unique users are tracked per pattern

**Steps**:
1. Track query pattern for user-1
2. Track same pattern for user-2
3. Track same pattern for user-1 again
4. Get pattern statistics
5. Verify unique_users contains 2 users

**Expected Result**: Unique users tracked correctly

---

### Test Case: Track Query Pattern When Telemetry Disabled
**Objective**: Verify that query patterns are not tracked when telemetry is disabled

**Steps**:
1. Disable telemetry
2. Track a query pattern
3. Verify pattern is not stored
4. Get query patterns
5. Verify no patterns returned

**Expected Result**: Patterns not tracked when telemetry disabled

---

### Test Case: Track Query Pattern When User Opted Out
**Objective**: Verify that query patterns are not tracked for opted-out users

**Steps**:
1. Opt-out a user
2. Track a query pattern for that user
3. Verify pattern is not stored
4. Verify no error occurs

**Expected Result**: Patterns not tracked for opted-out users

---

### Test Case: Get Query Patterns
**Objective**: Verify that query patterns can be retrieved

**Steps**:
1. Track multiple query patterns (SELECT, INSERT, UPDATE)
2. Get all query patterns
3. Verify all patterns are returned
4. Verify pattern data is correct

**Expected Result**: All query patterns returned correctly

---

## Feature Usage

### Test Case: Track Feature Usage
**Objective**: Verify that feature usage is tracked automatically when events are tracked

**Steps**:
1. Track an event for a feature
2. Get feature usage statistics
3. Verify feature usage is updated
4. Verify total_uses is correct
5. Verify unique_users includes the user

**Expected Result**: Feature usage tracked correctly

---

### Test Case: Feature Usage Unique Users
**Objective**: Verify that unique users are tracked per feature

**Steps**:
1. Track events for feature from 5 different users
2. Get feature usage statistics
3. Verify unique_users contains 5 users
4. Verify total_uses is 5

**Expected Result**: Unique users tracked correctly

---

### Test Case: Feature Usage Unique Agents
**Objective**: Verify that unique agents are tracked per feature

**Steps**:
1. Track events for feature from 3 different agents
2. Get feature usage statistics
3. Verify unique_agents contains 3 agents
4. Verify total_uses is 3

**Expected Result**: Unique agents tracked correctly

---

### Test Case: Feature Usage Daily Tracking
**Objective**: Verify that feature usage tracks daily usage

**Steps**:
1. Track events for a feature on the same day
2. Get feature usage statistics
3. Verify daily_usage contains today's date
4. Verify count matches number of events

**Expected Result**: Daily usage tracked correctly

---

### Test Case: Feature Usage Last Used
**Objective**: Verify that last_used timestamp is updated

**Steps**:
1. Track an event for a feature
2. Wait a moment
3. Track another event for the same feature
4. Get feature usage statistics
5. Verify last_used is updated to most recent event

**Expected Result**: Last used timestamp updated correctly

---

### Test Case: Get Top Features
**Objective**: Verify that top features can be retrieved

**Steps**:
1. Track events for multiple features with different counts
2. Get top features with limit=3
3. Verify top 3 features are returned
4. Verify features are sorted by total_uses (descending)
5. Verify counts are correct

**Expected Result**: Top features returned correctly sorted

---

### Test Case: Get Feature Usage Filtered
**Objective**: Verify that feature usage can be filtered by type

**Steps**:
1. Track events for multiple features
2. Get feature usage filtered by specific type
3. Verify only that feature type is returned
4. Verify usage statistics are correct

**Expected Result**: Feature usage filtered correctly

---

## Data Export

### Test Case: Export to JSON
**Objective**: Verify that analytics data can be exported to JSON

**Steps**:
1. Track some events and patterns
2. Export to JSON file
3. Verify file is created
4. Load JSON file
5. Verify data structure is correct
6. Verify all expected sections are present (summary, timeseries, patterns, features)

**Expected Result**: JSON export successful with correct data

---

### Test Case: Export to CSV - DAU
**Objective**: Verify that DAU data can be exported to CSV

**Steps**:
1. Track events across multiple dates
2. Export DAU data to CSV
3. Verify file is created
4. Load CSV file
5. Verify columns (date, dau)
6. Verify data is correct

**Expected Result**: CSV export successful with correct DAU data

---

### Test Case: Export to CSV - Features
**Objective**: Verify that feature usage can be exported to CSV

**Steps**:
1. Track events for multiple features
2. Export feature usage to CSV
3. Verify file is created
4. Load CSV file
5. Verify columns (feature_type, total_uses, unique_users, unique_agents, last_used)
6. Verify data is correct

**Expected Result**: CSV export successful with correct feature data

---

### Test Case: Export to CSV - Patterns
**Objective**: Verify that query patterns can be exported to CSV

**Steps**:
1. Track multiple query patterns
2. Export patterns to CSV
3. Verify file is created
4. Load CSV file
5. Verify columns (pattern_type, count, avg_execution_time_ms, success_rate, unique_users)
6. Verify data is correct

**Expected Result**: CSV export successful with correct pattern data

---

### Test Case: Export to CSV - Summary
**Objective**: Verify that summary data can be exported to CSV

**Steps**:
1. Track various events
2. Export summary to CSV
3. Verify file is created
4. Load CSV file
5. Verify data structure
6. Verify key metrics are present

**Expected Result**: CSV export successful with correct summary data

---

### Test Case: Export with Date Range
**Objective**: Verify that exports can be filtered by date range

**Steps**:
1. Track events across multiple dates
2. Export with date range (start_date, end_date)
3. Verify exported data only includes events in date range
4. Verify dates outside range are excluded

**Expected Result**: Export filtered correctly by date range

---

## API Endpoints

### Test Case: POST /api/analytics/telemetry/opt-in
**Objective**: Verify opt-in endpoint

**Steps**:
1. POST opt-in request with user_id
2. Verify 200 status code
3. Verify user is opted-in
4. Test without user_id
5. Verify 400 error

**Expected Result**: Opt-in endpoint works correctly

---

### Test Case: POST /api/analytics/telemetry/opt-out
**Objective**: Verify opt-out endpoint

**Steps**:
1. Opt-in a user first
2. POST opt-out request with user_id
3. Verify 200 status code
4. Verify user is opted-out
5. Test without user_id
6. Verify 400 error

**Expected Result**: Opt-out endpoint works correctly

---

### Test Case: GET /api/analytics/telemetry/status/<user_id>
**Objective**: Verify telemetry status endpoint

**Steps**:
1. Opt-in a user
2. GET status for that user
3. Verify 200 status code
4. Verify opted_in is True
5. Opt-out the user
6. GET status again
7. Verify opted_in is False

**Expected Result**: Status endpoint returns correct information

---

### Test Case: POST /api/analytics/events
**Objective**: Verify track event endpoint

**Steps**:
1. POST event with valid feature_type
2. Verify 201 status code
3. Verify event_id is returned
4. Test with invalid feature_type
5. Verify 400 error
6. Test without feature_type
7. Verify 400 error

**Expected Result**: Event tracking endpoint works correctly

---

### Test Case: GET /api/analytics/dau
**Objective**: Verify DAU endpoint

**Steps**:
1. Track some events
2. GET DAU for today
3. Verify 200 status code
4. Verify DAU count is returned
5. GET DAU for specific date
6. Verify DAU for that date

**Expected Result**: DAU endpoint returns correct data

---

### Test Case: GET /api/analytics/dau/timeseries
**Objective**: Verify DAU timeseries endpoint

**Steps**:
1. Track events across multiple dates
2. GET timeseries with start_date and end_date
3. Verify 200 status code
4. Verify timeseries data is returned
5. Test without dates
6. Verify 400 error

**Expected Result**: Timeseries endpoint returns correct data

---

### Test Case: GET /api/analytics/query-patterns
**Objective**: Verify query patterns endpoint

**Steps**:
1. Track some query patterns
2. GET query patterns
3. Verify 200 status code
4. Verify patterns are returned
5. Verify pattern data is correct

**Expected Result**: Query patterns endpoint returns correct data

---

### Test Case: GET /api/analytics/features
**Objective**: Verify feature usage endpoint

**Steps**:
1. Track events for multiple features
2. GET all feature usage
3. Verify 200 status code
4. Verify all features are returned
5. GET feature usage filtered by type
6. Verify only that feature is returned

**Expected Result**: Feature usage endpoint returns correct data

---

### Test Case: GET /api/analytics/features/top
**Objective**: Verify top features endpoint

**Steps**:
1. Track events for multiple features with different counts
2. GET top features with limit
3. Verify 200 status code
4. Verify top features are returned
5. Verify features are sorted correctly
6. Test with default limit
7. Verify default limit is applied

**Expected Result**: Top features endpoint returns correct data

---

### Test Case: GET /api/analytics/summary
**Objective**: Verify adoption summary endpoint

**Steps**:
1. Track various events and patterns
2. GET adoption summary
3. Verify 200 status code
4. Verify summary includes all sections (period, dau, unique_users, total_events, top_features, feature_adoption, query_patterns)
5. Test with date range
6. Verify data is filtered by date range

**Expected Result**: Summary endpoint returns comprehensive data

---

### Test Case: GET /api/analytics/export
**Objective**: Verify export endpoint

**Steps**:
1. Track some events
2. GET export with format=json
3. Verify 200 status code
4. Verify JSON file is returned
5. GET export with format=csv and data_type=dau
6. Verify CSV file is returned
7. Test with invalid format
8. Verify 400 error

**Expected Result**: Export endpoint works for all formats

---

## Privacy & Anonymization

### Test Case: ID Anonymization
**Objective**: Verify that user and agent IDs are anonymized

**Steps**:
1. Track an event with user_id and agent_id
2. Retrieve the event
3. Verify anonymous_user_id is different from original user_id
4. Verify anonymous_agent_id is different from original agent_id
5. Verify same user_id produces same anonymous_user_id
6. Verify different user_ids produce different anonymous_user_ids

**Expected Result**: IDs are anonymized consistently

---

### Test Case: ID Anonymization Disabled
**Objective**: Verify that anonymization can be disabled

**Steps**:
1. Create analytics instance with anonymize_ids=False
2. Track an event with user_id
3. Verify anonymous_user_id matches original user_id
4. Verify IDs are not hashed

**Expected Result**: IDs not anonymized when disabled

---

### Test Case: Opt-Out Removes Events
**Objective**: Verify that opting out removes existing events

**Steps**:
1. Track events for a user
2. Verify events are stored
3. Opt-out the user (only works if anonymize_ids=False)
4. Verify events for that user are removed
5. Track new event for the user
6. Verify new event is not tracked

**Expected Result**: Opt-out removes existing events (when anonymization disabled)

---

### Test Case: No Original IDs Stored
**Objective**: Verify that original IDs are never stored

**Steps**:
1. Track events with various user_ids and agent_ids
2. Search through stored events
3. Verify no original IDs are present in stored data
4. Verify only anonymized IDs are present

**Expected Result**: Original IDs never stored

---

## Edge Cases and Error Handling

### Test Case: Empty Analytics Data
**Objective**: Verify that analytics handles empty data gracefully

**Steps**:
1. Get DAU for date with no events
2. Verify returns 0 without error
3. Get query patterns with no patterns tracked
4. Verify returns empty dictionary
5. Get feature usage with no usage
6. Verify returns empty dictionary

**Expected Result**: Empty data handled gracefully

---

### Test Case: Invalid Date Formats
**Objective**: Verify that invalid date formats are handled

**Steps**:
1. Get DAU with invalid date format
2. Verify appropriate error handling
3. Get timeseries with invalid date format
4. Verify appropriate error handling

**Expected Result**: Invalid dates handled with errors

---

### Test Case: Large Number of Events
**Objective**: Verify that system handles large volumes of events

**Steps**:
1. Track large number of events (e.g., 1000)
2. Verify events are stored correctly
3. Verify performance is acceptable
4. Verify max_events limit is respected

**Expected Result**: Large volumes handled correctly

---

### Test Case: Concurrent Event Tracking
**Objective**: Verify that concurrent event tracking works correctly

**Steps**:
1. Track events concurrently (simulated)
2. Verify all events are stored
3. Verify no data corruption
4. Verify event counts are correct

**Expected Result**: Concurrent operations handled correctly

---

### Test Case: Feature Type Validation
**Objective**: Verify that invalid feature types are rejected

**Steps**:
1. Attempt to track event with invalid feature_type
2. Verify error is returned
3. Verify event is not stored

**Expected Result**: Invalid feature types rejected

---

### Test Case: Query Pattern Type Validation
**Objective**: Verify that query patterns use valid types

**Steps**:
1. Track query pattern with valid type
2. Verify pattern is stored
3. Verify pattern type matches

**Expected Result**: Valid pattern types accepted

---

### Test Case: Export File Permissions
**Objective**: Verify that export handles file permission errors

**Steps**:
1. Attempt to export to directory without write permissions
2. Verify error is handled gracefully
3. Verify appropriate error message

**Expected Result**: File permission errors handled gracefully

---

### Test Case: Date Range Edge Cases
**Objective**: Verify that date range filtering works correctly at boundaries

**Steps**:
1. Track events at period boundaries
2. Export with exact boundary dates
3. Verify events at boundaries are included correctly
4. Test with start_date > end_date
5. Verify appropriate error handling

**Expected Result**: Date range boundaries handled correctly

---

## Integration Tests

### Test Case: End-to-End Analytics Flow
**Objective**: Verify complete analytics workflow

**Steps**:
1. Opt-in users to telemetry
2. Track various events and query patterns
3. Get DAU statistics
4. Get query patterns
5. Get feature usage
6. Get adoption summary
7. Export data
8. Verify all steps work together correctly

**Expected Result**: Complete workflow executes successfully

---

### Test Case: Dashboard Integration
**Objective**: Verify that dashboard can retrieve and display analytics data

**Steps**:
1. Track various events
2. Access analytics dashboard
3. Verify dashboard loads analytics data via API
4. Verify charts render correctly
5. Verify tables display data
6. Test date range filtering
7. Test export functionality

**Expected Result**: Dashboard integrates correctly with analytics

---

## Performance Tests

### Test Case: Analytics Performance
**Objective**: Verify that analytics operations perform well

**Steps**:
1. Track 1000 events
2. Measure time to get DAU
3. Measure time to get summary
4. Measure time to export
5. Verify all operations complete within acceptable time

**Expected Result**: Analytics operations perform efficiently

---

### Test Case: Export Performance with Large Datasets
**Objective**: Verify that exports perform well with large datasets

**Steps**:
1. Track large number of events (e.g., 10,000)
2. Measure time to export JSON
3. Measure time to export CSV
4. Verify exports complete within acceptable time
5. Verify exported files are correct

**Expected Result**: Exports perform efficiently even with large datasets

