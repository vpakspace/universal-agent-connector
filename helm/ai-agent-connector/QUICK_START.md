# Helm Chart Quick Start Guide

## Prerequisites

- Kubernetes cluster (1.19+)
- Helm 3.0+
- kubectl configured

## Quick Installation

### 1. Build and Push Docker Image

```bash
# Build image
docker build -t your-registry/ai-agent-connector:1.0.0 .

# Push to registry
docker push your-registry/ai-agent-connector:1.0.0
```

### 2. Create Secrets

```bash
# Generate encryption key
ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Create secret
kubectl create secret generic ai-agent-connector-secret \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=ENCRYPTION_KEY="$ENCRYPTION_KEY" \
  --from-literal=OPENAI_API_KEY="your-openai-key" \
  --namespace production
```

### 3. Install Chart

```bash
# Install with production values
helm install ai-agent-connector ./helm/ai-agent-connector \
  -f helm/ai-agent-connector/values-production.yaml \
  --set image.repository=your-registry/ai-agent-connector \
  --set image.tag=1.0.0 \
  --namespace production \
  --create-namespace
```

### 4. Verify Installation

```bash
# Check pods
kubectl get pods -n production -l app.kubernetes.io/name=ai-agent-connector

# Check service
kubectl get svc -n production ai-agent-connector

# Check HPA
kubectl get hpa -n production ai-agent-connector

# Port forward and test
kubectl port-forward -n production svc/ai-agent-connector 5000:5000
curl http://localhost:5000/api/health
```

## Common Commands

```bash
# Upgrade
helm upgrade ai-agent-connector ./helm/ai-agent-connector \
  -f helm/ai-agent-connector/values-production.yaml \
  --namespace production

# Uninstall
helm uninstall ai-agent-connector --namespace production

# View values
helm get values ai-agent-connector --namespace production

# View all resources
helm get all ai-agent-connector --namespace production
```
