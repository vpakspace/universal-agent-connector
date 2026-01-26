# Universal Agent Connector

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![Tests](https://github.com/your-org/universal-agent-connector/workflows/python-tests/badge.svg)](https://github.com/your-org/universal-agent-connector/actions)

**Enterprise-grade connectivity layer for AI agents: secure database access, fine-grained permissions, natural language queries, and MCP governance.**

---

## Table of Contents

- [Overview](#overview)
- [Why Universal Agent Connector?](#why-universal-agent-connector)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Detailed Usage](#detailed-usage)
- [Project Structure](#project-structure)
- [Development](#development)
- [Roadmap](#roadmap)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Contact & Support](#contact--support)

---

## Overview

**Universal Agent Connector** is a Flask-based platform that lets AI agents securely connect to databases, run queries, and respect access control. It acts as a single integration point: you register agents, attach databases, set permissions, and execute SQL or natural language queries—all through a REST API, GraphQL, or embeddable widgets.

### What It Is

- **Connector**: Bridges AI agents (OpenAI, Anthropic, local models) to PostgreSQL, MySQL, MongoDB, BigQuery, Snowflake, and pluggable custom DBs.
- **Governance layer**: Policy engine, PII masking, audit logging, rate limiting, and MCP-oriented tool governance (semantic routing, ontology-based tool filtering).
- **Enterprise stack**: SSO (SAML, OAuth, LDAP), chargeback, adoption analytics, training-data export, legal-document generation, and multi-agent collaboration.

### Key Problems It Solves

| Problem | Solution |
|--------|----------|
| Agents need DB access without raw credentials | Register agents; store encrypted credentials; route queries through the connector |
| Coarse or no permission model | Table/dataset-level read/write permissions, access-preview API, permission enforcement on every query |
| NL → SQL scattered across apps | Centralized NL-to-SQL with schema awareness, validation, and cost tracking |
| Compliance and audit gaps | Audit logs, security notifications, anonymization, data residency, retention policies |
| Many DBs, many agents | Multi-DB support, connection pooling, failover, plugin SDK for custom drivers |
| MCP tool sprawl and context bloat | Semantic router + ontology-based filtering; governance middleware for tools |

---

## Why Universal Agent Connector?

- **One integration point** for agents and databases—no per-app credential and permission logic.
- **Security by default**: Encrypted credentials, permission checks before execution, audit logging, and optional air-gapped mode.
- **Extensible**: Plugin SDK for custom DBs, Universal Ontology Adapter for domain ontologies and generated MCP tools, configurable policies.
- **Production-oriented**: Connection pooling, timeouts, failover, dead-letter queue, rate limiting, cost tracking, and deployment templates (AWS, GCP, Azure, Kubernetes, serverless).

---

## Key Features

### Core

- **Agent registration & management** — Register agents with API keys; manage lifecycle (register, update, revoke).
- **Multi-database support** — PostgreSQL, MySQL, MongoDB, BigQuery, Snowflake; pluggable drivers via Plugin SDK.
- **Fine-grained permissions** — Read/write at table/dataset level; permission preview; enforcement on all queries.
- **Query execution** — Direct SQL and natural language→SQL with permission validation and cost tracking.
- **Connection management** — Pooling, timeouts, encrypted credentials (Fernet), DB failover.

### AI & MCP

- **Multi-provider AI** — OpenAI, Anthropic, local (e.g. Ollama); air-gapped mode for full isolation.
- **Rate limiting & retries** — Per-agent limits; configurable retry (exponential backoff, fixed, linear).
- **MCP Semantic Router** — Ontology-based tool filtering to reduce context size and improve routing.
- **Governance middleware** — Policy engine, PII masking, audit logging around MCP tool execution.
- **Universal Ontology Adapter** — Load ontologies (Turtle, OWL, YAML, JSON-LD); generate and validate MCP tools.

### Enterprise

- **SSO** — SAML 2.0, OAuth 2.0, LDAP; attribute mapping.
- **Legal documents** — Terms of Service, Privacy Policy; multi-jurisdiction (GDPR, CCPA, etc.).
- **Chargeback** — Usage tracking, allocation rules, invoice generation.
- **Adoption analytics** — DAU, query patterns, feature usage; opt-in telemetry.
- **Training data export** — Privacy-safe export of query–SQL pairs for fine-tuning.

### Developer Experience

- **REST & GraphQL** — REST for CRUD and actions; GraphQL for flexible querying.
- **Web UI** — Dashboard, integration wizard, access preview, analytics, cost dashboard, prompt studio.
- **SDKs** — Python and JavaScript/TypeScript clients.
- **CLI** — Node.js CLI (`aidb`) for scripts and CI/CD.
- **Demos** — E-commerce, SaaS metrics, financial reporting with sample data and walkthroughs.
- **Deployment** — Terraform, CloudFormation, Helm, serverless configs for AWS, GCP, Azure.

---

## Architecture

### High-Level Diagram

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                  Universal Agent Connector                │
                    ├─────────────────────────────────────────────────────────┤
                    │  REST API (/api)  │  GraphQL (/graphql)  │  Web UI      │
                    └─────────┬─────────┴──────────┬───────────┴──────┬───────┘
                              │                    │                   │
        ┌─────────────────────┼────────────────────┼───────────────────┼─────────────────────┐
        │                     │                    │                   │                     │
        ▼                     ▼                    ▼                   ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌──────────────┐   ┌──────────────┐   ┌─────────────────┐
│ Agent         │   │ Permissions &   │   │ DB Connectors│   │ AI Manager   │   │ MCP / Ontology  │
│ Registry      │   │ Access Control  │   │ (Factory +   │   │ (Providers,  │   │ (Semantic       │
│               │   │                 │   │  Pooling)    │   │  Rate Limit) │   │  Router, JAG)   │
└───────┬───────┘   └────────┬────────┘   └──────┬───────┘   └──────┬───────┘   └────────┬────────┘
        │                    │                    │                  │                    │
        └────────────────────┴────────────────────┴──────────────────┴────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
            ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
            │ PostgreSQL    │         │ MySQL         │         │ MongoDB,      │
            │               │         │               │         │ BigQuery,     │
            │               │         │               │         │ Snowflake     │
            └───────────────┘         └───────────────┘         └───────────────┘
```

### Component Overview

| Component | Purpose |
|----------|---------|
| **API (REST)** | Agents, DBs, permissions, queries, audit, SSO, legal, chargeback, analytics, training-data export |
| **GraphQL** | Flexible querying; hooks into cost tracking, failover |
| **Agent Registry** | Registration, API-key auth, lifecycle |
| **Access Control** | Resource-level permissions; used by query execution |
| **DB Connectors** | Factory + pooling; multi-DB and plugin support |
| **AI Agent Manager** | Multi-provider AI, rate limits, retries, webhooks |
| **MCP / Ontology** | Semantic router, governance middleware, Universal Ontology Adapter |

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design, data flow, and patterns.

---

## Quick Start

### Prerequisites

- **Python 3.8+**
- **PostgreSQL** (or another supported DB) for testing
- **Virtual environment** (recommended)

### Installation

```bash
git clone https://github.com/your-org/universal-agent-connector.git
cd universal-agent-connector

python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### Configuration

```bash
# Optional but recommended for production
export SECRET_KEY="your-secret-key"
export ENCRYPTION_KEY="your-fernet-key"   # For credential encryption
export OPENAI_API_KEY="your-openai-key"   # For natural language queries
```

Generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Run

```bash
python main.py
```

Default: **http://127.0.0.1:5000**

### Basic Usage

**1. Test database connection**

```bash
curl -X POST http://127.0.0.1:5000/api/databases/test \
  -H "Content-Type: application/json" \
  -d '{"connection_string": "postgresql://user:pass@localhost:5432/mydb"}'
```

**2. Register an agent**

```bash
curl -X POST http://127.0.0.1:5000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my-agent",
    "agent_credentials": {"api_key": "agent-key", "api_secret": "agent-secret"},
    "database": {
      "connection_string": "postgresql://user:pass@localhost:5432/mydb",
      "connection_name": "mydb",
      "type": "postgresql"
    }
  }'
```

**3. Set permissions**

```bash
curl -X PUT "http://127.0.0.1:5000/api/agents/my-agent/permissions/resources" \
  -H "Content-Type: application/json" \
  -d '{"resource_id": "public.users", "resource_type": "table", "permissions": ["read"]}'
```

**4. Execute a query** (use the `api_key` from registration)

```bash
curl -X POST "http://127.0.0.1:5000/api/agents/my-agent/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <agent_api_key>" \
  -d '{"query": "SELECT * FROM users LIMIT 5"}'
```

### Access Points

| Resource | URL |
|----------|-----|
| Dashboard | http://127.0.0.1:5000/dashboard |
| Integration wizard | http://127.0.0.1:5000/wizard |
| API docs | http://127.0.0.1:5000/api/api-docs |
| GraphQL playground | http://127.0.0.1:5000/graphql/playground |
| Analytics | http://127.0.0.1:5000/analytics |
| Console | http://127.0.0.1:5000/console (PIN at startup) |

---

## Detailed Usage

### Configuration

Use environment variables for configuration. Key options:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | `development` / `production` / `testing` | `development` |
| `PORT` | Server port | `5000` |
| `HOST` | Bind host | `127.0.0.1` |
| `SECRET_KEY` | Flask secret | (dev default) |
| `ENCRYPTION_KEY` | Fernet key for DB credentials | (temp key in dev) |
| `OPENAI_API_KEY` | For NL→SQL | — |
| `AIR_GAPPED_MODE` | Disable external AI APIs | `false` |
| `LOCAL_AI_BASE_URL` | Local AI endpoint (e.g. Ollama) | `http://localhost:11434` |
| `LOCAL_AI_MODEL` | Default local model | `llama2` |

### Programmatic Integration (Python)

```python
import requests

BASE = "http://localhost:5000/api"

# 1. Register agent
r = requests.post(f"{BASE}/agents/register", json={
    "agent_id": "analytics-agent",
    "agent_credentials": {"api_key": "k", "api_secret": "s"},
    "database": {
        "connection_string": "postgresql://user:pass@localhost/analytics",
        "connection_name": "analytics",
        "type": "postgresql"
    }
})
api_key = r.json()["api_key"]

# 2. Set permissions
requests.put(f"{BASE}/agents/analytics-agent/permissions/resources", json={
    "resource_id": "public.sales",
    "resource_type": "table",
    "permissions": ["read"]
})

# 3. Query
r = requests.post(
    f"{BASE}/agents/analytics-agent/query",
    headers={"X-API-Key": api_key},
    json={"query": "SELECT COUNT(*) FROM sales"}
)
print(r.json()["result"])
```

### Python SDK

```bash
pip install universal-agent-connector
```

```python
from universal_agent_connector import UniversalAgentConnector

client = UniversalAgentConnector(base_url="http://localhost:5000", api_key="admin-key")
agent = client.register_agent(
    agent_id="my-agent",
    agent_credentials={"api_key": "key", "api_secret": "secret"},
    database={"host": "localhost", "database": "mydb", "user": "u", "password": "p"}
)
result = client.execute_query("my-agent", "SELECT 1", api_key=agent["api_key"])
```

See [sdk/README.md](../sdk/README.md) and [SDK JS](../sdk-js/) for full SDK usage.

### Interactive Demos

- **[E-Commerce](demos/ecommerce/)** — Sales, customers, products.
- **[SaaS Metrics](demos/saas/)** — MRR, churn, growth.
- **[Financial](demos/financial/)** — Transactions, reports.

```bash
./demos/setup_all_demos.sh   # or demos\setup_all_demos.ps1 on Windows
```

### API Reference

- **OpenAPI**: `GET /api/api-docs` when the app is running.
- **Detailed reference**: [API](API.md)

### Documentation

- **[Documentation Index](DOCUMENTATION_INDEX.md)** — Full doc index
- **[ARCHITECTURE](ARCHITECTURE.md)** — Design, components, data flow
- **[API](API.md)** — REST & GraphQL reference

---

## Project Structure

```
Universal Agent Connector/
├── ai_agent_connector/          # Main Python package
│   └── app/
│       ├── api/                 # REST routes (routes.py)
│       ├── agents/              # Registry, AI manager, providers
│       ├── auth/                # SSO
│       ├── db/                  # Connectors, factory, pooling, plugin
│       ├── graphql/             # GraphQL schema and routes
│       ├── permissions/         # Access control
│       ├── prompts/             # Prompt studio
│       ├── utils/               # NL→SQL, cost, audit, chargeback, etc.
│       └── widgets/             # Embeddable widgets
├── src/                         # Intelligence & ontology
│   ├── intelligence/            # Ontology adapter, tool registry, validation
│   ├── ontology/                # Compliance guardrails
│   ├── evaluation/              # MINE, spectral analysis
│   ├── disambiguation/          # JAG resolver, type checker
│   └── reports/                 # Integrity reports
├── tests/                       # Test suite
├── docs/                        # Guides and references
├── demos/                       # E-commerce, SaaS, financial
├── deployment/                  # Cloud deployment guides
├── terraform/                   # IaC (AWS, GCP, Azure)
├── helm/                        # Kubernetes
├── serverless/                  # Lambda, Azure Functions, GCP
├── cli/                         # Node.js CLI
├── sdk/                         # Python SDK
├── sdk-js/                      # JS/TS SDK
├── main.py                      # Entry point
├── requirements.txt
└── config/                      # e.g. ontology_config.yaml
```

---

## Development

### Setup

```bash
python -m venv venv
source venv/bin/activate   # or .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy
```

### Tests

```bash
pytest tests/ -v
pytest tests/ --cov=ai_agent_connector --cov-report=html
pytest tests/test_api_routes.py tests/test_access_control.py -v
```

### Code Style

- **Formatter**: `black .`
- **Linting**: `flake8 .`
- **Type hints** and **Google-style docstrings** encouraged.

See [CONTRIBUTING.md](../CONTRIBUTING.md) and [docs/CODE_STYLE_GUIDE.md](CODE_STYLE_GUIDE.md) for full guidelines.

---

## Roadmap

- **Short-term**: Richer OpenAPI spec, additional DB plugins, performance tuning.
- **Medium-term**: Enhanced MCP tool governance, more ontology formats, RBAC extensions.
- **Long-term**: Distributed tracing, additional cloud regions, marketplace for ontologies and plugins.

See [CHANGELOG.md](../CHANGELOG.md) for version history.

---

## License

This project is licensed under the **MIT License** — see [LICENSE](../LICENSE) for details.

---

## Acknowledgments

- Flask, OpenAI, Anthropic, and the open-source libraries listed in `requirements.txt`.
- Contributors and adopters of the Universal Agent Connector and MCP ecosystems.

---

## Contact & Support

- **Documentation**: [docs/](docs/), [API.md](API.md), [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues**: [GitHub Issues](https://github.com/cloudbadal007/universal-agent-connector/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cloudbadal007/universal-agent-connector/discussions)
- **Security**: See [SECURITY.md](../SECURITY.md) and [THREAT_MODEL.md](../THREAT_MODEL.md)
- **Medium Article**: [Universal Agent Connector — MCP, Ontology, Production-Ready AI Infrastructure](https://medium.com/@cloudpankaj/universal-agent-connector-mcp-ontology-production-ready-ai-infrastructure-0b4e35f22942)

---

*Universal Agent Connector — connect AI agents to data, securely and at scale.*
