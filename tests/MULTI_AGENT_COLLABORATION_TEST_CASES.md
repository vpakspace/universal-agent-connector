# Multi-Agent Collaboration Test Cases

Comprehensive test cases for multi-agent collaboration feature.

## Test Coverage

### Unit Tests (`test_agent_orchestrator.py`)

#### AgentOrchestrator Tests

1. **Session Management**
   - ✅ Create collaboration session
   - ✅ Create session with initial state
   - ✅ Retrieve session
   - ✅ Retrieve non-existent session

2. **Workflow Execution**
   - ✅ Determine workflow based on roles
   - ✅ Execute collaboration workflow
   - ✅ Execute with custom workflow
   - ✅ Handle workflow errors
   - ✅ Session not found error

3. **Agent Handlers**
   - ✅ Schema research handler
   - ✅ Schema research without connector
   - ✅ SQL generation handler
   - ✅ Query validation handler
   - ✅ Query validation for dangerous queries
   - ✅ Result analysis handler

4. **Query Analysis**
   - ✅ Detect query type (SELECT, INSERT, UPDATE, DELETE)
   - ✅ Estimate query complexity (simple, moderate, complex)

5. **Communication**
   - ✅ Send message between agents
   - ✅ Send message to invalid session

6. **Trace Visualization**
   - ✅ Get trace visualization
   - ✅ Get visualization for non-existent session

#### AgentMessage Tests

1. ✅ Create agent message
2. ✅ Convert message to dict
3. ✅ Create message from dict

#### AgentTrace Tests

1. ✅ Create agent trace
2. ✅ Convert trace to dict

#### CollaborationSession Tests

1. ✅ Create collaboration session
2. ✅ Convert session to dict

### Integration Tests (`test_multi_agent_api.py`)

#### API Endpoint Tests

1. **Create Collaboration Session**
   - ✅ Create session successfully
   - ✅ Missing query field
   - ✅ Missing agents field
   - ✅ Invalid agent ID
   - ✅ Invalid role

2. **Execute Collaboration**
   - ✅ Execute collaboration successfully
   - ✅ Execute with custom workflow
   - ✅ Session not found error

3. **Get Session**
   - ✅ Get session successfully
   - ✅ Session not found

4. **Get Trace Visualization**
   - ✅ Get visualization successfully
   - ✅ Visualization error handling

5. **Send Message**
   - ✅ Send message successfully
   - ✅ Missing required fields
   - ✅ Session not found

6. **Authentication**
   - ✅ Unauthenticated request

## Test Scenarios

### Scenario 1: Basic Collaboration Flow

**Setup:**
- Schema researcher agent
- SQL generator agent

**Steps:**
1. Create collaboration session
2. Execute collaboration
3. Verify schema research completed
4. Verify SQL generation completed
5. Check final state contains generated SQL

**Expected:**
- Session status: completed
- Traces: 2 (one per agent)
- State contains schema_info and generated_sql

### Scenario 2: Full Pipeline

**Setup:**
- Schema researcher
- SQL generator
- Query validator
- Result analyzer

**Steps:**
1. Create session with all 4 agents
2. Execute collaboration
3. Verify all agents executed in order
4. Check validation results
5. Check analysis results

**Expected:**
- All 4 agents executed
- Execution order: researcher → generator → validator → analyzer
- Validation results present
- Analysis results present

### Scenario 3: Custom Workflow

**Setup:**
- Multiple agents

**Steps:**
1. Create session
2. Execute with custom workflow order
3. Verify agents executed in custom order

**Expected:**
- Agents execute in specified order
- Not default role-based order

### Scenario 4: Error Handling

**Setup:**
- Agent without database connection

**Steps:**
1. Create session with agent missing DB connection
2. Execute collaboration
3. Verify error handling

**Expected:**
- Session status: failed
- Error trace recorded
- Error message in result

### Scenario 5: Message Passing

**Setup:**
- Two agents in session

**Steps:**
1. Create session
2. Send message from agent-1 to agent-2
3. Verify message stored
4. Retrieve session and check messages

**Expected:**
- Message stored in session
- Message appears in messages list
- Correct from/to agents

