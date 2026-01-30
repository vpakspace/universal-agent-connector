# Universal Agent Connector

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/vpakspace/universal-agent-connector/actions/workflows/ci.yml/badge.svg)](https://github.com/vpakspace/universal-agent-connector/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-94%20passed-success)](https://github.com/vpakspace/universal-agent-connector/actions)
[![Python 3.10|3.11|3.12](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io)
[![OntoGuard](https://img.shields.io/badge/OntoGuard-integrated-orange.svg)](https://github.com/vpakspace/ontoguard-ai)

**Enterprise-grade MCP infrastructure with ontology-driven semantic routing for AI agents**

Enterprise-grade connectivity layer for AI agents: secure database access, fine-grained permissions, natural language queries, and MCP governance.

## ⭐ Star History

If you find Universal Agent Connector useful, please star the repo! It helps us understand adoption and motivates continued development.

[![Star History Chart](https://api.star-history.com/svg?repos=cloudbadal007/universal-agent-connector&type=Date)](https://star-history.com/#cloudbadal007/universal-agent-connector&Date)

## 💬 Community

**Get help, share ideas, and connect with the community:**

- **[GitHub Discussions](https://github.com/cloudbadal007/universal-agent-connector/discussions)** - Ask questions, share ideas, show your projects
- **[Community Forums Guide](docs/COMMUNITY_FORUMS.md)** - How to use discussions effectively
- **[FAQ](https://github.com/cloudbadal007/universal-agent-connector/discussions/categories/q-a)** - Frequently asked questions

**Discussion Categories:**
- 💬 **Q&A** - Ask questions and get help
- 💡 **Ideas** - Share feature ideas and suggestions
- 💭 **General** - Community discussion
- 🎉 **Show and Tell** - Share your projects

## 📰 Articles & Resources

- **[Medium Article: Universal Agent Connector — MCP, Ontology, Production-Ready AI Infrastructure](https://medium.com/@cloudpankaj/universal-agent-connector-mcp-ontology-production-ready-ai-infrastructure-0b4e35f22942)** - Deep dive into the architecture, features, and use cases
- **[Substack: Badal AI World](https://badalaiworld.substack.com)** - AI insights and updates
- **[Video Tutorial](https://youtu.be/QwTDeMBUwEY)** - Setup and usage walkthrough

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines, code style, and how to submit pull requests.

**Quick Links:**
- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Developer Setup](docs/DEVELOPER_SETUP.md) - Development environment
- [Code Style Guide](docs/CODE_STYLE_GUIDE.md) - Coding standards
- [PR Template](.github/pull_request_template.md) - Pull request template

## 🚀 Try It Now - No Installation Required!

**[👉 Try in Browser (Gitpod)](https://gitpod.io/#https://github.com/your-repo/ai-agent-connector)** | **[👉 Try in Browser (GitHub Codespaces)](https://github.com/codespaces)**

One-click setup with pre-loaded demo data and guided tutorial. Get started in 2 minutes!

## 🎥 Video Tutorials

**Learn faster with video tutorials!** Watch step-by-step guides for common workflows:

1. **[Getting Started - Setup & Installation](docs/video-tutorials/01-setup.md)** (5 min) - Install, register agent, connect database
2. **[Your First Query](docs/video-tutorials/02-first-query.md)** (4 min) - Natural language queries and results
3. **[Managing Permissions](docs/video-tutorials/03-permissions.md)** (6 min) - Security and access control
4. **[Monitoring & Analytics](docs/video-tutorials/04-monitoring.md)** (5 min) - Track usage, costs, performance
5. **[Troubleshooting Common Issues](docs/video-tutorials/05-troubleshooting.md)** (6 min) - Fix common problems

**See [Video Tutorials Guide](docs/video-tutorials/README.md) for all tutorials and production information.**

## Features

- **Interactive Demo Projects**: Get started in 2 minutes with e-commerce, SaaS metrics, and financial reporting demos - see [demos/README.md](demos/README.md)
- **Agent Registration**: Register and manage AI agents with unique identifiers
- **Authentication**: Secure API key-based authentication for agents
- **Access Control**: Fine-grained permission management system
- **RESTful API**: Clean REST API for agent management
- **Database Ready**: Extensible database connector architecture
- **Secure Credentials**: Database credentials encrypted at rest using Fernet symmetric encryption
- **Multi-Database Support**: PostgreSQL, MySQL, MongoDB, BigQuery, Snowflake
- **Connection Pooling**: Configurable connection pooling for performance optimization
- **Timeout Management**: Configurable timeouts for connections and queries
- **AI Agent Management**: Register and manage multiple AI agent providers (OpenAI, Anthropic, local models, custom models)
- **Air-Gapped Mode**: Complete network isolation with local AI model support - no external API calls, data never leaves your network
- **Rate Limiting**: Per-agent rate limits (queries per minute/hour/day) to control costs and resource usage
- **Retry Policies**: Configurable retry strategies for failed agent requests (exponential backoff, fixed delay, linear)
- **Version Control**: Track and rollback agent configuration changes
- **Webhook Notifications**: Real-time notifications for agent query success/failure events
- **Clear Error Messages**: User-friendly, actionable error messages for query failures
- **Database Failover**: Automatic failover to backup databases when primary is unavailable
- **Dead-Letter Queue**: Capture and replay failed queries after fixing issues
- **Visualizations**: Generate charts and tables from query results (bar, line, pie, scatter, area, table, heatmap)
- **Scheduled Queries**: Schedule recurring queries (hourly, daily, weekly, monthly, custom cron)
- **Export to External Systems**: Export results to S3, Google Sheets, Slack, Email, CSV, JSON, Excel
- **Natural Language Explanations**: Plain language explanations of query results with statistics and trends
- **A/B Testing**: Test different AI models on the same query to compare performance
- **Data Residency Rules**: Enforce data residency rules (e.g., EU data stays in EU databases) for GDPR compliance
- **Data Retention Policies**: Set retention policies for query logs with automatic purging
- **Audit Log Anonymization**: Anonymize user identities in audit logs while maintaining accountability
- **Contextual Help Tooltips**: Schema-aware help tooltips explaining databases, tables, and columns
- **Autocomplete Suggestions**: Autocomplete for table/column names in natural language queries
- **Setup Wizard**: Guided setup wizard for connecting first database and agent in under 5 minutes
- **Plugin SDK**: Extensible plugin system for adding custom database drivers with TypeScript types and validation
- **Embeddable Query Widgets**: Add live, interactive query widgets to your blog or website with iframe embed code, customizable themes, and secure API key management - see [WIDGET_EMBED_GUIDE.md](WIDGET_EMBED_GUIDE.md)
- **CLI Tool**: Command-line interface for querying databases in scripts and CI/CD - `npm install -g aidb` - see [cli/README.md](cli/README.md)
- **Prompt Engineering Studio**: Visual editor for customizing SQL generation prompts with variables, A/B testing, and template library - see [docs/PROMPT_STUDIO_GUIDE.md](docs/PROMPT_STUDIO_GUIDE.md)
- **Query Optimization**: Automatic query optimization with EXPLAIN analysis, index recommendations, query rewrites, and before/after metrics - see [docs/QUERY_OPTIMIZATION_GUIDE.md](docs/QUERY_OPTIMIZATION_GUIDE.md)
- **Multi-Agent Collaboration**: Orchestrate multiple agents to collaborate on complex queries (schema research, SQL generation, validation) with trace visualization - see [docs/MULTI_AGENT_COLLABORATION_GUIDE.md](docs/MULTI_AGENT_COLLABORATION_GUIDE.md)
- **SSO Integration**: Enterprise SSO support with SAML 2.0, OAuth 2.0, and LDAP authentication, including attribute mapping - see [docs/SSO_INTEGRATION_GUIDE.md](docs/SSO_INTEGRATION_GUIDE.md)
- **Legal Documents Generator**: Generate Terms of Service and Privacy Policy documents with customizable templates and multi-jurisdiction compliance (GDPR, CCPA, PIPEDA, etc.) - see [docs/LEGAL_DOCUMENTS_GUIDE.md](docs/LEGAL_DOCUMENTS_GUIDE.md)
- **Chargeback Reports**: Track usage and allocate costs by team/user with flexible allocation rules and invoice generation - see [docs/CHARGEBACK_GUIDE.md](docs/CHARGEBACK_GUIDE.md)
- **Adoption Analytics**: Track DAU, query patterns, and feature usage with opt-in anonymous telemetry, interactive dashboard, and BI tool exports - see [docs/ADOPTION_ANALYTICS_GUIDE.md](docs/ADOPTION_ANALYTICS_GUIDE.md)
- **Training Data Export**: Export query-SQL pairs for fine-tuning custom models with privacy-safe anonymization, format conversion (JSONL/JSON/CSV), and dataset statistics - see [docs/TRAINING_DATA_EXPORT_GUIDE.md](docs/TRAINING_DATA_EXPORT_GUIDE.md)

## Project Structure

```
ai_agent_connector/
│
├── app/                 # Core application logic
│   ├── __init__.py
│   ├── db/              # Database connection, models
│   │   ├── __init__.py
│   │   ├── connector.py # Database connector classes/functions
│   ├── agents/          # AI agent registration/auth
│   │   ├── __init__.py
│   │   ├── registry.py
│   ├── permissions/     # Access control logic
│   │   ├── __init__.py
│   │   ├── access_control.py
│   ├── api/             # API endpoints/routes
│   │   ├── __init__.py
│   │   ├── routes.py
│   └── utils/           # Utility functions/helpers
│       ├── __init__.py
│       └── helpers.py
│
├── tests/               # Unit tests
│
├── config/              # Configuration files (env, secrets)
│
├── requirements.txt     # Python dependencies
├── README.md
└── main.py              # Entry point
```

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set encryption key (for production):
```bash
# Generate a secure encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set as environment variable
export ENCRYPTION_KEY="your-generated-key-here"
```

**Note**: The encryption key is required for securing database credentials. If not set, a temporary key will be generated (not suitable for production).

## Usage

### Running the Application

```bash
python main.py
```

The application will start on `http://127.0.0.1:5000` by default.

### Interactive Demo Projects 🚀

**Get started in 2 minutes!** Try our interactive demos with sample data:

- **[E-Commerce Analytics Demo](demos/ecommerce/README.md)** - Analyze sales, customers, and products
- **[SaaS Metrics Dashboard Demo](demos/saas/README.md)** - Track MRR, churn, and user growth
- **[Financial Reporting Demo](demos/financial/README.md)** - Generate financial reports and analyze transactions

Each demo includes:
- ✅ Sample database with realistic data
- ✅ Step-by-step walkthrough (2 minutes)
- ✅ Natural language query examples
- ✅ Ready-to-use agent configurations

**Quick Start:**
```bash
# Setup all demos at once
./demos/setup_all_demos.sh  # Linux/Mac
demos\setup_all_demos.ps1   # Windows

# Or setup individual demos
createdb ecommerce_demo
psql -U postgres -d ecommerce_demo -f demos/ecommerce/setup.sql
```

See [demos/README.md](demos/README.md) for complete demo documentation.

### Web Dashboard

For non-technical users, a simple web-based dashboard is available at:

- **Dashboard**: `http://127.0.0.1:5000/dashboard` - Overview of agents and system status
- **Integration Wizard**: `http://127.0.0.1:5000/wizard` - Step-by-step guide to connect agents and databases
- **Agents Management**: `http://127.0.0.1:5000/agents` - View and manage all registered agents
- **Access Preview**: `http://127.0.0.1:5000/agents/<agent_id>/access-preview` - Preview which tables/fields an agent can access

The dashboard provides a user-friendly interface for:
- Connecting new agents to databases without writing code
- Testing database connections before registration
- Viewing and managing existing agents
- Setting up permissions through a guided wizard
- Previewing agent access to tables and fields (self-service permission transparency)

**No coding required!** Simply follow the wizard steps to:
1. Enter agent information
2. Configure database connection (with connection testing)
3. Provide agent credentials
4. Review and connect

The dashboard automatically handles all API calls in the background.

### Environment Variables

You can configure the application using environment variables:

- `FLASK_ENV`: Environment mode (development, production, testing)
- `PORT`: Server port (default: 5000)
- `HOST`: Server host (default: 127.0.0.1)
- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: Database connection string
- `OPENAI_API_KEY`: OpenAI API key for natural language query conversion (required for NL queries, not needed in air-gapped mode)
- `AIR_GAPPED_MODE`: Enable air-gapped mode to block external API calls (default: false)
- `LOCAL_AI_BASE_URL`: Base URL for local AI model API (default: http://localhost:11434 for Ollama)
- `LOCAL_AI_MODEL`: Default local AI model to use (default: llama2)

### API Endpoints

#### Health Check
```bash
GET /api/health
```

#### Test Database Connection
```bash
POST /api/databases/test
Content-Type: application/json

{
  "connection_string": "postgresql://db_user:db_pass@db.example.com/analytics"
}
```

Test a database connection before registering an agent. Useful for validating credentials programmatically.

**Alternative format (individual parameters):**
```json
{
  "host": "db.example.com",
  "port": 5432,
  "user": "db_user",
  "password": "db_pass",
  "database": "analytics"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Database connection test successful",
  "database_info": {
    "connection_string": "***",
    "connection_name": "default",
    "type": "postgresql"
  }
}
```

**Response (Failure):**
```json
{
  "status": "error",
  "message": "Database connection failed: connection refused",
  "error": "connection refused"
}
```

#### Register Agent
```bash
POST /api/agents/register
Content-Type: application/json

{
  "agent_id": "agent-001",
  "agent_info": {
    "name": "Reporting Agent",
    "type": "assistant"
  },
  "agent_credentials": {
    "api_key": "agent-issued-key",
    "api_secret": "agent-issued-secret"
  },
  "database": {
    "connection_string": "postgresql://db_user:db_pass@db.example.com/analytics",
    "connection_name": "analytics",
    "type": "postgresql"
  }
}
```

The registration flow:
- securely hashes the provided agent credentials
- validates the supplied database details by performing a connection test
- links the agent to the verified database so future queries can route through the connector
- returns an API key for the agent to use for authentication

**Response:**
```json
{
  "agent_id": "agent-001",
  "api_key": "generated-api-key-here",
  "database": {
    "status": "connected",
    "connection_name": "analytics",
    "type": "postgresql"
  },
  "message": "Agent registered with database connectivity"
}
```

#### Update Agent Database Connection
```bash
PUT /api/agents/<agent_id>/database
Content-Type: application/json

{
  "connection_string": "postgresql://new_user:new_pass@new_host:5432/new_db"
}
```

Update or add a database connection for an existing agent. Useful for:
- Changing database credentials
- Switching to a different database
- Adding a database connection to an agent that didn't have one

**Response:**
```json
{
  "message": "Database connection updated for agent agent-001",
  "agent_id": "agent-001",
  "database": {
    "status": "connected",
    "connection_name": "default",
    "type": "postgresql"
  },
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### List Available Tables/Datasets
```bash
GET /api/agents/<agent_id>/tables
```

Lists all available tables and datasets from the agent's connected database. This helps admins see what resources they can set permissions on. The response includes permission information for each table.

**Response:**
```json
{
  "agent_id": "agent-001",
  "database": "analytics",
  "tables": [
    {
      "schema": "public",
      "table_name": "users",
      "resource_id": "users",
      "type": "table",
      "permissions": ["read", "write"],
      "has_read": true,
      "has_write": true
    },
    {
      "schema": "analytics",
      "table_name": "sales",
      "resource_id": "analytics.sales",
      "type": "table",
      "permissions": ["read"],
      "has_read": true,
      "has_write": false
    }
  ],
  "count": 2
}
```

#### Preview Agent Access (Self-Service)
```bash
GET /api/agents/<agent_id>/access-preview
```

Provides a comprehensive preview of what tables and fields an agent can access, making permissions transparent for self-service users. This endpoint shows:
- Summary statistics (total tables, accessible/inaccessible counts, permission breakdown)
- Detailed information for accessible tables including column-level details
- List of inaccessible tables

**Response:**
```json
{
  "agent_id": "agent-001",
  "database": "analytics",
  "summary": {
    "total_tables": 5,
    "accessible_tables": 3,
    "inaccessible_tables": 2,
    "read_only_tables": 1,
    "read_write_tables": 2,
    "write_only_tables": 0
  },
  "accessible_tables": [
    {
      "schema": "public",
      "table_name": "users",
      "resource_id": "users",
      "access_status": "accessible",
      "permissions": ["read", "write"],
      "has_read": true,
      "has_write": true,
      "column_count": 3,
      "columns": [
        {
          "name": "id",
          "type": "integer",
          "nullable": false,
          "default": null,
          "position": 1
        },
        {
          "name": "name",
          "type": "varchar",
          "nullable": true,
          "default": null,
          "position": 2
        },
        {
          "name": "email",
          "type": "varchar",
          "nullable": true,
          "default": null,
          "position": 3
        }
      ]
    },
    {
      "schema": "public",
      "table_name": "orders",
      "resource_id": "orders",
      "access_status": "accessible",
      "permissions": ["read"],
      "has_read": true,
      "has_write": false,
      "column_count": 2,
      "columns": [
        {
          "name": "id",
          "type": "integer",
          "nullable": false,
          "default": null,
          "position": 1
        },
        {
          "name": "user_id",
          "type": "integer",
          "nullable": true,
          "default": null,
          "position": 2
        }
      ]
    }
  ],
  "inaccessible_tables": [
    {
      "schema": "analytics",
      "table_name": "sales",
      "resource_id": "analytics.sales",
      "access_status": "no_permission",
      "permissions": [],
      "has_read": false,
      "has_write": false,
      "column_count": 0,
      "columns": []
    }
  ]
}
}
```

**Web Interface:**
Access the visual preview at: `http://127.0.0.1:5000/agents/<agent_id>/access-preview`

The web interface provides:
- Visual summary cards showing permission statistics
- Expandable column details for accessible tables
- Clear distinction between accessible and inaccessible tables
- Permission badges (READ/WRITE) for easy identification

#### Set Table/Dataset Permissions
```bash
PUT /api/agents/<agent_id>/permissions/resources
Content-Type: application/json

{
  "resource_id": "public.sales_orders",
  "resource_type": "table",   # or "dataset"
  "permissions": ["read", "write"]
}
```

Use this endpoint to manage fine-grained read/write access for a registered agent. A companion `GET /api/agents/<agent_id>/permissions/resources` call lists the current resource-level permissions.

**Permission Types:**
- `read`: Required for SELECT queries
- `write`: Required for INSERT, UPDATE, DELETE queries
- `delete`: For future use (currently not enforced)
- `admin`: For administrative operations (currently not enforced)

#### List Resource Permissions
```bash
GET /api/agents/<agent_id>/permissions/resources
```

Lists all resource-level permissions currently granted to an agent.

**Response:**
```json
{
  "agent_id": "agent-001",
  "resources": {
    "public.orders": {
      "type": "table",
      "permissions": ["read", "write"]
    },
    "analytics.sales": {
      "type": "table",
      "permissions": ["read"]
    }
  }
}
```

#### Revoke Resource Permissions
```bash
DELETE /api/agents/<agent_id>/permissions/resources/<resource_id>
```

Revokes all permissions for an agent on a specific resource (table or dataset).

**Response:**
```json
{
  "message": "Permissions revoked for resource public.orders",
  "agent_id": "agent-001",
  "resource_id": "public.orders"
}
```

#### Execute Query with Permission Enforcement
```bash
POST /api/agents/<agent_id>/query
Content-Type: application/json
X-API-Key: <agent_api_key>

{
  "query": "SELECT * FROM public.users WHERE id = %s",
  "params": [1],              # Optional: query parameters
  "as_dict": false             # Optional: return results as dictionaries
}
```

This endpoint executes database queries with automatic permission enforcement:

**Features:**
- **Automatic Permission Validation**: Checks if the agent has required permissions on all tables/datasets accessed by the query
- **Query Type Detection**: Automatically determines if query requires READ or WRITE permission
- **Table Extraction**: Parses SQL to identify all tables/datasets being accessed
- **Secure Execution**: Only executes queries if agent has appropriate permissions

**Response (Success):**
```json
{
  "agent_id": "agent-001",
  "query_type": "SELECT",
  "tables_accessed": ["public.users"],
  "success": true,
  "result": [["user1"], ["user2"]],
  "row_count": 2
}
```

**Response (Permission Denied):**
```json
{
  "error": "Permission denied",
  "denied_resources": [
    {
      "resource": "public.orders",
      "required_permission": "read",
      "message": "Agent does not have read permission on public.orders"
    }
  ],
  "message": "Agent lacks required permissions on one or more resources"
}
```

**Supported Query Types:**
- `SELECT`: Requires `read` permission
- `INSERT`: Requires `write` permission
- `UPDATE`: Requires `write` permission
- `DELETE`: Requires `write` permission

**Example Workflow:**
1. Register an agent with database connection
2. Set permissions on specific tables/datasets
3. Agent executes queries using their API key
4. System automatically validates permissions before execution

#### Natural Language Query
```bash
POST /api/agents/<agent_id>/query/natural
Content-Type: application/json
X-API-Key: <agent_api_key>

{
  "query": "Show me all users who are older than 25",
  "as_dict": false  # Optional: return results as dictionaries
}
```

This endpoint allows admins to submit questions in plain English. The system automatically:
- Converts the natural language question to SQL
- Validates permissions on required tables
- Executes the query
- Returns results

**Features:**
- **Automatic SQL Generation**: Uses AI to convert natural language to SQL
- **Schema-Aware**: Automatically includes database schema information for accurate SQL generation
- **Permission Enforcement**: Same permission checks as direct SQL queries
- **Error Handling**: Provides detailed error messages if conversion or execution fails

**Response (Success):**
```json
{
  "agent_id": "agent-001",
  "natural_language_query": "Show me all users who are older than 25",
  "generated_sql": "SELECT * FROM users WHERE age > 25",
  "query_type": "SELECT",
  "tables_accessed": ["users"],
  "success": true,
  "result": [["user1", 30], ["user2", 28]],
  "row_count": 2
}
```

**Response (Permission Denied):**
```json
{
  "error": "Permission denied",
  "denied_resources": [
    {
      "resource": "users",
      "required_permission": "read",
      "message": "Agent does not have read permission on users"
    }
  ],
  "generated_sql": "SELECT * FROM users WHERE age > 25",
  "natural_language_query": "Show me all users who are older than 25"
}
```

**Configuration:**
- Set `OPENAI_API_KEY` environment variable to enable natural language queries
- Uses `gpt-4o-mini` model by default (configurable)

#### List Agents
```bash
GET /api/agents
```

#### Get Agent
```bash
GET /api/agents/<agent_id>
```

#### Revoke Agent
```bash
DELETE /api/agents/<agent_id>
```

Completely revokes an agent's access to the system. This operation:

**What gets removed:**
- Agent registration and metadata
- All API keys (agent can no longer authenticate)
- All permissions (general and resource-level)
- Database connection configurations
- Stored credentials

**Security:**
- After revocation, the agent cannot authenticate or access any resources
- All access is immediately invalidated
- The revocation is logged for audit purposes

**Response:**
```json
{
  "message": "Agent agent-001 revoked successfully",
  "details": {
    "agent_id": "agent-001",
    "permissions_revoked": true,
    "api_keys_invalidated": true,
    "database_access_removed": true,
    "credentials_removed": true
  }
}
```

**Use Cases:**
- Agent is no longer needed
- Security concerns or compromised credentials
- Agent change or replacement
- Compliance requirements for access removal

### AI Agent Management Endpoints

All AI agent management endpoints require admin permissions. Use the `X-API-Key` header with an admin agent's API key.

#### Register AI Agent
```bash
POST /api/admin/ai-agents/register
Content-Type: application/json
X-API-Key: <admin-api-key>

{
  "agent_id": "openai-agent-1",
  "provider": "openai",
  "model": "gpt-4",
  "api_key": "sk-...",
  "temperature": 0.7,
  "max_tokens": 2000,
  "rate_limit": {
    "queries_per_minute": 60,
    "queries_per_hour": 1000
  },
  "retry_policy": {
    "enabled": true,
    "max_retries": 3,
    "strategy": "exponential",
    "initial_delay": 1.0
  }
}
```

Register an AI agent with support for:
- **Providers**: `openai`, `anthropic`, `local` (for local AI models), or `custom`
- **Air-Gapped Mode**: When enabled, only `local` provider is allowed. See [AIR_GAPPED_MODE.md](AIR_GAPPED_MODE.md) for details.
- **Rate Limits**: Control queries per minute/hour/day
- **Retry Policies**: Configure retry strategies for failed requests
- **Version Control**: Automatic version tracking for configuration changes

**Response:**
```json
{
  "agent_id": "openai-agent-1",
  "provider": "openai",
  "model": "gpt-4",
  "version": 1,
  "registered_at": "2024-01-15T10:30:00Z"
}
```

#### List AI Agents
```bash
GET /api/admin/ai-agents
X-API-Key: <admin-api-key>
```

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "openai-agent-1",
      "configuration": {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.7
      },
      "rate_limit": {
        "queries_per_minute": 60,
        "queries_per_hour": 1000
      },
      "retry_policy": {
        "enabled": true,
        "max_retries": 3,
        "strategy": "exponential"
      },
      "current_version": 1
    }
  ],
  "count": 1
}
```

#### Execute Query
```bash
POST /api/admin/ai-agents/<agent_id>/query
Content-Type: application/json
X-API-Key: <admin-api-key>

{
  "query": "What is machine learning?",
  "context": {
    "system_prompt": "You are a helpful assistant."
  }
}
```

Executes a query using the specified AI agent. Automatically applies rate limiting, retry policies, and sends webhook notifications.

**Response:**
```json
{
  "response": "Machine learning is...",
  "model": "gpt-4",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  },
  "provider": "openai"
}
```

#### Set Rate Limit
```bash
POST /api/admin/ai-agents/<agent_id>/rate-limit
Content-Type: application/json
X-API-Key: <admin-api-key>

{
  "queries_per_minute": 100,
  "queries_per_hour": 2000,
  "queries_per_day": 10000
}
```

Configure rate limits to control costs and resource usage.

#### Get Rate Limit Usage
```bash
GET /api/admin/ai-agents/<agent_id>/rate-limit
X-API-Key: <admin-api-key>
```

**Response:**
```json
{
  "agent_id": "openai-agent-1",
  "rate_limit": {
    "queries_per_minute": 100,
    "queries_per_hour": 2000
  },
  "usage": {
    "rate_limits_configured": true,
    "limits": {
      "queries_per_minute": 100,
      "queries_per_hour": 2000
    },
    "current_usage": {
      "queries_last_minute": 5,
      "queries_last_hour": 50,
      "queries_last_day": 500
    },
    "remaining": {
      "queries_this_minute": 95,
      "queries_this_hour": 1950,
      "queries_this_day": 9500
    }
  }
}
```

#### Set Retry Policy
```bash
POST /api/admin/ai-agents/<agent_id>/retry-policy
Content-Type: application/json
X-API-Key: <admin-api-key>

{
  "enabled": true,
  "max_retries": 5,
  "strategy": "exponential",
  "initial_delay": 1.0,
  "max_delay": 60.0,
  "backoff_multiplier": 2.0,
  "retryable_errors": ["timeout", "connection_error", "rate_limit"],
  "jitter": true
}
```

Configure retry policies for handling transient errors. Strategies:
- `fixed`: Fixed delay between retries
- `exponential`: Exponential backoff (default)
- `linear`: Linear backoff

#### List Configuration Versions
```bash
GET /api/admin/ai-agents/<agent_id>/versions?limit=10
X-API-Key: <admin-api-key>
```

**Response:**
```json
{
  "agent_id": "openai-agent-1",
  "versions": [
    {
      "version": 2,
      "timestamp": "2024-01-15T11:00:00Z",
      "config": {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.8
      },
      "description": "Updated temperature",
      "created_by": "admin"
    },
    {
      "version": 1,
      "timestamp": "2024-01-15T10:30:00Z",
      "config": {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.7
      },
      "description": "Initial configuration",
      "created_by": "admin"
    }
  ],
  "count": 2
}
```

#### Rollback Configuration
```bash
POST /api/admin/ai-agents/<agent_id>/rollback
Content-Type: application/json
X-API-Key: <admin-api-key>

{
  "version": 1,
  "description": "Rolling back due to issues"
}
```

Rollback to a previous configuration version. Creates a new version with the rolled-back configuration.

**Response:**
```json
{
  "agent_id": "openai-agent-1",
  "rollback_to_version": 1,
  "new_version": {
    "version": 3,
    "timestamp": "2024-01-15T12:00:00Z",
    "config": {...},
    "tags": ["rollback", "from_version_1"]
  },
  "message": "Configuration rolled back successfully"
}
```

#### Register Webhook
```bash
POST /api/admin/ai-agents/<agent_id>/webhooks
Content-Type: application/json
X-API-Key: <admin-api-key>

{
  "url": "https://example.com/webhook",
  "events": ["query_success", "query_failure", "rate_limit_exceeded"],
  "secret": "webhook-secret",
  "timeout": 10,
  "retry_on_failure": true,
  "max_retries": 3
}
```

Register a webhook to receive notifications for agent events:
- `query_success`: Query executed successfully
- `query_failure`: Query failed after retries
- `rate_limit_exceeded`: Rate limit was exceeded
- `configuration_changed`: Configuration was updated
- `agent_registered`: New agent registered
- `agent_revoked`: Agent was removed

**Response:**
```json
{
  "agent_id": "openai-agent-1",
  "webhook_id": "webhook_1234567890",
  "webhook": {
    "url": "https://example.com/webhook",
    "events": ["query_success", "query_failure"],
    "secret": "***",
    "timeout": 10,
    "enabled": true
  },
  "message": "Webhook registered successfully"
}
```

#### Get Webhook History
```bash
GET /api/admin/ai-agents/<agent_id>/webhooks/history?limit=100
X-API-Key: <admin-api-key>
```

**Response:**
```json
{
  "agent_id": "openai-agent-1",
  "history": [
    {
      "webhook_url": "https://example.com/webhook",
      "event": "query_success",
      "timestamp": "2024-01-15T10:30:00Z",
      "status": "success",
      "response_code": 200,
      "attempts": 1
    }
  ],
  "statistics": {
    "total_deliveries": 100,
    "successful": 95,
    "failed": 5,
    "success_rate": 95.0
  }
}
```

#### API Documentation
```bash
GET /api/api-docs
```

Returns OpenAPI 3.0 compatible API documentation. Useful for:
- API client generation
- Understanding request/response schemas
- Integration with API documentation tools

**Response:** OpenAPI 3.0 JSON specification

#### Audit Logs
```bash
GET /api/audit/logs
```

Retrieve audit logs with filtering options. All queries and agent actions are automatically logged for audit purposes.

**Query Parameters:**
- `agent_id`: Filter by agent ID
- `action_type`: Filter by action type (query_execution, natural_language_query, agent_registered, permission_set, etc.)
- `status`: Filter by status (success, error, denied)
- `limit`: Maximum number of logs to return (default: 100, max: 1000)
- `offset`: Number of logs to skip for pagination (default: 0)

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": "2024-01-15T10:30:00Z",
      "action_type": "query_execution",
      "agent_id": "agent-001",
      "status": "success",
      "details": {
        "query_type": "SELECT",
        "tables_accessed": ["users"],
        "row_count": 5,
        "query_preview": "SELECT * FROM users WHERE age > 25"
      }
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0,
  "has_more": true
}
```

**Action Types:**
- `query_execution`: Direct SQL query execution
- `natural_language_query`: Natural language query execution
- `agent_registered`: Agent registration
- `agent_revoked`: Agent revocation
- `permission_set`: Permission assignment
- `permission_revoked`: Permission revocation
- `permission_listed`: Permission listing
- `tables_listed`: Table listing
- `agent_viewed`: Agent information retrieval
- `agents_listed`: Agent list retrieval

#### Get Specific Audit Log
```bash
GET /api/audit/logs/<log_id>
```

Retrieve a specific audit log entry by ID.

#### Audit Statistics
```bash
GET /api/audit/statistics
```

Get statistics about audit logs.

**Query Parameters:**
- `agent_id`: Filter statistics by agent ID (optional)

**Response:**
```json
{
  "total_actions": 150,
  "by_action_type": {
    "query_execution": 80,
    "natural_language_query": 20,
    "agent_registered": 5,
    "permission_set": 10
  },
  "by_status": {
    "success": 140,
    "error": 8,
    "denied": 2
  },
  "recent_actions": [...]
}
```

#### Security Notifications
```bash
GET /api/notifications
```

Get security notifications and alerts. The system automatically monitors for security issues and anomalous access patterns.

**Query Parameters:**
- `severity`: Filter by severity (low, medium, high, critical)
- `agent_id`: Filter by agent ID
- `unread_only`: Only return unread notifications (true/false)
- `limit`: Maximum number of notifications to return (default: 100, max: 1000)

**Response:**
```json
{
  "notifications": [
    {
      "id": 1,
      "timestamp": "2024-01-15T10:30:00Z",
      "event_type": "failed_authentication",
      "severity": "medium",
      "agent_id": "agent-001",
      "message": "Failed authentication attempt",
      "details": {
        "error": "Invalid API key",
        "ip": "192.168.1.1"
      },
      "read": false
    }
  ],
  "total": 25,
  "unread_count": 5,
  "count": 25
}
```

**Security Events Monitored:**
- **Failed Authentication**: Multiple failed login attempts
- **Permission Denied**: Access attempts to unauthorized resources
- **Multiple Failures**: Repeated failures in short time (anomaly)
- **Unusual Access Pattern**: Unusual query rates or patterns
- **Agent Revoked**: Agent access revocation events
- **Rate Limit Exceeded**: Excessive query rates

**Severity Levels:**
- `critical`: Immediate attention required (e.g., multiple security breaches)
- `high`: Important security events (e.g., agent revocation, multiple failures)
- `medium`: Security concerns (e.g., failed authentication, permission denied)
- `low`: Informational security events

#### Mark Notification as Read
```bash
PUT /api/notifications/<notification_id>/read
```

Mark a specific notification as read.

#### Mark All Notifications as Read
```bash
PUT /api/notifications/read-all
```

Mark all notifications as read.

#### Notification Statistics
```bash
GET /api/notifications/stats
```

Get statistics about security notifications.

**Response:**
```json
{
  "total": 25,
  "unread": 5,
  "by_severity": {
    "critical": 2,
    "high": 5,
    "medium": 15,
    "low": 3
  },
  "by_event_type": {
    "failed_authentication": 10,
    "permission_denied": 8,
    "multiple_failures": 2
  },
  "recent_critical": [...]
}
```

### Dashboard Access

The web dashboard includes a **Security Alerts** section that displays recent security notifications. Access the full notifications page at `/notifications` to view all alerts, filter by severity, and manage notification status.

## Developer Guide

### Programmatic Integration

The API is designed for easy programmatic integration. Here's a typical workflow:

**1. Test Database Connection:**
```python
import requests

response = requests.post('http://localhost:5000/api/databases/test', json={
    'connection_string': 'postgresql://user:pass@localhost/db'
})
if response.json()['status'] == 'success':
    print("Database connection valid")
```

**2. Register an Agent:**
```python
response = requests.post('http://localhost:5000/api/agents/register', json={
    'agent_id': 'my-agent',
    'agent_credentials': {
        'api_key': 'agent-key',
        'api_secret': 'agent-secret'
    },
    'database': {
        'connection_string': 'postgresql://user:pass@localhost/db'
    }
})
api_key = response.json()['api_key']
```

**3. Set Permissions:**
```python
requests.put(
    f'http://localhost:5000/api/agents/my-agent/permissions/resources',
    json={
        'resource_id': 'users',
        'permissions': ['read', 'write']
    }
)
```

**4. Execute Queries:**
```python
response = requests.post(
    'http://localhost:5000/api/agents/my-agent/query',
    json={'query': 'SELECT * FROM users LIMIT 10'},
    headers={'X-API-Key': api_key}
)
results = response.json()['result']
```

**5. Update Database Connection:**
```python
requests.put(
    'http://localhost:5000/api/agents/my-agent/database',
    json={
        'connection_string': 'postgresql://new_user:new_pass@new_host/db'
    }
)
```

### Database Failover Endpoints

#### Register Failover Endpoints
```bash
POST /api/admin/agents/<agent_id>/failover/endpoints
Content-Type: application/json

{
  "endpoints": [
    {
      "name": "Primary Database",
      "host": "db-primary.example.com",
      "port": 5432,
      "user": "user",
      "password": "pass",
      "database": "mydb",
      "database_type": "postgresql",
      "is_primary": true,
      "priority": 0
    },
    {
      "name": "Backup Database",
      "host": "db-backup.example.com",
      "port": 5432,
      "user": "user",
      "password": "pass",
      "database": "mydb",
      "database_type": "postgresql",
      "is_primary": false,
      "priority": 1
    }
  ]
}
```

#### Get Failover Status
```bash
GET /api/admin/agents/<agent_id>/failover/status
```

**Response:**
```json
{
  "agent_id": "agent-001",
  "status": "primary",
  "current_endpoint": {
    "endpoint_id": "...",
    "name": "Primary Database",
    "is_primary": true
  },
  "endpoints": [...],
  "available_endpoints": 2,
  "total_endpoints": 2
}
```

#### Reset Endpoint
```bash
POST /api/admin/agents/<agent_id>/failover/endpoints/<endpoint_id>/reset
```

### Dead-Letter Queue Endpoints

#### List DLQ Entries
```bash
GET /api/admin/dlq/entries?agent_id=<agent_id>&status=pending&limit=100
```

#### Get DLQ Entry
```bash
GET /api/admin/dlq/entries/<entry_id>
```

#### Replay DLQ Entry
```bash
POST /api/admin/dlq/entries/<entry_id>/replay
```

**Response:**
```json
{
  "entry": {...},
  "result": [...],
  "message": "Query replayed successfully",
  "retry_count": 1
}
```

#### Archive DLQ Entry
```bash
POST /api/admin/dlq/entries/<entry_id>/archive
```

#### Delete DLQ Entry
```bash
DELETE /api/admin/dlq/entries/<entry_id>
```

#### Get DLQ Statistics
```bash
GET /api/admin/dlq/statistics?agent_id=<agent_id>
```

**Response:**
```json
{
  "total_entries": 10,
  "status_counts": {
    "pending": 5,
    "success": 3,
    "failed": 2
  },
  "error_type_counts": {
    "ConnectionError": 5,
    "SyntaxError": 3
  }
}
```

#### Clear Agent DLQ
```bash
POST /api/admin/dlq/agents/<agent_id>/clear
```

### Error Handling

All endpoints return consistent error responses. Query failures now include formatted error messages:

**Query Error Response:**
```json
{
  "error": "Query execution failed",
  "user_friendly_message": "Invalid column name: 'invalid_column'. Please check the column name and try again.",
  "error_type": "Exception",
  "actionable_details": {
    "column": "invalid_column"
  },
  "suggested_fixes": [
    "Check the column name spelling and case sensitivity",
    "Verify the column exists in the table"
  ],
  "generated_sql": "SELECT invalid_column FROM users",
  "dlq_entry_id": "...",
  "failover_attempted": false
}
```
```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "agent_id": "agent-001"  // if applicable
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created (agent registered)
- `400`: Bad Request (validation error)
- `401`: Unauthorized (missing/invalid API key)
- `403`: Forbidden (permission denied)
- `404`: Not Found (agent/resource not found)
- `500`: Internal Server Error

### API Documentation

Access the OpenAPI specification at `/api/api-docs` for complete API documentation, request/response schemas, and integration details.

## Development

### Running in Development Mode

```bash
export FLASK_ENV=development
python main.py
```

### Testing

CI runs on GitHub Actions (Python 3.10, 3.11, 3.12) with lint (black, isort, bandit) and pytest.

```bash
# Run all unit tests (no external dependencies required)
pytest tests/test_*_unit.py tests/test_smoke.py -v

# 94 tests passed in 0.57s
```

**Test coverage by module:**

| Test File | Tests | Module |
|-----------|-------|--------|
| `test_sql_parser_unit.py` | 16 | SQL parser (extract_tables, get_query_type, permissions) |
| `test_rate_limiter_unit.py` | 11 | Rate limiter (config, sliding window, reset) |
| `test_retry_policy_unit.py` | 16 | Retry policy (delays, strategies, executor) |
| `test_ontoguard_adapter_unit.py` | 20 | OntoGuard adapter + exceptions (pass-through, mock validator) |
| `test_helpers_unit.py` | 10 | Helpers (format_response, validate_json, timestamps) |
| `test_smoke.py` | 3 | Import smoke tests |

**E2E tests** (require PostgreSQL + Docker):
```bash
docker-compose up -d
python e2e_postgres_tests.py  # 15/15 passed
```

## Plugin SDK

The AI Agent Connector includes a Plugin SDK that allows developers to create custom database driver plugins for proprietary or niche databases.

### Overview

The Plugin SDK provides:
- **Base Plugin Class**: `DatabasePlugin` - Abstract base class for all plugins
- **Plugin Registry**: Automatic registration and discovery of plugins
- **TypeScript Types**: Type definitions for plugin development
- **Validation**: Built-in configuration validation
- **Integration**: Seamless integration with the existing database connector factory

### Creating a Plugin

1. **Create a Plugin Class**

```python
from ai_agent_connector.app.db.plugin import DatabasePlugin
from ai_agent_connector.app.db.base_connector import BaseDatabaseConnector
from typing import Dict, Any, List, Optional, Union, Tuple

class MyCustomConnector(BaseDatabaseConnector):
    """Your custom database connector implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Initialize your database client here
    
    def connect(self) -> bool:
        # Implement connection logic
        self._is_connected = True
        return True
    
    def disconnect(self) -> None:
        # Implement disconnection logic
        self._is_connected = False
    
    def execute_query(
        self,
        query: str,
        params: Optional[Union[Dict[str, Any], Tuple, List]] = None,
        fetch: bool = True,
        as_dict: bool = False
    ) -> Optional[Union[List[Tuple], List[Dict[str, Any]]]]:
        # Implement query execution
        return [] if fetch else None
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    def get_database_info(self) -> Dict[str, Any]:
        return {'type': 'my_custom_db', 'version': '1.0.0'}


class MyCustomDatabasePlugin(DatabasePlugin):
    """Plugin for My Custom Database"""
    
    @property
    def plugin_name(self) -> str:
        return "my_custom_db_plugin"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    @property
    def database_type(self) -> str:
        return "my_custom_db"
    
    @property
    def display_name(self) -> str:
        return "My Custom Database"
    
    @property
    def description(self) -> str:
        return "Plugin for connecting to My Custom Database"
    
    @property
    def required_config_keys(self) -> List[str]:
        return ['host', 'database', 'api_key']
    
    @property
    def optional_config_keys(self) -> List[str]:
        return ['port', 'timeout']
    
    def create_connector(self, config: Dict[str, Any]) -> BaseDatabaseConnector:
        return MyCustomConnector(config)
    
    def detect_database_type(self, config: Dict[str, Any]) -> Optional[str]:
        if config.get('type') == 'my_custom_db':
            return 'my_custom_db'
        return None
```

2. **Register the Plugin**

```python
from ai_agent_connector.app.db.plugin import register_plugin

plugin = MyCustomDatabasePlugin()
register_plugin(plugin)
```

3. **Use the Plugin**

```python
from ai_agent_connector.app.db import DatabaseConnector

# Use your custom database type
connector = DatabaseConnector(
    database_type='my_custom_db',
    host='localhost',
    database='mydb',
    api_key='your-api-key'
)

connector.connect()
results = connector.execute_query("SELECT * FROM users")
connector.disconnect()
```

### Loading Plugins from Files

You can load plugins from Python files:

```python
from ai_agent_connector.app.db.plugin import get_plugin_registry

registry = get_plugin_registry()

# Load a single plugin
plugin = registry.load_plugin_from_file('/path/to/plugin.py')

# Load all plugins from a directory
plugins = registry.load_plugins_from_directory('/path/to/plugins')
```

### Plugin API Endpoints

The Plugin SDK includes REST API endpoints for plugin management:

- `GET /api/plugins` - List all registered plugins
- `GET /api/plugins/<database_type>` - Get plugin information
- `DELETE /api/plugins/<database_type>` - Unregister a plugin
- `POST /api/plugins/load` - Load a plugin from a file
- `POST /api/plugins/load-directory` - Load plugins from a directory
- `POST /api/plugins/validate` - Validate plugin configuration
- `GET /api/plugins/supported-types` - Get all supported database types

### Example Plugin

See `examples/plugins/example_custom_db.py` for a complete example plugin implementation.

### TypeScript Types

TypeScript type definitions are available in `ai_agent_connector/app/db/plugin_types.ts` for reference when developing plugins or integrating with TypeScript/JavaScript applications.

### Validation Tests

The Plugin SDK includes comprehensive validation tests. Run them with:

```bash
pytest tests/test_plugin_sdk.py
```

### Plugin Requirements

All plugins must:
1. Extend `DatabasePlugin` base class
2. Implement all abstract methods and properties
3. Return a connector that extends `BaseDatabaseConnector`
4. Implement proper error handling
5. Validate configuration before creating connectors

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


