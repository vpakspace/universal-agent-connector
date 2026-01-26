# Helm Chart for Kubernetes Deployment

## Overview

Production-ready Helm chart for deploying AI Agent Connector to Kubernetes with configurable values, health checks, and auto-scaling.

## Acceptance Criteria

✅ **Helm Chart with Configurable Values** - Comprehensive values.yaml with all configuration options  
✅ **Health Checks** - Liveness, readiness, and startup probes configured  
✅ **Auto-Scaling** - HorizontalPodAutoscaler with CPU and memory metrics

## Implementation Details

### 1. Chart Structure

**Directory**: `helm/ai-agent-connector/`

**Files**:
- `Chart.yaml` - Chart metadata and version
- `values.yaml` - Default configuration values
- `values-production.yaml` - Production-ready values
- `values-development.yaml` - Development values
- `README.md` - Comprehensive documentation
- `.helmignore` - Files to ignore when packaging

**Templates**:
- `_helpers.tpl` - Template helpers and labels
- `deployment.yaml` - Deployment with health checks
- `service.yaml` - Service definition
- `hpa.yaml` - HorizontalPodAutoscaler
- `ingress.yaml` - Ingress configuration
- `configmap.yaml` - ConfigMap for configuration
- `secret.yaml` - Secret template
- `serviceaccount.yaml` - Service account
- `networkpolicy.yaml` - Network policy (optional)
- `pdb.yaml` - Pod disruption budget
- `NOTES.txt` - Post-installation notes

### 2. Health Checks

**Three Types of Probes**:

#### Liveness Probe
- Detects if container is running
- Restarts container on failure
- Path: `/api/health`
- Configurable delays and thresholds

#### Readiness Probe
- Detects if container is ready for traffic
- Removes pod from service on failure
- Path: `/api/health`
- Faster than liveness probe

#### Startup Probe
- Gives container time to start
- Prevents premature restarts
- Path: `/api/health`
- Higher failure threshold

**Configuration**:
```yaml
healthCheck:
  livenessProbe:
    enabled: true
    initialDelaySeconds: 30
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
  readinessProbe:
    enabled: true
    initialDelaySeconds: 10
    periodSeconds: 5
    timeoutSeconds: 3
    failureThreshold: 3
  startupProbe:
    enabled: true
    initialDelaySeconds: 0
    periodSeconds: 10
    timeoutSeconds: 3
    failureThreshold: 30
```

### 3. Auto-Scaling

**HorizontalPodAutoscaler (HPA)**:
- CPU-based scaling (default: 70% target)
- Memory-based scaling (default: 80% target)
- Configurable min/max replicas
- Custom scaling behavior

**Configuration**:
```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

### 4. Configurable Values

**Key Configuration Areas**:

- **Image**: Repository, tag, pull policy
- **Replicas**: Replica count (when HPA disabled)
- **Service**: Type, port, nodePort
- **Ingress**: Enable/disable, hosts, TLS
- **Resources**: CPU and memory limits/requests
- **Environment**: Environment variables
- **Secrets**: Secret management
- **ConfigMap**: Configuration data
- **Security**: Security contexts, pod security
- **Affinity**: Pod affinity/anti-affinity
- **Tolerations**: Node tolerations

### 5. Security Features

**Pod Security Context**:
- Run as non-root user
- File system group
- Security constraints

**Container Security Context**:
- Drop all capabilities
- No privilege escalation
- Read-only root filesystem (optional)

**Network Policy**:
- Optional network policy
- Ingress/egress rules
- Namespace isolation

### 6. Additional Features

**Pod Disruption Budget**:
- Automatic PDB when HPA enabled
- Ensures minimum availability during disruptions

**Service Account**:
- Optional service account creation
- Custom annotations support

**Init Containers**:
- Optional init containers
- Example: Wait for database

**Extra Volumes**:
- Support for additional volumes
- ConfigMap volumes
- Secret volumes

## Installation

### Quick Start

```bash
# Install with default values
helm install ai-agent-connector ./helm/ai-agent-connector

