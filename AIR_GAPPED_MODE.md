# Air-Gapped Mode Documentation

## Overview

Air-gapped mode ensures that **no sensitive data leaves your network** by blocking all external API calls and requiring the use of local AI models. This is essential for organizations with strict data privacy requirements, compliance needs, or security policies that prohibit external data transmission.

## Features

- ✅ **Complete Network Isolation**: Blocks all external API calls to OpenAI, Anthropic, and other cloud-based AI services
- ✅ **Local AI Model Support**: Supports local AI models via Ollama, LocalAI, or any OpenAI-compatible API
- ✅ **Automatic Validation**: Automatically validates and blocks external providers when air-gapped mode is enabled
- ✅ **Natural Language to SQL**: Supports local models for natural language query conversion
- ✅ **Configuration Flag**: Simple environment variable to enable/disable air-gapped mode

## Use Cases

- **Sensitive Data**: Healthcare, financial, or government data that cannot leave the network
- **Compliance Requirements**: GDPR, HIPAA, or other regulations requiring data residency
- **Security Policies**: Organizations with strict no-external-API policies
- **Offline Environments**: Systems that operate without internet connectivity
- **Cost Control**: Avoid external API costs by using local models

## Configuration

### Enable Air-Gapped Mode

Set the `AIR_GAPPED_MODE` environment variable:

```bash
export AIR_GAPPED_MODE=true
```

Or in your `.env` file:

```env
AIR_GAPPED_MODE=true
```

### Local AI Configuration

Configure your local AI model endpoint:

```bash
# Ollama (default)
export LOCAL_AI_BASE_URL=http://localhost:11434
export LOCAL_AI_MODEL=llama2

# LocalAI
export LOCAL_AI_BASE_URL=http://localhost:8080/v1
export LOCAL_AI_MODEL=local-model

# Custom local endpoint
export LOCAL_AI_BASE_URL=http://192.168.1.100:5000/v1
export LOCAL_AI_MODEL=custom-model
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AIR_GAPPED_MODE` | `false` | Enable/disable air-gapped mode |
| `LOCAL_AI_BASE_URL` | `http://localhost:11434` | Base URL for local AI API |
| `LOCAL_AI_MODEL` | `llama2` | Default model to use |
| `LOCAL_AI_API_KEY` | (optional) | API key if required by local model |

## Setting Up Local AI Models

### Option 1: Ollama (Recommended)

Ollama is the easiest way to run local LLMs:

1. **Install Ollama**:
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows
   # Download from https://ollama.ai/download
   ```

2. **Pull a Model**:
   ```bash
   ollama pull llama2
   # or
   ollama pull mistral
   # or
   ollama pull codellama
   ```

3. **Verify Installation**:
   ```bash
   curl http://localhost:11434/api/generate -d '{
     "model": "llama2",
     "prompt": "Hello"
   }'
   ```

4. **Configure AI Agent Connector**:
   ```bash
   export AIR_GAPPED_MODE=true
   export LOCAL_AI_BASE_URL=http://localhost:11434
   export LOCAL_AI_MODEL=llama2
   ```

### Option 2: LocalAI

LocalAI provides OpenAI-compatible API for local models:

1. **Install LocalAI**:
   ```bash
   docker run -p 8080:8080 -ti localai/localai:latest
   ```

2. **Configure**:
   ```bash
   export AIR_GAPPED_MODE=true
   export LOCAL_AI_BASE_URL=http://localhost:8080/v1
   export LOCAL_AI_MODEL=your-model
   ```

### Option 3: Custom Local Endpoint

If you have your own OpenAI-compatible API endpoint:

```bash
export AIR_GAPPED_MODE=true
export LOCAL_AI_BASE_URL=http://your-server:port/v1
export LOCAL_AI_MODEL=your-model
```

## Registering Local AI Agents

### Using the API

```bash
POST /api/admin/ai-agents/register
Content-Type: application/json
X-API-Key: <admin-api-key>

