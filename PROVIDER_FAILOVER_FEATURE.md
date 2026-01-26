# AI Provider Failover Feature - Implementation Summary

## Overview

This document describes the automatic AI provider failover feature implementation that allows admins to configure automatic failover between AI providers (e.g., OpenAI → Claude) to ensure system availability during outages.

## Acceptance Criteria

✅ **Health checks** - Automatic health monitoring of AI providers  
✅ **Automatic switching** - Automatic failover to backup providers when primary fails  
✅ **Retry logic** - Integrated retry logic with failover support

## Implementation Details

### 1. Provider Failover Manager (`ai_agent_connector/app/utils/provider_failover.py`)

The core failover system that:
- Manages provider health status
- Performs automatic health checks
- Handles automatic failover between providers
- Tracks consecutive failures
- Supports manual provider switching

**Key Features:**
- **Health Status Tracking**: Tracks health status (healthy, unhealthy, unknown, checking)
- **Automatic Health Checks**: Background health checks with configurable intervals
- **Consecutive Failure Tracking**: Tracks consecutive failures to trigger failover
- **Provider Chain**: Maintains ordered list of providers (primary + backups)
- **Thread-Safe**: Uses locks for thread-safe operations
- **Response Time Tracking**: Tracks provider response times

### 2. Integration with AIAgentManager

Failover is integrated into `AIAgentManager`:
- Providers are automatically registered with failover manager
- `execute_query` method uses failover if configured
- Failover configuration methods added to manager
- Health status accessible through manager

### 3. Health Check System

Health checks work by:
1. Sending a simple test query to the provider
2. Measuring response time
3. Tracking success/failure status
4. Updating consecutive failure count
5. Automatically switching if threshold exceeded

**Health Check Configuration:**
- `health_check_enabled`: Enable/disable health checks
- `health_check_interval`: Interval between checks (default: 60 seconds)
- `health_check_timeout`: Timeout for health check (default: 5 seconds)
- `max_consecutive_failures`: Failover threshold (default: 3 failures)
- `health_check_query`: Query used for health checks (default: "Hello")

### 4. API Endpoints

#### Configure Failover
- **POST** `/api/agents/<agent_id>/failover`
  - Configure failover for an agent
  - Request body: `primary_provider_id`, `backup_provider_ids`, configuration options
  - Returns: Failover configuration

#### Get Failover Config
- **GET** `/api/agents/<agent_id>/failover`
  - Get failover configuration for an agent
  - Returns: Failover configuration or 404 if not configured

#### Get Failover Stats
- **GET** `/api/agents/<agent_id>/failover/stats`
  - Get failover statistics including health status
  - Returns: Statistics with provider health information

#### Check Provider Health
- **GET** `/api/agents/<agent_id>/failover/health`
  - Manually check health of providers for an agent
  - Returns: Health status

#### Get All Provider Health
- **GET** `/api/providers/health`
  - Get health status of all registered providers
  - Returns: Health status for all providers

#### Switch Provider
- **POST** `/api/agents/<agent_id>/failover/switch`
  - Manually switch to a different provider
  - Request body: `provider_id`
  - Returns: Success message

### 5. Failover Flow

1. **Query Execution**:
   - If failover is configured, try primary provider first
   - If primary fails, automatically try backup providers in order
   - Return result from first successful provider
   - Raise error if all providers fail

2. **Health Monitoring**:
   - Background thread checks provider health periodically
   - Updates health status based on check results
   - Tracks consecutive failures

3. **Automatic Switching**:
   - If primary provider has too many consecutive failures
   - Automatically switch to next healthy provider in chain
   - Update active provider for agent

### 6. Provider Health Status

**Status Values:**
- `HEALTHY`: Provider is responding correctly
- `UNHEALTHY`: Provider is failing
- `UNKNOWN`: Health status not yet determined
- `CHECKING`: Health check in progress

