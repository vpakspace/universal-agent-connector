# Cold Start Optimization Guide

Strategies to achieve <2 second cold start times for serverless deployments.

## Target Metrics

- **Cold Start**: <2 seconds
- **Warm Invocation**: <100ms
- **Database Connection**: <50ms (pooled)

## Optimization Strategies

### 1. Lazy Imports

**Problem**: Importing all modules at startup increases cold start time.

**Solution**: Import only what's needed, when it's needed.

```python
# ❌ Bad: Import everything at module level
from main import create_app
app = create_app()

# ✅ Good: Lazy import in handler
_app = None
def _lazy_import_app():
    global _app
    if _app is None:
        from main import create_app
        _app = create_app()
    return _app
```

### 2. Connection Pooling

**Problem**: Creating new database connections on each invocation is slow.

**Solution**: Reuse connections across invocations.

```python
# Configure connection pool
app.config['DATABASE_POOL_SIZE'] = 5
app.config['DATABASE_MAX_OVERFLOW'] = 10

# Use connection pool in handlers
from ai_agent_connector.app.db.connector import DatabaseConnector
connector = DatabaseConnector()  # Uses pool
```

### 3. Minimize Package Size

**Problem**: Large packages take longer to load.

**Solution**: 
- Remove unused dependencies
- Use Lambda layers (AWS) to share common dependencies
- Compress packages

```bash
# Check package size
du -sh deployment-package.zip

# Remove unnecessary files
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -r {} +
```

### 4. Provisioned Concurrency / Minimum Instances

**AWS Lambda**: Use provisioned concurrency
```yaml
ProvisionedConcurrencyConfig:
  ProvisionedConcurrentExecutions: 2
```

**GCP Cloud Functions**: Set minimum instances
```bash
--min-instances=1
```

**Azure Functions**: Enable Always-On
```bash
az functionapp config set --always-on true
```

### 5. Optimize Memory Allocation

**Higher memory = faster CPU** (up to a point)

- AWS Lambda: 512MB-1GB optimal
- GCP Cloud Functions: 512MB-1GB optimal
- Azure Functions: 1.5GB default

### 6. Use Managed Database Proxies

**AWS**: RDS Proxy
- Connection pooling
- Reduced connection overhead
- Better performance

**GCP**: Cloud SQL Proxy
- Secure connections
- Connection pooling
- Lower latency

**Azure**: Connection pooling in application
- Reuse connections
- Configure pool size

### 7. Optimize Initialization Code

**Problem**: Heavy initialization in `create_app()`.

**Solution**: Defer heavy operations.

```python
def create_app():
    app = Flask(__name__)
    
    # ✅ Lightweight initialization
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    
    # ❌ Avoid heavy imports here
    # from heavy_module import HeavyClass
    
    # ✅ Lazy load heavy modules
    @app.before_first_request
    def load_heavy_modules():
        from heavy_module import HeavyClass
        app.heavy = HeavyClass()
    
    return app
```

### 8. Use Health Check Endpoint

**Lightweight health check** without app initialization:

```python
def health_handler(event, context):
    """No app initialization - returns immediately"""
    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'healthy'})
    }
```

### 9. Monitor and Measure

**Track cold start times**:

```python
import time

_init_start_time = time.time()
# ... initialization ...
init_time = time.time() - _init_start_time

if init_time > 2.0:
    print(f"WARNING: Cold start took {init_time:.2f}s")
```

### 10. Platform-Specific Optimizations

#### AWS Lambda
- Use Lambda layers for dependencies
- Enable X-Ray tracing (minimal overhead)
- Use ARM architecture (Graviton2) for better price/performance

#### GCP Cloud Functions
- Use Cloud SQL Proxy connector
- Set minimum instances > 0
- Use Gen2 functions (better performance)

#### Azure Functions
- Enable Always-On for production
- Use Premium plan for better performance
- Configure connection pooling

## Measurement

### Test Cold Start

```bash
# AWS
aws lambda invoke \
  --function-name ai-agent-connector-api \
  --payload '{}' \
  response.json

# GCP
curl -w "@curl-format.txt" -o /dev/null -s \
  https://REGION-PROJECT_ID.cloudfunctions.net/ai-agent-connector/health

# Azure
curl -w "@curl-format.txt" -o /dev/null -s \
  https://ai-agent-connector.azurewebsites.net/api/health
```

### Monitor Cold Starts

- **AWS**: CloudWatch Logs (look for "Init Duration")
- **GCP**: Cloud Monitoring (function initialization time)
- **Azure**: Application Insights (cold start metrics)

## Best Practices

1. **Always use lazy imports** for heavy modules
2. **Enable connection pooling** for databases
3. **Set minimum instances** > 0 for production
4. **Monitor cold start times** regularly
5. **Optimize package size** continuously
6. **Use health check endpoints** for monitoring
7. **Test cold starts** after each deployment

## Troubleshooting

### Cold Start > 2s

1. Check package size
2. Review imports (use lazy loading)
3. Enable provisioned concurrency/min instances
4. Optimize database connection setup
5. Check initialization code

### Warm Invocation Slow

1. Check database query performance
2. Review connection pool configuration
3. Monitor memory usage
4. Check for memory leaks

## References

- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [GCP Cloud Functions Performance](https://cloud.google.com/functions/docs/bestpractices/tips)
- [Azure Functions Performance](https://docs.microsoft.com/azure/azure-functions/functions-best-practices)

