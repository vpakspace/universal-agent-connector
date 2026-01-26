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