# Install to specific namespace
helm install ai-agent-connector ./helm/ai-agent-connector \
  --namespace production \
  --create-namespace

# Install with production values
helm install ai-agent-connector ./helm/ai-agent-connector \
  -f helm/ai-agent-connector/values-production.yaml \
  --namespace production
```

### Custom Values

```bash
# Create custom values file
cat > my-values.yaml <<EOF
replicaCount: 3
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
ingress:
  enabled: true
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
EOF

# Install with custom values
helm install ai-agent-connector ./helm/ai-agent-connector \
  -f my-values.yaml
```

## Configuration Examples

### Production Deployment

```yaml
replicaCount: 3

image:
  repository: your-registry/ai-agent-connector
  tag: "1.0.0"
  pullPolicy: Always

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70

resources:
  limits:
    cpu: 4000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 1Gi

ingress:
  enabled: true
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: api-tls
      hosts:
        - api.example.com

affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
        - key: app.kubernetes.io/name
          operator: In
          values:
          - ai-agent-connector
      topologyKey: kubernetes.io/hostname
```

### Development Deployment

```yaml
replicaCount: 1

autoscaling:
  enabled: false

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 256Mi

ingress:
  enabled: false
```

## Health Checks

### Liveness Probe

Ensures container is running and restarts if unhealthy:

```yaml
livenessProbe:
  httpGet:
    path: /api/health
    port: 5000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Readiness Probe

Ensures container is ready to accept traffic:

```yaml
readinessProbe:
  httpGet:
    path: /api/health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Startup Probe

Gives container time to start before other probes:

```yaml
startupProbe:
  httpGet:
    path: /api/health
    port: 5000
  initialDelaySeconds: 0
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 30  # 5 minutes total
```

## Auto-Scaling

### Basic HPA

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

### Advanced HPA with Custom Behavior

```yaml
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 1
        periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 2
        periodSeconds: 15
      selectPolicy: Max
```

## Secrets Management

### Create Secrets Manually

```bash
kubectl create secret generic ai-agent-connector-secret \
  --from-literal=SECRET_KEY='your-secret-key' \
  --from-literal=ENCRYPTION_KEY='your-encryption-key' \
  --from-literal=OPENAI_API_KEY='your-openai-key' \
  --namespace production
```

### Use External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: ai-agent-connector-secret
spec:
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: ai-agent-connector-secret
    creationPolicy: Owner
  data:
  - secretKey: SECRET_KEY
    remoteRef:
      key: secret/ai-agent-connector
      property: SECRET_KEY
```

## Upgrading

```bash
# Upgrade with same values
helm upgrade ai-agent-connector ./helm/ai-agent-connector

# Upgrade with new values
helm upgrade ai-agent-connector ./helm/ai-agent-connector \
  -f new-values.yaml

# Check upgrade status
helm status ai-agent-connector

# View upgrade history
helm history ai-agent-connector

# Rollback if needed
helm rollback ai-agent-connector
```

## Monitoring

### Check Pod Status

```bash
kubectl get pods -l app.kubernetes.io/name=ai-agent-connector
```

### View Logs

```bash
kubectl logs -l app.kubernetes.io/name=ai-agent-connector --tail=100 -f
```

### Check HPA Status

```bash
kubectl get hpa ai-agent-connector
kubectl describe hpa ai-agent-connector
```

### Check Resource Usage

```bash
kubectl top pods -l app.kubernetes.io/name=ai-agent-connector
```

## Files Created

