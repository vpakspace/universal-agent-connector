# aidb - AI Agent Connector CLI

Command-line tool for querying databases via AI Agent Connector using natural language.

## Installation

```bash
npm install -g aidb
```

Or install from source:

```bash
cd cli
npm install
npm link
```

## Quick Start

### 1. Configure

```bash
aidb config
```

This will prompt you for:
- AI Agent Connector URL (default: http://localhost:5000)
- API Key
- Default Agent ID

Or set environment variables:

```bash
export AIDB_URL="http://localhost:5000"
export AIDB_API_KEY="your-api-key"
export AIDB_AGENT_ID="your-agent-id"
```

### 2. Test Connection

```bash
aidb test
```

### 3. Query

```bash
aidb query "What are the top 5 best-selling products?"
```

## Commands

### Query

Execute a natural language query:

```bash
aidb query "What are the top 10 customers by revenue?"
aidb q "Show me sales for last month"  # Short alias
```

**Options:**
- `--preview` - Preview SQL without executing
- `--no-cache` - Disable result caching
- `--json` - Output results as JSON

**Examples:**
```bash
# Preview SQL
aidb query "What are the top products?" --preview

# JSON output
aidb query "Show me all customers" --json

# Disable cache
aidb query "Get latest orders" --no-cache
```

### Explain

Explain what a query would do without executing it:

```bash
aidb explain "What are the top products?"
aidb e "Show me sales data"  # Short alias
```

**Options:**
- `--json` - Output as JSON

### Test

Test connection to AI Agent Connector:

```bash
aidb test
```

**Options:**
- `--json` - Output as JSON

### Migrate

Import/export configurations for environment promotion:

```bash
# Export configuration
aidb migrate export --output config.json

# Import configuration
aidb migrate import --input config.json

# Validate configuration
aidb migrate import --input config.json --validate

# Dry run (show what would be done)
aidb migrate import --input config.json --dry-run

# Rollback to backup
aidb migrate rollback --backup backup.json
```

**Options:**
- `--output <file>` - Output file for export
- `--input <file>` - Input file for import
- `--backup <file>` - Backup file for rollback
- `--validate` - Validate only, do not import
- `--dry-run` - Show what would be done without making changes
- `--json` - Output as JSON

**Examples:**
```bash
# Export from development
aidb migrate export -o dev-config.json

# Import to staging
aidb migrate import -i dev-config.json --dry-run

# Rollback if needed
aidb migrate rollback --backup dev-config.json
```

### Config

Manage CLI configuration:

```bash
# Interactive configuration
aidb config

# Set a value
aidb config --set url=http://localhost:5000
aidb config --set apiKey=your-key

# Get a value
aidb config --get url

# List all configuration
aidb config --list
```

## Global Options

All commands support these global options:

- `-u, --url <url>` - AI Agent Connector API URL
- `-k, --api-key <key>` - API key for authentication
- `-a, --agent-id <id>` - Agent ID
- `-j, --json` - Output results as JSON
- `--verbose` - Verbose output

## Examples

### Basic Query

```bash
aidb query "What are the top 5 products by sales?"
```

### JSON Output for Scripts

```bash
aidb query "Get total revenue" --json | jq '.rows[0].total_revenue'
```

### Preview SQL

```bash
aidb query "Show me customers from New York" --preview
```

### Using in CI/CD

```bash
#!/bin/bash
# CI/CD script example

# Set configuration
export AIDB_URL="https://api.example.com"
export AIDB_API_KEY="$CI_API_KEY"
export AIDB_AGENT_ID="$CI_AGENT_ID"

# Test connection
aidb test || exit 1

# Run query and capture result
RESULT=$(aidb query "Get total users" --json)
TOTAL_USERS=$(echo $RESULT | jq -r '.rows[0].total_users')

if [ "$TOTAL_USERS" -gt 1000 ]; then
  echo "Threshold exceeded: $TOTAL_USERS users"
  exit 1
fi
```

### Using in Node.js Scripts

```javascript
const { execSync } = require('child_process');

// Execute query and parse JSON
const result = JSON.parse(
  execSync('aidb query "Get total revenue" --json', { encoding: 'utf8' })
);

console.log('Total Revenue:', result.rows[0].total_revenue);
```

## Configuration

Configuration is stored in `~/.aidb/config.json`.

You can also use environment variables:
- `AIDB_URL` - API URL
- `AIDB_API_KEY` - API key
- `AIDB_AGENT_ID` - Default agent ID

## Output Formats

### Table Format (Default)

Results are displayed as formatted tables:

```
Results:

┌─────────┬──────────────┬───────┐
│ id      │ name         │ price │
├─────────┼──────────────┼───────┤
│ 1       │ Product 1    │ 100   │
│ 2       │ Product 2    │ 200   │
└─────────┴──────────────┴───────┘

2 row(s)
Execution time: 45ms
```

### JSON Format

With `--json` flag:

```json
{
  "success": true,
  "sql": "SELECT * FROM products LIMIT 10",
  "rows": [
    {"id": 1, "name": "Product 1", "price": 100}
  ],
  "columns": ["id", "name", "price"],
  "execution_time": 45
}
```

## Error Handling

Errors are displayed in red and exit with code 1:

```bash
$ aidb query "test"
Error: API key required. Use --api-key or set AIDB_API_KEY environment variable.
```

For JSON output, errors are returned as JSON:

```json
{
  "success": false,
  "error": "API Error (401): Invalid API key"
}
```

## Troubleshooting

### Connection Issues

```bash
# Test connection
aidb test

# Check URL
aidb config --get url

# Verbose output
aidb test --verbose
```

### Authentication Issues

```bash
# Check API key
aidb config --get apiKey

# Set API key
aidb config --set apiKey=your-key
```

### Agent Not Found

```bash
# Check agent ID
aidb config --get agentId

# Set agent ID
aidb config --set agentId=your-agent-id
```

## Development

```bash
# Install dependencies
npm install

# Run tests
npm test

# Lint
npm run lint

# Link for local development
npm link
```

## License

MIT

