# Universal Agent Connector — API Reference

All API routes are under the `/api` prefix. The live OpenAPI spec is available at `GET /api/api-docs` when the application is running.

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Health & Info](#2-health--info)
3. [Database](#3-database)
4. [Agents](#4-agents)
5. [Permissions & Access](#5-permissions--access)
6. [Queries](#6-queries)
7. [Audit & Notifications](#7-audit--notifications)
8. [Cost](#8-cost)
9. [Multi-Agent Collaboration](#9-multi-agent-collaboration)
10. [SSO](#10-sso)
11. [Legal](#11-legal)
12. [Chargeback](#12-chargeback)
13. [Analytics](#13-analytics)
14. [Training Data Export](#14-training-data-export)
15. [Admin AI Agents](#15-admin-ai-agents)
16. [Error Responses](#16-error-responses)

---

## 1. Authentication

Most agent-scoped endpoints require the **`X-API-Key`** header with the agent’s API key (returned at registration). Admin AI endpoints use an admin API key.

```http
X-API-Key: <agent_api_key>
```

- **401 Unauthorized**: Missing or invalid API key.

---

## 2. Health & Info

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check. Returns `{ "status": "healthy", "service": "AI Agent Connector" }`. |
| `GET` | `/api/api-docs` | OpenAPI 3.0 documentation. |
| `GET` | `/api` | Service info, version, and endpoint list. |

---

## 3. Database

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/databases/test` | Test a database connection before registration. |

**Request body** (either):

- `connection_string`: Full DB URL, or
- `host`, `port`, `user`, `password`, `database` (and optional `connection_name`, `type`).

**Response**: `{ "status": "success"|"error", "message", "database_info"?, "error"?" }`

---

## 4. Agents

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/agents/register` | Register a new agent. |
| `GET` | `/api/agents` | List all agents. |
| `GET` | `/api/agents/<agent_id>` | Get agent details. |
| `DELETE` | `/api/agents/<agent_id>` | Revoke agent (removes keys, permissions, DB config). |
| `PUT` | `/api/agents/<agent_id>/database` | Update agent’s database connection. |

### Register Agent

**Request body**:

```json
{
  "agent_id": "string",
  "agent_info": { "name": "string", "type": "string" },
  "agent_credentials": { "api_key": "string", "api_secret": "string" },
  "database": {
    "connection_string": "string",
    "connection_name": "string",
    "type": "postgresql|mysql|..."
  }
}
```

**Response** (`201`): `{ "agent_id", "api_key", "database": { "status", "connection_name", "type" }, "message" }`

---

## 5. Permissions & Access

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/agents/<agent_id>/tables` | List tables/datasets and their permissions. |
| `GET` | `/api/agents/<agent_id>/access-preview` | Preview accessible vs inaccessible tables and columns. |
| `PUT` | `/api/agents/<agent_id>/permissions/resources` | Set resource-level permissions. |
| `GET` | `/api/agents/<agent_id>/permissions/resources` | List resource permissions. |
| `DELETE` | `/api/agents/<agent_id>/permissions/resources/<resource_id>` | Revoke permissions for a resource. |

### Set Resource Permissions

**Request body**:

```json
{
  "resource_id": "schema.table_or_dataset",
  "resource_type": "table|dataset",
  "permissions": ["read", "write"]
}
```

---

## 6. Queries

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/agents/<agent_id>/query` | `X-API-Key` | Execute SQL. |
| `POST` | `/api/agents/<agent_id>/query/natural` | `X-API-Key` | Natural language → SQL, then execute. |

### Execute SQL

**Request body**:

```json
{
  "query": "SELECT ...",
  "params": [],
  "as_dict": false
}
```

**Response** (success): `{ "agent_id", "query_type", "tables_accessed", "success": true, "result", "row_count" }`

**Response** (permission denied): `{ "error", "denied_resources", "message" }`

### Natural Language Query

**Request body**:

```json
{
  "query": "Show me all users older than 25",
  "as_dict": false
}
```

**Response** includes `natural_language_query`, `generated_sql`, `query_type`, `tables_accessed`, `success`, `result`, `row_count`, or `error` / `denied_resources`.

---

## 7. Audit & Notifications

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/audit/logs` | List audit logs (optional: `agent_id`, `action_type`, `status`, `limit`, `offset`). |
| `GET` | `/api/audit/logs/<log_id>` | Get a single log entry. |
| `GET` | `/api/audit/statistics` | Audit statistics (optional: `agent_id`). |
| `GET` | `/api/notifications` | Security notifications (optional: `severity`, `agent_id`, `unread_only`, `limit`). |
| `PUT` | `/api/notifications/<id>/read` | Mark notification as read. |
| `PUT` | `/api/notifications/read-all` | Mark all as read. |
| `GET` | `/api/notifications/stats` | Notification statistics. |

---

## 8. Cost

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/cost/dashboard` | Cost dashboard data. |
| `GET` | `/api/cost/export` | Export cost data (e.g. CSV). |
| `GET` | `/api/cost/stats` | Cost statistics. |
| `GET` | `/api/cost/budget-alerts` | Budget alerts. |

---

## 9. Multi-Agent Collaboration

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/agents/collaborate` | Create collaboration session (NL query). |
| `GET` | `/api/agents/collaborate` | List sessions. |
| `GET` | `/api/agents/collaborate/<session_id>` | Get session. |
| `POST` | `/api/agents/collaborate/<session_id>/execute` | Execute approved SQL. |
| `GET` | `/api/agents/collaborate/<session_id>/trace` | Get collaboration trace. |

---

## 10. SSO

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/sso/configs` | List SSO configs. |
| `POST` | `/api/sso/configs` | Create SSO config. |
| `GET` | `/api/sso/configs/<config_id>` | Get SSO config. |
| `PUT` | `/api/sso/configs/<config_id>` | Update SSO config. |
| `DELETE` | `/api/sso/configs/<config_id>` | Delete SSO config. |
| `POST` | `/api/sso/login/<provider>` | Initiate login. |
| `POST` | `/api/sso/callback/<provider>` | SSO callback. |
| `GET` | `/api/sso/user-profile` | Current user profile. |
| `GET` | `/api/sso/attribute-mapping/<config_id>` | Get attribute mapping. |
| `PUT` | `/api/sso/attribute-mapping/<config_id>` | Set attribute mapping. |

---

## 11. Legal

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/legal/templates` | List legal templates. |
| `POST` | `/api/legal/templates` | Create template. |
| `GET` | `/api/legal/templates/<template_id>` | Get template. |
| `POST` | `/api/legal/documents/generate` | Generate document (ToS, Privacy Policy, etc.). |
| `GET` | `/api/legal/documents/<document_id>` | Get generated document. |
| `GET` | `/api/legal/jurisdictions` | List supported jurisdictions. |

---

## 12. Chargeback

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chargeback/usage` | Record usage. |
| `GET` | `/api/chargeback/usage` | Get usage records. |
| `POST` | `/api/chargeback/allocation-rules` | Create allocation rule. |
| `GET` | `/api/chargeback/allocation-rules` | List rules. |
| `POST` | `/api/chargeback/allocate` | Run allocation. |
| `POST` | `/api/chargeback/invoices` | Create invoice. |
| `GET` | `/api/chargeback/invoices` | List invoices. |

---

## 13. Analytics

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/analytics/telemetry/opt-in` | Opt-in telemetry (`user_id`). |
| `POST` | `/api/analytics/telemetry/opt-out` | Opt-out telemetry. |
| `GET` | `/api/analytics/telemetry/status/<user_id>` | Telemetry status. |
| `POST` | `/api/analytics/events` | Submit analytics events. |
| `GET` | `/api/analytics/dau` | DAU metrics. |
| `GET` | `/api/analytics/query-patterns` | Query pattern analytics. |
| `GET` | `/api/analytics/feature-usage` | Feature usage. |
| `GET` | `/api/analytics/export` | Export analytics (e.g. BI). |

---

## 14. Training Data Export

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/training-data/pairs` | Add query–SQL pair. |
| `GET` | `/api/training-data/pairs` | List pairs. |
| `GET` | `/api/training-data/pairs/<pair_id>` | Get pair. |
| `DELETE` | `/api/training-data/pairs/<pair_id>` | Delete pair. |
| `GET` | `/api/training-data/statistics` | Dataset statistics. |
| `GET` | `/api/training-data/export` | Export (e.g. JSONL, JSON, CSV). |

---

## 15. Admin AI Agents

These require **admin** `X-API-Key`. See main README for request/response shapes.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/admin/ai-agents/register` | Register AI provider config. |
| `GET` | `/api/admin/ai-agents` | List AI agents. |
| `POST` | `/api/admin/ai-agents/<agent_id>/query` | Execute AI query (non-DB). |

Additional admin endpoints (rate limit, retry policy, versions, rollback, webhooks) are documented in the README and OpenAPI spec.

---

## 16. Error Responses

Standard error shape:

```json
{
  "error": "Short error type",
  "message": "Detailed message",
  "agent_id": "optional"
}
```

Query execution errors may also include:

- `user_friendly_message`: Human-readable explanation.
- `suggested_fixes`: Array of remediation hints.
- `actionable_details`: Extra context (e.g. column name).
- `generated_sql`: For NL query failures.
- `dlq_entry_id`: If the query was stored in the dead-letter queue.
- `denied_resources`: For permission denials.

**Common status codes**: `200` OK, `201` Created, `400` Bad Request, `401` Unauthorized, `403` Forbidden, `404` Not Found, `500` Internal Server Error.

---

## GraphQL

GraphQL is served at **`/graphql`**. A playground is at **`/graphql/playground`**. The schema supports queries (and optionally subscriptions) for agents, costs, failover, and related data. See the in-app playground and [ARCHITECTURE](ARCHITECTURE.md) for integration details.

---

For more examples and usage, see the [README](README_GITHUB.md) and the live **`/api/api-docs`** OpenAPI spec.