### Scenario 6: Query Validation

**Setup:**
- SQL generator
- Query validator

**Steps:**
1. Generate SQL with DELETE without WHERE
2. Validate query
3. Check validation results

**Expected:**
- Validation fails
- Error message about missing WHERE clause
- Validated_sql is None

### Scenario 7: Trace Visualization

**Setup:**
- Multiple agents with traces

**Steps:**
1. Create and execute session
2. Get trace visualization
3. Verify visualization structure

**Expected:**
- Timeline with all traces
- Agent statistics
- Duration metrics
- Messages included

## Test Data

### Sample Agents

```json
{
  "schema-agent": {
    "agent_id": "schema-agent",
    "role": "schema_researcher",
    "database_config": {...}
  },
  "sql-agent": {
    "agent_id": "sql-agent",
    "role": "sql_generator"
  },
  "validator-agent": {
    "agent_id": "validator-agent",
    "role": "query_validator"
  },
  "analyzer-agent": {
    "agent_id": "analyzer-agent",
    "role": "result_analyzer"
  }
}
```

### Sample Queries

1. **Simple Query:**
   ```
   "Find all active users"
   ```

2. **Complex Query:**
   ```
   "Find all customers who purchased products in category 'Electronics' in the last quarter"
   ```

3. **Dangerous Query:**
   ```
   "Delete inactive users"
   ```

## Edge Cases

1. **Empty Agent List**
   - Should return 400 error

2. **Invalid Role**
   - Should return 400 error

3. **Non-existent Agent**
   - Should return 404 error

4. **Missing Required Fields**
   - Should return 400 error

5. **Invalid Session ID**
   - Should return 404 error

6. **Agent Without Database**
   - Should handle gracefully with error trace

7. **SQL Generation Failure**
   - Should record error in trace

8. **Concurrent Sessions**
   - Should handle multiple sessions independently

## Performance Tests

1. **Large Schema Research**
   - Test with 100+ tables
   - Verify performance

2. **Complex Workflow**
   - Test with 10+ agents
   - Verify execution time

3. **Many Traces**
   - Test with 100+ traces
   - Verify visualization performance

## Security Tests

1. **Authentication**
   - Verify API key required
   - Verify invalid API key rejected

2. **Agent Isolation**
   - Verify agents can only access their own sessions
   - Verify no cross-agent data leakage

3. **Input Validation**
   - Verify SQL injection prevention
   - Verify XSS prevention in messages

## Integration Points

### With Existing Systems

1. **Agent Registry**
   - Verify agent lookup
   - Verify database connector retrieval

2. **NL to SQL Converter**
   - Verify integration with SQL generation
   - Verify schema formatting

3. **Database Connector**
   - Verify connection handling
   - Verify query execution

## Running Tests

### Unit Tests

```bash
python -m pytest tests/test_agent_orchestrator.py -v
```

### Integration Tests

```bash
python -m pytest tests/test_multi_agent_api.py -v
```

### All Tests

```bash
python -m pytest tests/test_agent_orchestrator.py tests/test_multi_agent_api.py -v
```

### With Coverage

```bash
python -m pytest tests/test_agent_orchestrator.py tests/test_multi_agent_api.py --cov=ai_agent_connector.app.utils.agent_orchestrator --cov=ai_agent_connector.app.api.routes --cov-report=html
```

## Test Metrics

### Coverage Goals

- **Unit Tests**: >90% coverage
- **Integration Tests**: >80% coverage
- **Critical Paths**: 100% coverage

### Test Categories

- **Unit Tests**: 30+ test cases
- **Integration Tests**: 15+ test cases
- **Edge Cases**: 10+ test cases
- **Error Handling**: 8+ test cases

## Continuous Integration

Tests should run:
- On every commit
- Before merging PRs
- On scheduled basis (nightly)

## Test Maintenance

### When to Update Tests

1. New agent roles added
2. New message types added
3. Workflow changes
4. API changes
5. Bug fixes

### Test Documentation

- Keep test cases documented
- Update when features change
- Document test data requirements
- Document test environment setup