1. `helm/ai-agent-connector/Chart.yaml` - Chart metadata
2. `helm/ai-agent-connector/values.yaml` - Default values (400+ lines)
3. `helm/ai-agent-connector/values-production.yaml` - Production values
4. `helm/ai-agent-connector/values-development.yaml` - Development values
5. `helm/ai-agent-connector/templates/_helpers.tpl` - Template helpers
6. `helm/ai-agent-connector/templates/deployment.yaml` - Deployment (170+ lines)
7. `helm/ai-agent-connector/templates/service.yaml` - Service
8. `helm/ai-agent-connector/templates/hpa.yaml` - HorizontalPodAutoscaler
9. `helm/ai-agent-connector/templates/ingress.yaml` - Ingress
10. `helm/ai-agent-connector/templates/configmap.yaml` - ConfigMap
11. `helm/ai-agent-connector/templates/secret.yaml` - Secret
12. `helm/ai-agent-connector/templates/serviceaccount.yaml` - Service account
13. `helm/ai-agent-connector/templates/networkpolicy.yaml` - Network policy
14. `helm/ai-agent-connector/templates/pdb.yaml` - Pod disruption budget
15. `helm/ai-agent-connector/templates/NOTES.txt` - Post-install notes
16. `helm/ai-agent-connector/README.md` - Documentation (500+ lines)
17. `helm/ai-agent-connector/.helmignore` - Ignore patterns
18. `Dockerfile` - Container image definition
19. `HELM_CHART_FEATURE.md` - This document

## Docker Image

A `Dockerfile` is provided for building the container image:

```bash
# Build image
docker build -t ai-agent-connector:1.0.0 .

# Run locally
docker run -p 5000:5000 \
  -e SECRET_KEY=your-secret \
  -e ENCRYPTION_KEY=your-key \
  ai-agent-connector:1.0.0
```

## Production Checklist

- [ ] Create secrets (SECRET_KEY, ENCRYPTION_KEY, API keys)
- [ ] Configure image repository and tag
- [ ] Set appropriate resource limits
- [ ] Enable auto-scaling with proper min/max
- [ ] Configure ingress with TLS
- [ ] Set up pod anti-affinity
- [ ] Enable network policies
- [ ] Configure monitoring (Prometheus)
- [ ] Set up backup for persistent data
- [ ] Configure pod disruption budget
- [ ] Test health checks
- [ ] Verify auto-scaling behavior
- [ ] Load test the deployment

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -l app.kubernetes.io/name=ai-agent-connector

# Describe pod for events
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>
```

### Health Checks Failing

```bash
# Port forward to test health endpoint
kubectl port-forward svc/ai-agent-connector 5000:5000
curl http://localhost:5000/api/health

# Check probe configuration
kubectl get deployment ai-agent-connector -o yaml | grep -A 10 probe
```

### Auto-Scaling Not Working

```bash
# Check HPA status
kubectl get hpa ai-agent-connector
kubectl describe hpa ai-agent-connector

# Verify metrics server
kubectl top nodes
kubectl top pods

# Check HPA events
kubectl get events --field-selector involvedObject.name=ai-agent-connector
```

## Best Practices

1. **Use Production Values**: Use `values-production.yaml` for production
2. **External Secrets**: Use external-secrets operator or sealed-secrets
3. **Resource Limits**: Always set appropriate resource limits
4. **Pod Anti-Affinity**: Distribute pods across nodes
5. **Health Checks**: Configure all three probe types
6. **Auto-Scaling**: Enable HPA with appropriate targets
7. **Monitoring**: Set up Prometheus metrics
8. **Backup**: Backup persistent data regularly
9. **Network Policies**: Restrict network access
10. **Security**: Run as non-root, drop capabilities

## Conclusion

The Helm chart provides:

- ✅ **Configurable values** for all deployment aspects
- ✅ **Health checks** (liveness, readiness, startup probes)
- ✅ **Auto-scaling** with HPA (CPU and memory)
- ✅ **Production-ready** configuration
- ✅ **Security** best practices
- ✅ **Comprehensive documentation**

The Helm chart enables DevOps teams to deploy AI Agent Connector to Kubernetes with confidence!