**Health Information:**
- `last_check`: Timestamp of last health check
- `last_success`: Timestamp of last successful check
- `last_failure`: Timestamp of last failure
- `consecutive_failures`: Number of consecutive failures
- `response_time_ms`: Response time in milliseconds
- `error_message`: Last error message (if any)

## Usage Examples

### Configure Failover

```bash
# Configure failover for an agent
curl -X POST http://localhost:5000/api/agents/my-agent/failover \
  -H "Content-Type: application/json" \
  -d '{
    "primary_provider_id": "openai-agent",
    "backup_provider_ids": ["claude-agent", "backup-openai-agent"],
    "health_check_enabled": true,
    "health_check_interval": 60,
    "health_check_timeout": 5,
    "max_consecutive_failures": 3,
    "auto_failover_enabled": true
  }'
```

### Get Failover Configuration

```bash
# Get failover config
curl http://localhost:5000/api/agents/my-agent/failover
```

### Get Failover Statistics

```bash
# Get failover stats with health status
curl http://localhost:5000/api/agents/my-agent/failover/stats
```

### Check Provider Health

```bash
# Check health of providers
curl http://localhost:5000/api/agents/my-agent/failover/health

# Get health of all providers
curl http://localhost:5000/api/providers/health
```

### Manually Switch Provider

```bash
# Switch to backup provider
curl -X POST http://localhost:5000/api/agents/my-agent/failover/switch \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "claude-agent"
  }'
```

## Architecture Notes

### Thread Safety
- Uses threading locks for concurrent access
- Background health check threads are daemon threads
- Provider registration and switching are thread-safe

### Performance
- Health checks run in background threads
- Health check queries are lightweight ("Hello")
- Failover adds minimal overhead to query execution
- Response times are tracked for monitoring

### Error Handling
- Failover failures don't break query execution
- Falls back to standard retry logic if failover fails
- Health check errors are logged but don't stop monitoring
- All provider failures are tracked and reported

## Integration with Existing Features

The failover system integrates with:
- **Retry Policy**: Failover works alongside retry logic
- **Rate Limiting**: Rate limits apply per provider
- **Cost Tracking**: Costs are tracked per provider used
- **Webhooks**: Failover events can trigger webhooks (extensible)

## Configuration Options

### FailoverConfig

```python
{
    "agent_id": "my-agent",
    "primary_provider_id": "openai-agent",
    "backup_provider_ids": ["claude-agent"],
    "health_check_enabled": true,
    "health_check_interval": 60,  # seconds
    "health_check_timeout": 5,  # seconds
    "max_consecutive_failures": 3,
    "auto_failover_enabled": true,
    "health_check_query": "Hello"
}
```

## Testing

Comprehensive test suite in `tests/test_provider_failover.py`:
- Provider registration and configuration
- Health check functionality
- Automatic failover logic
- Manual provider switching
- API endpoint testing
- Edge cases and error handling

Run tests:
```bash
pytest tests/test_provider_failover.py -v
```

## Files Modified/Created

### New Files
- `ai_agent_connector/app/utils/provider_failover.py` - Core failover manager
- `tests/test_provider_failover.py` - Comprehensive test suite
- `PROVIDER_FAILOVER_FEATURE.md` - This documentation

### Modified Files
- `ai_agent_connector/app/agents/ai_agent_manager.py` - Integrated failover
- `ai_agent_connector/app/api/routes.py` - Added API endpoints

## Future Enhancements

Potential improvements:
1. **Webhook Notifications**: Notify on failover events
2. **Metrics/Logging**: Enhanced logging and metrics for failover events
3. **Circuit Breaker Pattern**: Add circuit breaker for faster failover
4. **Load Balancing**: Distribute load across healthy providers
5. **Health Check Customization**: Allow custom health check queries
6. **Provider Priority**: Weight providers by cost/performance
7. **Automatic Recovery**: Automatically switch back to primary when healthy
8. **Dashboard UI**: Visual dashboard for failover status

## Conclusion

The provider failover feature is fully implemented and ready for use. It provides automatic failover between AI providers with health monitoring, ensuring system availability during provider outages.
