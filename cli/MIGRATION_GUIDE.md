# Migration Guide - Environment Promotion

Guide for using the `aidb migrate` command to promote configurations across environments.

## Overview

The migration feature allows you to:
- **Export** configurations from one environment
- **Import** configurations to another environment
- **Validate** configurations before import
- **Rollback** to previous configurations

## Quick Start

### 1. Export Configuration

Export configuration from your source environment:

```bash
# Development environment
export AIDB_URL="http://dev.example.com"
export AIDB_API_KEY="dev-key"
export AIDB_AGENT_ID="dev-agent"

aidb migrate export --output dev-config.json
```

This creates a JSON file containing:
- Agent configuration
- Resource permissions
- Table information
- Metadata

### 2. Validate Configuration

Before importing, validate the configuration:

```bash
aidb migrate import --input dev-config.json --validate
```

### 3. Import to Target Environment

Import to your target environment:

```bash
# Staging environment
export AIDB_URL="http://staging.example.com"
export AIDB_API_KEY="staging-key"

# Dry run first
aidb migrate import --input dev-config.json --dry-run

# Actual import
aidb migrate import --input dev-config.json
```

### 4. Rollback if Needed

If something goes wrong, rollback:

```bash
# Create backup before import
cp dev-config.json backup.json

# Import
aidb migrate import --input dev-config.json

# If needed, rollback
aidb migrate rollback --backup backup.json
```

## Configuration File Format

The exported configuration file has the following structure:

```json
{
  "version": "1.0.0",
  "exported_at": "2024-01-15T00:00:00.000Z",
  "source_url": "http://dev.example.com",
  "agent": {
    "agent_id": "my-agent",
    "name": "My Agent",
    "type": "analytics",
    "database": {
      "type": "postgresql",
      "connection_name": "main-db"
    },
    "resource_permissions": {
      "products": {
        "type": "table",
        "permissions": ["read"]
      },
      "customers": {
        "type": "table",
        "permissions": ["read", "write"]
      }
    }
  },
  "tables": ["products", "customers", "orders"],
  "metadata": {
    "exported_by": "user",
    "environment": "development"
  }
}
```

## Commands

### Export

Export configuration from current environment:

```bash
aidb migrate export --output config.json
```

**What it exports:**
- Agent ID and name
- Agent type
- Database connection info (type, name - not connection string for security)
- Resource permissions
- Available tables
- Metadata (exported by, environment)

**Note:** Connection strings are NOT exported for security reasons. You'll need to configure database connections separately in each environment.

### Import

Import configuration to target environment:

```bash
aidb migrate import --input config.json
```

**What it imports:**
- Agent configuration (if agent doesn't exist)
- Resource permissions
- Table access

**Options:**
- `--validate` - Only validate, don't import
- `--dry-run` - Show what would be done
- `--json` - Output as JSON

### Rollback

Rollback to a previous configuration:

```bash
aidb migrate rollback --backup backup.json
```

This imports the backup configuration, effectively rolling back changes.

## Validation

The migration system validates configurations before import:

### Required Fields

- `version` - Configuration version
- `agent.agent_id` - Agent identifier
- `agent.name` - Agent name

### Structure Validation

- Resource permissions must have `type` and `permissions` array
- Tables must be an array
- Metadata must be an object

### Example Validation

```bash
# Validate configuration
aidb migrate import --input config.json --validate

# Output:
✓ Configuration validated
✓ Validation only - no changes made
```

## Dry Run

Use dry run to see what would be done without making changes:

```bash
aidb migrate import --input config.json --dry-run
```

**Output:**
```
Dry run mode - no changes will be made

Would perform:
  - Register new agent
  - Set 5 resource permissions
```

## Environment Promotion Workflow

### Development → Staging

```bash
# 1. Export from development
cd dev-environment
aidb migrate export -o dev-config.json

# 2. Validate
aidb migrate import -i dev-config.json --validate

# 3. Import to staging
cd staging-environment
aidb migrate import -i ../dev-config.json --dry-run
aidb migrate import -i ../dev-config.json
```

### Staging → Production

```bash
# 1. Export from staging
cd staging-environment
aidb migrate export -o staging-config.json

# 2. Create backup of production
cd production-environment
aidb migrate export -o production-backup.json

# 3. Dry run
aidb migrate import -i ../staging-config.json --dry-run

# 4. Import
aidb migrate import -i ../staging-config.json

# 5. If issues, rollback
aidb migrate rollback --backup production-backup.json
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Promote Configuration

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options:
          - staging
          - production

jobs:
  promote:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install aidb
        run: npm install -g aidb
      
      - name: Export from source
        env:
          AIDB_URL: ${{ secrets.DEV_URL }}
          AIDB_API_KEY: ${{ secrets.DEV_API_KEY }}
          AIDB_AGENT_ID: ${{ secrets.DEV_AGENT_ID }}
        run: aidb migrate export -o config.json
      
      - name: Validate configuration
        run: aidb migrate import -i config.json --validate
      
      - name: Import to target
        env:
          AIDB_URL: ${{ secrets[format('{0}_URL', inputs.environment)] }}
          AIDB_API_KEY: ${{ secrets[format('{0}_API_KEY', inputs.environment)] }}
        run: aidb migrate import -i config.json
```

### GitLab CI Example

```yaml
promote_config:
  stage: deploy
  script:
    - npm install -g aidb
    - |
      export AIDB_URL="$SOURCE_URL"
      export AIDB_API_KEY="$SOURCE_API_KEY"
      export AIDB_AGENT_ID="$SOURCE_AGENT_ID"
      aidb migrate export -o config.json
    - aidb migrate import -i config.json --validate
    - |
      export AIDB_URL="$TARGET_URL"
      export AIDB_API_KEY="$TARGET_API_KEY"
      aidb migrate import -i config.json
  only:
    - main
```

## Best Practices

### 1. Always Validate First

```bash
aidb migrate import --input config.json --validate
```

### 2. Use Dry Run

```bash
aidb migrate import --input config.json --dry-run
```

### 3. Create Backups

```bash
# Before import
aidb migrate export -o backup-$(date +%Y%m%d).json

# Import
aidb migrate import -i config.json

# If needed
aidb migrate rollback --backup backup-20240115.json
```

### 4. Version Control

Commit configuration files to version control:

```bash
git add config.json
git commit -m "Export configuration for v1.2.0"
```

### 5. Environment-Specific Configs

Keep separate configs for each environment:

```
configs/
  ├── dev-config.json
  ├── staging-config.json
  └── prod-config.json
```

## Troubleshooting

### Validation Errors

```bash
# Check configuration structure
cat config.json | jq .

# Validate
aidb migrate import -i config.json --validate
```

### Import Errors

```bash
# Check agent exists
aidb test

# Check permissions
aidb migrate import -i config.json --dry-run
```

### Rollback Issues

```bash
# Verify backup file
cat backup.json | jq .

# Rollback
aidb migrate rollback --backup backup.json
```

## Security Notes

- **Connection strings are NOT exported** - Configure separately in each environment
- **API keys are NOT exported** - Use environment-specific keys
- **Sensitive data** - Review configurations before committing to version control

## Related Documentation

- [CLI README](README.md) - CLI tool documentation
- [CLI Implementation Summary](CLI_IMPLEMENTATION_SUMMARY.md) - Implementation details

---

**Questions?** Check the [troubleshooting](#troubleshooting) section or review the [CLI README](README.md).

