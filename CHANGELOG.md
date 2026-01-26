# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (New features)

### Changed
- (Changes in existing functionality)

### Deprecated
- (Soon-to-be removed features)

### Removed
- (Removed features)

### Fixed
- (Bug fixes)

### Security
- (Security-related changes)

---

## [1.0.0] - 2026-01-26

### 🎉 Initial Public Release - "Genesis"

This is the first public release of Universal Agent Connector, representing a complete enterprise-grade infrastructure layer for AI agents.

### Added

#### Core Infrastructure
- Multi-database support: PostgreSQL, MySQL, MongoDB, BigQuery, Snowflake
- Agent registry with API key authentication
- Fine-grained permission system (table/dataset level read/write)
- Connection pooling and timeout management
- Database failover and dead-letter queue
- Encrypted credential storage (Fernet encryption)

#### AI & MCP Integration
- Multi-provider AI support: OpenAI, Anthropic, local models (Ollama), custom providers
- Air-gapped mode for complete network isolation
- Rate limiting and retry policies (exponential backoff, fixed, linear)
- MCP Semantic Router with ontology-based tool filtering
- Governance middleware for MCP tools
- Universal Ontology Adapter (OWL, Turtle, YAML, JSON-LD support)

#### Enterprise Features
- SSO integration: SAML 2.0, OAuth 2.0, LDAP with attribute mapping
- Legal documents generator (Terms of Service, Privacy Policy) with multi-jurisdiction compliance
- Chargeback reports with usage tracking and invoice generation
- Adoption analytics (DAU, query patterns, feature usage)
- Training data export for model fine-tuning
- Audit logging with anonymization
- Security monitoring and alerting
- Data residency rules enforcement
- Data retention policies

#### Developer Experience
- REST API with 100+ endpoints
- GraphQL API for flexible querying
- Python SDK with full type hints
- JavaScript/TypeScript SDK
- Node.js CLI tool (`aidb`)
- Web dashboard and integration wizard
- Interactive demos (e-commerce, SaaS, financial)
- Comprehensive documentation (30+ guides)

#### Deployment & Infrastructure
- Docker support
- Kubernetes Helm charts
- Terraform modules for AWS, GCP, Azure
- CloudFormation templates
- Serverless deployments (Lambda, Azure Functions, GCP Cloud Functions)
- GitHub Actions CI/CD workflows

#### Query Features
- Natural language to SQL conversion
- Query optimization with EXPLAIN analysis
- Query scheduling (hourly, daily, weekly, monthly, cron)
- Query caching
- Query templates and sharing
- Query suggestions and autocomplete
- Result visualizations (charts, tables)
- Query export to external systems (S3, Google Sheets, Slack, Email)

#### Additional Features
- Multi-agent collaboration with orchestration
- Prompt Studio for prompt engineering
- Widget embedding for blogs/websites
- A/B testing for AI models
- Row-level security
- PII masking
- Contextual help tooltips
- Schema-aware autocomplete

### Documentation
- Architecture guide with system design
- Complete API reference (REST & GraphQL)
- Deployment guides for all major clouds
- Feature-specific guides (SSO, chargeback, analytics, etc.)
- Developer setup and code style guide
- Video tutorials
- Contributing guidelines
- Security policy and threat model

### Statistics
- 574 files
- 166,144+ lines of code
- Comprehensive test suite
- 30+ documentation pages

---

## [0.1.0] - 2024-01-XX

### Added
- Initial release of AI Agent Connector
- Agent registration with API credentials
- PostgreSQL database connector
- Fine-grained permission management (read/write on tables/datasets)
- Natural language to SQL query conversion
- Comprehensive audit logging system
- Security monitoring and notifications
- RESTful API for all operations
- Web dashboard and integration wizard for non-technical users
- Self-service access preview feature
- Agent revocation capabilities
- API documentation endpoint

### Features
- **Database Connection**: Connect PostgreSQL databases securely
- **Agent Management**: Register, view, and revoke AI agents
- **Permission Control**: Set read/write permissions on specific tables
- **Natural Language Queries**: Submit questions in plain English
- **Audit Logs**: View complete history of all queries and actions
- **Security Monitoring**: Automatic detection of security issues and anomalies
- **User-Friendly UI**: Dashboard and wizard for easy setup
- **Access Transparency**: Preview which tables/fields agents can access

### Technical Details
- Flask-based REST API
- OpenAI integration for NL-to-SQL conversion
- Secure credential hashing (SHA-256)
- Permission enforcement at query level
- Comprehensive test coverage (86+ tests)





