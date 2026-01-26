# Helm Chart Test Suite

Comprehensive test suite for validating the AI Agent Connector Helm chart.

## Test Files

### `test_chart_structure.py`
Tests the basic Helm chart structure:
- Chart.yaml existence and structure
- values.yaml existence and validity
- Templates directory structure
- Required template files
- Documentation files

### `test_values_validation.py`
Validates values.yaml configuration:
- Image configuration
- Replica count
- Service configuration
- Autoscaling configuration
- Health check configuration
- Resources configuration
- Ingress configuration
- Environment variables
- Secrets and ConfigMap configuration

### `test_helm_templates.py`
Tests Helm template rendering (requires Helm CLI):
- Deployment template rendering
- Service template rendering
- HPA template rendering
- ConfigMap template rendering
- Ingress template rendering
- All templates render without errors

### `test_health_checks.py`
Validates health check probe configuration:
- Liveness probe configuration
- Readiness probe configuration
- Startup probe configuration
- Probe timing and thresholds
- Health check path consistency

### `test_autoscaling.py`
Tests auto-scaling configuration:
- Autoscaling enabled/disabled
- Min/max replicas validation
- CPU and memory targets
- Production autoscaling settings
- Scaling behavior configuration

### `test_security.py`
Validates security configuration:
- Container security context
- Pod security context
- Non-root user configuration
- Capability dropping
- Network policy configuration

### `test_integration.py`
Integration tests for complete chart:
- Production configuration completeness
- Health checks in production
- Replica count consistency
- Service port matching
- Image configuration
- Required templates
- Environment variables
- Resource limits and requests

## Running Tests

### Install Dependencies

```bash
pip install pytest pyyaml
```

### Run All Tests

```bash
# From chart root
pytest tests/ -v

# From project root
pytest helm/ai-agent-connector/tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_chart_structure.py -v
pytest tests/test_values_validation.py -v
pytest tests/test_health_checks.py -v
```

### Run with Helm Template Tests

Some tests require Helm CLI to be installed:

```bash
# Install Helm first
# Then run with --helm-tests flag
pytest tests/ --helm-tests -v
```

### Run Specific Test Class

```bash
pytest tests/test_chart_structure.py::TestChartStructure -v
```

### Run Specific Test

```bash
pytest tests/test_chart_structure.py::TestChartStructure::test_chart_yaml_exists -v
```

## Test Coverage

### ✅ Chart Structure
- Chart.yaml validation
- values.yaml validation
- Template files existence
- Directory structure

### ✅ Values Validation
- All required configuration sections
- Type validation
- Value range validation
- Production vs development values

### ✅ Health Checks
- All three probe types
- Timing configuration
- Path consistency
- Threshold validation

### ✅ Auto-Scaling
- HPA configuration
- Min/max replicas
- Target metrics
- Scaling behavior

### ✅ Security
- Security contexts
- Non-root configuration
- Capability dropping
- Network policies

### ✅ Integration
- Complete configuration validation
- Cross-component consistency
- Production readiness

## Test Statistics

- **Total Test Files**: 7
- **Total Test Classes**: 7
- **Total Test Cases**: 50+
- **Coverage**: All chart components

## Continuous Integration

Tests can be integrated into CI/CD:

```yaml
# Example GitHub Actions
- name: Test Helm Chart
  run: |
    pip install pytest pyyaml
    pytest helm/ai-agent-connector/tests/ -v
```

## Prerequisites

- Python 3.7+
- pytest
- PyYAML
- Helm CLI (optional, for template rendering tests)

## Notes

- Template rendering tests (`test_helm_templates.py`) require Helm CLI
- These tests are skipped by default unless `--helm-tests` flag is used
- Tests validate configuration but don't deploy to Kubernetes
- For actual deployment testing, use a Kubernetes test environment
