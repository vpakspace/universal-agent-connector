# Universal Agent Connector — Architecture

This document describes the high-level architecture, components, data flow, design patterns, and technology choices for the Universal Agent Connector.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Core Components](#3-core-components)
4. [Data Flow](#4-data-flow)
5. [Design Patterns](#5-design-patterns)
6. [Technology Stack](#6-technology-stack)
7. [Key Dependencies](#7-key-dependencies)
8. [Security & Error Handling](#8-security--error-handling)
9. [Performance Considerations](#9-performance-considerations)
10. [Extension Points](#10-extension-points)

---

## 1. System Overview

Universal Agent Connector is a **centralized connectivity and governance layer** between AI agents and data stores. It provides:

- **Registration and auth**: Agents identify via API keys; credentials are stored encrypted.
- **Access control**: Table/dataset-level read/write permissions enforced on every query.
- **Query execution**: SQL and natural language→SQL, with validation and cost tracking.
- **Observability**: Audit logs, security notifications, cost tracking, adoption analytics.
- **MCP / ontology**: Semantic routing, policy-based tool governance, ontology-driven tool generation.

The system is **stateless at the application layer**: agent metadata, permissions, and connection configs can be backed by a store (in-memory, DB, etc.). The Flask app itself does not mandate a specific persistence layer.

---

## 2. High-Level Architecture

### 2.1 Entry Points

| Entry Point | Purpose |
|-------------|---------|
| **REST API** (`/api`) | Agent CRUD, DB tests, permissions, queries, audit, SSO, legal, chargeback, analytics, training-data export, admin AI agents |
| **GraphQL** (`/graphql`) | Flexible querying; integrates with cost tracking, failover |
| **Web UI** | Dashboard, wizard, agents, access preview, analytics, cost dashboard, prompt studio, notifications |
| **Widgets** (`/widget`) | Embeddable query widgets |
| **Prompt studio** (`/prompts`) | Prompt templates and management |

### 2.2 Component Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              Universal Agent Connector                             │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ REST API    │  │ GraphQL     │  │ Web UI      │  │ Widgets     │              │
│  │ (Flask BP)  │  │ (Graphene)  │  │ (Jinja2)    │  │ (embed)     │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                │                      │
│         └────────────────┴────────────────┴────────────────┘                      │
│                                    │                                              │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐   │
│  │                    Application / Service Layer                             │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │   │
│  │  │ Agent        │ │ Access       │ │ Audit        │ │ Cost Tracker     │  │   │
│  │  │ Registry     │ │ Control      │ │ Logger       │ │                  │  │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘  │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │   │
│  │  │ AI Agent     │ │ NL→SQL       │ │ DB Connector │ │ Security         │  │   │
│  │  │ Manager      │ │ Converter    │ │ Factory      │ │ Monitor          │  │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘  │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                        │   │
│  │  │ Agent        │ │ SSO          │ │ Enterprise   │  (chargeback, legal,   │   │
│  │  │ Orchestrator │ │ Manager      │ │ Utils        │   analytics, etc.)     │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                        │   │
│  └────────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                              │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐   │
│  │                    MCP / Ontology / Intelligence (optional)                 │   │
│  │  ┌──────────────────┐ ┌──────────────────┐ ┌────────────────────────────┐  │   │
│  │  │ MCP Semantic     │ │ Governance       │ │ Universal Ontology Adapter  │  │   │
│  │  │ Router           │ │ Middleware       │ │ (ontologies → tools)        │  │   │
│  │  └──────────────────┘ └──────────────────┘ └────────────────────────────┘  │   │
│  │  ┌──────────────────┐ ┌──────────────────┐ ┌────────────────────────────┐  │   │
│  │  │ Policy Engine    │ │ NL Resource      │ │ JAG (disambiguation,        │  │   │
│  │  │                  │ │ Resolver         │ │  MINE, guardrails, etc.)    │  │   │
│  │  └──────────────────┘ └──────────────────┘ └────────────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                              │
└────────────────────────────────────┼──────────────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
  ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
  │ PostgreSQL  │            │ MySQL       │            │ MongoDB,    │
  │             │            │             │            │ BigQuery,   │
  │             │            │             │            │ Snowflake   │
  └─────────────┘            └─────────────┘            └─────────────┘
```

### 2.3 Deployment Topology

The app can run as:

- **Single process**: `python main.py` (dev).
- **Container**: Dockerfile; run behind a reverse proxy (e.g. Nginx).
- **Kubernetes**: Helm charts in `helm/`.
- **Serverless**: AWS Lambda, Azure Functions, GCP Cloud Functions (see `serverless/`).
- **Cloud**: Terraform/CloudFormation for AWS, GCP, Azure (see `deployment/`, `terraform/`).

---

## 3. Core Components

### 3.1 Agent Registry (`ai_agent_connector.app.agents.registry`)

- **Purpose**: Register agents, issue/validate API keys, store agent metadata and DB config.
- **Key operations**: `register()`, `get()`, `authenticate_agent()`, `revoke()`, `update_database()`.
- **Inputs**: Agent id, credentials, database config.
- **Outputs**: API key, agent info, connection status.

### 3.2 Access Control (`ai_agent_connector.app.permissions.access_control`)

- **Purpose**: Enforce table/dataset-level read/write permissions.
- **Key operations**: `has_permission()`, `has_resource_permission()`, `set_resource_permissions()`, `revoke_resource_permissions()`.
- **Inputs**: Agent id, resource id, permission type (read/write).
- **Outputs**: Boolean checks; used by query execution before running SQL.

### 3.3 Database Connectors (`ai_agent_connector.app.db`)

- **Purpose**: Connect to supported DBs, execute queries, pool connections.
- **Components**:
  - **Factory** (`factory.py`): Instantiates connector by `database_type`.
  - **Connectors** (`connector.py`, `connectors.py`): Per-DB implementations (PostgreSQL, MySQL, etc.).
  - **Pooling** (`pooling.py`): Connection pooling.
  - **Plugin** (`plugin.py`): Plugin SDK for custom drivers.
- **Inputs**: Connection config (string or params), query, params, `as_dict` flag.
- **Outputs**: Rows, row count, connection status.

### 3.4 AI Agent Manager (`ai_agent_connector.app.agents.ai_agent_manager`)

- **Purpose**: Manage AI provider configs (OpenAI, Anthropic, local), rate limits, retries, webhooks, versioning.
- **Key operations**: Register AI agent, execute non-DB AI queries, rate-limit checks, retry logic.
- **Inputs**: Provider, model, API key, rate limits, retry policy, webhook config.
- **Outputs**: AI responses, usage stats, webhook events.

### 3.5 NL→SQL Converter (`ai_agent_connector.app.utils.nl_to_sql`)

- **Purpose**: Convert natural language questions to SQL using schema context and AI.
- **Inputs**: NL query, schema info, agent context.
- **Outputs**: Generated SQL, optionally executed results; integrates with cost tracker.

### 3.6 Audit Logger (`ai_agent_connector.app.utils.audit_logger`)

- **Purpose**: Log actions (registration, permissions, queries, etc.) for compliance and debugging.
- **Inputs**: Action type, agent id, status, details.
- **Outputs**: Stored log entries; exposed via `/api/audit/*`.

### 3.7 Cost Tracker (`ai_agent_connector.app.utils.cost_tracker`)

- **Purpose**: Track query cost, token usage, budgets; feed dashboards and chargeback.
- **Inputs**: Agent id, query metadata, token counts, provider costs.
- **Outputs**: Aggregated costs, budget alerts; used by GraphQL and APIs.

### 3.8 Security Monitor (`ai_agent_connector.app.utils.security_monitor`)

- **Purpose**: Detect anomalies (failed auth, permission denied, unusual patterns) and emit notifications.
- **Inputs**: Auth events, permission denials, error rates.
- **Outputs**: Security notifications; consumed by `/api/notifications`.

### 3.9 Agent Orchestrator (`ai_agent_connector.app.utils.agent_orchestrator`)

- **Purpose**: Multi-agent collaboration (e.g. schema research, SQL generation, validation) for complex NL workflows.
- **Inputs**: Collaboration session config, NL query.
- **Outputs**: Session id, trace, final SQL/result.

### 3.10 MCP Semantic Router (`mcp_semantic_router.py`)

- **Purpose**: Use a business ontology to filter MCP tools and reduce context; route NL to concepts (Revenue, Customer, etc.).
- **Inputs**: NL query, ontology, tool usage stats.
- **Outputs**: Resolved concept, filtered tool list.

### 3.11 Policy Engine (`policy_engine.py`)

- **Purpose**: Validate MCP tool calls (rate limits, RLS, complexity, PII access).
- **Inputs**: User id, tenant id, tool name, arguments.
- **Outputs**: `ValidationResult` (allowed/denied, reason, suggestions).

### 3.12 Governance Middleware (`mcp_governance_middleware.py`)

- **Purpose**: Wrap MCP tools with policy checks, PII masking, and audit logging.
- **Inputs**: Tool decorator config (`requires_pii`, `sensitivity_level`), tool args.
- **Outputs**: Governed tool; audit records; masked results.

### 3.13 Universal Ontology Adapter (`src.intelligence`)

- **Purpose**: Load ontologies (Turtle, OWL, YAML, JSON-LD), extract classes/properties/axioms, generate MCP tools, validate operations.
- **Key modules**: `ontology_adapter`, `tool_registry`, `validation_engine`, `ontology_validator`, `doc_generator`.
- **Inputs**: Ontology file path, config (`config/ontology_config.yaml`).
- **Outputs**: Parsed ontology, generated tools, validation results, health reports.

---

## 4. Data Flow

### 4.1 Query Execution (SQL)

1. Client sends `POST /api/agents/<id>/query` with `X-API-Key` and JSON `{ "query": "SELECT ..." }`.
2. **Auth**: Registry validates API key → agent id.
3. **Permissions**: Access control checks read/write for tables extracted from SQL (e.g. via `sql_parser`).
4. **Execution**: Connector factory returns appropriate DB connector; query runs (pooled).
5. **Audit**: Audit logger records action; security monitor may emit events.
6. **Cost**: Cost tracker records usage.
7. Response: `{ "success": true, "result": [...], "row_count": n }` or error with `user_friendly_message`, `suggested_fixes`, etc.

### 4.2 Natural Language Query

1. Client sends `POST /api/agents/<id>/query/natural` with `{ "query": "Show me ..." }`.
2. **Auth** and **permissions** (as above; permissions applied to generated SQL).
3. **NL→SQL**: Converter uses schema + AI to produce SQL.
4. **Validation**: Same permission and table checks as SQL path.
5. **Execution**, **audit**, **cost** as above.
6. Response includes `natural_language_query`, `generated_sql`, `result`, etc.

### 4.3 Multi-Agent Collaboration

1. Client creates session via `POST /api/agents/collaborate` with NL query.
2. Orchestrator runs multi-step workflow (schema research → SQL generation → validation).
3. Client can `GET /api/agents/collaborate/<session_id>/trace` and `POST .../execute` to run approved SQL.
4. Audit and cost track each step.

### 4.4 MCP Tool Call (Governed)

1. MCP client invokes a tool wrapped with `governed_mcp_tool`.
2. Middleware extracts `user_id`, `tenant_id` from context.
3. **Policy engine** validates (rate limit, RLS, complexity, PII).
4. On success: run tool; optionally **PII-mask** results; **audit** log.
5. On failure: return structured error with `ValidationResult`.

---

## 5. Design Patterns

| Pattern | Where | Purpose |
|--------|-------|---------|
| **Blueprint (Flask)** | API, GraphQL, widgets, prompts | Modular routing |
| **Factory** | DB connectors | Create connector by type |
| **Registry** | Agents, plugins | Central registration and lookup |
| **Decorator** | Governance middleware | Cross-cutting policy, audit, masking |
| **Strategy** | Retry policies, AI providers | Pluggable behavior |
| **Adapter** | Ontology parsers (Turtle, YAML, JSON-LD) | Uniform interface over different formats |
| **Dependency injection** | Cost tracker, failover manager | Pass shared services into GraphQL, NL→SQL, etc. |

---

## 6. Technology Stack

| Layer | Technologies |
|-------|--------------|
| **Runtime** | Python 3.8+ |
| **Web** | Flask 3.x, Jinja2 |
| **API** | REST (Flask routes), GraphQL (Graphene, flask-graphql) |
| **Databases** | PostgreSQL (primary), MySQL, MongoDB, BigQuery, Snowflake; `psycopg2`, `pymysql`, `pymongo`, etc. |
| **AI** | OpenAI, Anthropic; optional local (e.g. Ollama) |
| **Security** | `cryptography` (Fernet), API-key auth, SSO (SAML, OAuth, LDAP) |
| **Ontology / analysis** | `rdflib`, `pyyaml`, `networkx`, `numpy`, `scipy` |
| **Testing** | pytest, pytest-cov, pytest-mock, pytest-benchmark |
| **Load testing** | Locust |
| **Deployment** | Docker, Terraform, CloudFormation, Helm, serverless configs |

---

## 7. Key Dependencies

| Dependency | Purpose |
|------------|---------|
| **Flask** | Web framework, blueprints, request handling |
| **openai** | NL→SQL and other OpenAI-based features |
| **anthropic** | Anthropic provider support |
| **psycopg2-binary** | PostgreSQL connector |
| **pymysql, pymongo, google-cloud-bigquery, snowflake-connector-python** | Additional DBs |
| **cryptography** | Credential encryption (Fernet) |
| **graphene, flask-graphql** | GraphQL API |
| **requests** | Outbound HTTP (e.g. AI, webhooks) |
| **rdflib, pyyaml** | Ontology parsing |
| **networkx, numpy, scipy** | Graph and spectral analysis (e.g. MINE, JAG) |

---

## 8. Security & Error Handling

- **Authentication**: API key in `X-API-Key`; validated via Agent Registry.
- **Authorization**: Access control checks before every query; denied resources returned in error payload.
- **Secrets**: DB credentials encrypted at rest; use `ENCRYPTION_KEY` in production.
- **Audit**: All material actions logged; support for anonymization and retention policies.
- **Error responses**: Consistent JSON shape with `error`, `message`, `user_friendly_message`, `suggested_fixes`, `dlq_entry_id` where relevant.
- **Threat model**: See [THREAT_MODEL.md](../THREAT_MODEL.md); mitigations in [SECURITY.md](../SECURITY.md).

---

## 9. Performance Considerations

- **Connection pooling**: Used for DB connectors to avoid per-query connection churn.
- **Timeouts**: Configurable for connections and queries.
- **Rate limiting**: Per-agent limits (e.g. queries per minute/hour) to protect downstream AI and DBs.
- **Caching**: Policy engine caches validation results with TTL; query cache and other utils can be enabled where applicable.
- **Failover**: Database failover support to switch to backup endpoints on failure.
- **Load testing**: Locust-based load tests in `load_tests/`.

---

## 10. Extension Points

| Extension | Mechanism | Location |
|-----------|-----------|----------|
| **Custom DB** | Plugin SDK; implement `DatabasePlugin` and `BaseDatabaseConnector` | `ai_agent_connector.app.db.plugin`, `examples/plugins/` |
| **Ontology format** | Implement `OntologyAdapter` | `src.intelligence.ontology_adapter` |
| **AI provider** | Add provider in AI Agent Manager | `ai_agent_connector.app.agents.providers` |
| **MCP tools** | Ontology-driven generation via Tool Registry; governance via decorator | `src.intelligence.tool_registry`, `mcp_governance_middleware` |
| **SSO** | SSO config and provider hooks | `ai_agent_connector.app.auth.sso` |

---

For deployment, configuration, and API details, see [README](README_GITHUB.md), [API](API.md), and the [deployment](../deployment/README.md) guides.