{
  "agent_id": "local-llama-agent",
  "provider": "local",
  "model": "llama2",
  "api_base": "http://localhost:11434",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### Using Python

```python
from ai_agent_connector.app.agents.providers import (
    AgentProvider,
    AgentConfiguration
)
from ai_agent_connector.app.agents.ai_agent_manager import AIAgentManager

manager = AIAgentManager()

config = AgentConfiguration(
    provider=AgentProvider.LOCAL,
    model="llama2",
    api_base="http://localhost:11434",
    temperature=0.7,
    max_tokens=2000
)

manager.register_ai_agent(
    agent_id="local-llama-agent",
    config=config
)
```

## Natural Language to SQL

The natural language to SQL converter automatically uses local models when air-gapped mode is enabled:

```python
from ai_agent_connector.app.utils.nl_to_sql import NLToSQLConverter

# Automatically uses local model if AIR_GAPPED_MODE=true
converter = NLToSQLConverter()

result = converter.convert_to_sql(
    natural_language_query="Show me all users older than 25",
    schema_info=schema_info
)
```

## Security Validation

The system automatically validates and blocks external providers when air-gapped mode is enabled:

### Blocked Providers

- ❌ **OpenAI**: `openai` provider is blocked
- ❌ **Anthropic**: `anthropic` provider is blocked
- ❌ **External Custom**: Custom providers with external URLs are blocked

### Allowed Providers

- ✅ **Local**: `local` provider is always allowed
- ✅ **Local Custom**: Custom providers with localhost/private network URLs

### Example Error

If you try to register an OpenAI agent in air-gapped mode:

```python
# This will raise AirGappedModeError
config = AgentConfiguration(
    provider=AgentProvider.OPENAI,
    model="gpt-4",
    api_key="sk-..."
)
```

Error message:
```
AirGappedModeError: External provider 'openai' is not allowed in air-gapped mode. 
Use 'local' provider with a local AI model (Ollama, LocalAI, etc.)
```

## Network Isolation

### What's Blocked

- All HTTP/HTTPS requests to external domains (api.openai.com, api.anthropic.com, etc.)
- External API calls for AI agent queries
- External API calls for natural language to SQL conversion
- External webhook notifications (if configured to external URLs)

### What's Allowed

- Local network requests (localhost, 127.0.0.1, private IP ranges)
- Database connections (internal databases)
- Internal API calls
- Local AI model endpoints

### Private Network Ranges

The following are considered "local" and allowed:
- `localhost` / `127.0.0.1`
- `10.x.x.x` (RFC 1918)
- `172.16.x.x` - `172.31.x.x` (RFC 1918)
- `192.168.x.x` (RFC 1918)

## Testing Air-Gapped Mode

### 1. Enable Air-Gapped Mode

```bash
export AIR_GAPPED_MODE=true
```

### 2. Start Local AI Model

```bash
# Using Ollama
ollama serve
ollama pull llama2
```

### 3. Test Local Agent Registration

```python
from ai_agent_connector.app.agents.providers import (
    AgentProvider,
    AgentConfiguration
)
from ai_agent_connector.app.agents.ai_agent_manager import AIAgentManager

manager = AIAgentManager()

# This should work
config = AgentConfiguration(
    provider=AgentProvider.LOCAL,
    model="llama2",
    api_base="http://localhost:11434"
)
manager.register_ai_agent("test-agent", config)

# This should fail
try:
    config = AgentConfiguration(
        provider=AgentProvider.OPENAI,
        model="gpt-4",
        api_key="sk-..."
    )
    manager.register_ai_agent("test-agent-2", config)
except AirGappedModeError as e:
    print(f"Blocked: {e}")
```

### 4. Test Natural Language Query

```python
from ai_agent_connector.app.utils.nl_to_sql import NLToSQLConverter

converter = NLToSQLConverter()
result = converter.convert_to_sql("Show all users")
print(result)
```

## Troubleshooting

### Local Model Not Responding

1. **Check if model is running**:
   ```bash
   curl http://localhost:11434/api/tags  # Ollama
   ```

2. **Check model name**:
   ```bash
   ollama list  # List available models
   ```

3. **Test model directly**:
   ```bash
   ollama run llama2 "Hello"
   ```

### Connection Errors

- Ensure local AI service is running
- Check firewall settings
- Verify `LOCAL_AI_BASE_URL` is correct
- Check if port is accessible

### Model Not Found

- Verify model name matches installed model
- For Ollama: Use `ollama list` to see available models
- Ensure model is pulled/downloaded

### Performance Issues

Local models may be slower than cloud APIs:
- Use smaller models for faster responses
- Consider GPU acceleration
- Adjust `max_tokens` to limit response length
- Use appropriate hardware (GPU recommended)

## Best Practices

1. **Model Selection**: Choose models appropriate for your hardware
   - **CPU**: Smaller models (llama2:7b, mistral:7b)
   - **GPU**: Larger models (llama2:13b, codellama:34b)

2. **Hardware Requirements**:
   - **Minimum**: 8GB RAM, 4 CPU cores
   - **Recommended**: 16GB+ RAM, GPU with 8GB+ VRAM

3. **Model Optimization**:
   - Use quantized models when available
   - Consider model fine-tuning for SQL tasks
   - Cache frequently used queries

4. **Security**:
   - Keep local AI services on internal networks
   - Use firewall rules to restrict access
   - Monitor for any external connection attempts
   - Regular security audits

## Compliance and Security

### Data Residency

Air-gapped mode ensures:
- ✅ No data transmitted to external services
- ✅ All processing happens on-premises
- ✅ Complete control over data flow
- ✅ Compliance with data residency requirements

### Audit and Monitoring

Monitor for:
- External connection attempts (should be blocked)
- Local model performance
- Query success/failure rates
- Resource usage

### Security Checklist

- [ ] Air-gapped mode enabled via environment variable
- [ ] Local AI model running and accessible
- [ ] Firewall rules preventing external connections
- [ ] Network monitoring enabled
- [ ] Regular security audits
- [ ] Access controls on local AI services

## Migration from External to Local

### Step 1: Set Up Local AI

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama2
```

### Step 2: Enable Air-Gapped Mode

```bash
export AIR_GAPPED_MODE=true
export LOCAL_AI_BASE_URL=http://localhost:11434
export LOCAL_AI_MODEL=llama2
```

### Step 3: Update Agent Configurations

Replace external agents with local ones:

```python
# Old (external)
config = AgentConfiguration(
    provider=AgentProvider.OPENAI,
    model="gpt-4",
    api_key="sk-..."
)

# New (local)
config = AgentConfiguration(
    provider=AgentProvider.LOCAL,
    model="llama2",
    api_base="http://localhost:11434"
)
```

### Step 4: Test and Validate

- Test all AI agent queries
- Test natural language to SQL conversion
- Verify no external connections
- Monitor performance

## API Reference

### Environment Variables

```python
# Enable air-gapped mode
os.environ['AIR_GAPPED_MODE'] = 'true'

# Configure local AI
os.environ['LOCAL_AI_BASE_URL'] = 'http://localhost:11434'
os.environ['LOCAL_AI_MODEL'] = 'llama2'
```

### Python API

```python
from ai_agent_connector.app.utils.air_gapped import (
    is_air_gapped_mode,
    validate_provider_allowed,
    get_local_ai_config
)

# Check mode
if is_air_gapped_mode():
    print("Air-gapped mode enabled")

# Validate provider
try:
    validate_provider_allowed('openai')
except AirGappedModeError:
    print("External provider blocked")

# Get local config
config = get_local_ai_config()
print(config['base_url'])
```

## Support

For issues or questions:
- Check logs for error messages
- Verify local AI model is running
- Test model connectivity
- Review network configuration

## Related Documentation

- [Security Guide](SECURITY.md) - Security best practices
- [Threat Model](THREAT_MODEL.md) - Security threat analysis
- [API Documentation](README.md) - Complete API reference

