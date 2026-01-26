# AI Agent Connector Helm Chart

Helm chart for deploying AI Agent Connector to Kubernetes with configurable values, health checks, and auto-scaling.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- kubectl configured to access your cluster

## Installation

### Quick Start

```bash
# Add the chart (if using a chart repository)
helm repo add ai-agent-connector https://charts.example.com
helm repo update

# Install with default values
helm install ai-agent-connector ./helm/ai-agent-connector

# Install with custom values
helm install ai-agent-connector ./helm/ai-agent-connector -f my-values.yaml

# Install to specific namespace
helm install ai-agent-connector ./helm/ai-agent-connector --namespace production --create-namespace
```

### Custom Values

Create a `my-values.yaml` file:

```yaml
replicaCount: 3

image:
  repository: your-registry/ai-agent-connector
  tag: "1.0.0"

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
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

secrets:
  enabled: true
  SECRET_KEY: "base64-encoded-secret-key"
  ENCRYPTION_KEY: "base64-encoded-encryption-key"
  OPENAI_API_KEY: "base64-encoded-openai-key"
```

Install with custom values:

```bash
helm install ai-agent-connector ./helm/ai-agent-connector -f my-values.yaml
```

## Configuration

### Required Configuration

#### Secrets

Create secrets before deployment:

```bash
# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Create secret manually
kubectl create secret generic ai-agent-connector-secret \
  --from-literal=SECRET_KEY='your-secret-key' \
  --from-literal=ENCRYPTION_KEY='your-encryption-key' \
  --from-literal=OPENAI_API_KEY='your-openai-key' \
  --namespace production
```

Or use external-secrets operator or sealed-secrets.

### Configuration Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `2` |
| `image.repository` | Container image repository | `ai-agent-connector` |
| `image.tag` | Container image tag | `1.0.0` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `5000` |
| `ingress.enabled` | Enable ingress | `false` |
| `autoscaling.enabled` | Enable auto-scaling | `true` |
| `autoscaling.minReplicas` | Minimum replicas | `2` |
| `autoscaling.maxReplicas` | Maximum replicas | `10` |
| `autoscaling.targetCPUUtilizationPercentage` | Target CPU utilization | `70` |
| `autoscaling.targetMemoryUtilizationPercentage` | Target memory utilization | `80` |
| `resources.limits.cpu` | CPU limit | `2000m` |
| `resources.limits.memory` | Memory limit | `2Gi` |
| `resources.requests.cpu` | CPU request | `500m` |
| `resources.requests.memory` | Memory request | `512Mi` |
| `healthCheck.livenessProbe.enabled` | Enable liveness probe | `true` |
| `healthCheck.readinessProbe.enabled` | Enable readiness probe | `true` |
| `healthCheck.startupProbe.enabled` | Enable startup probe | `true` |

## Health Checks

The chart includes three types of health checks:

### Liveness Probe

Detects if the container is running. If it fails, Kubernetes restarts the container.

- **Path**: `/api/health`
- **Initial Delay**: 30 seconds
- **Period**: 10 seconds
- **Timeout**: 5 seconds
- **Failure Threshold**: 3

### Readiness Probe

Detects if the container is ready to accept traffic. If it fails, the pod is removed from service endpoints.

- **Path**: `/api/health`
- **Initial Delay**: 10 seconds
- **Period**: 5 seconds
- **Timeout**: 3 seconds
- **Failure Threshold**: 3

### Startup Probe

Gives the container time to start before liveness and readiness probes begin.

- **Path**: `/api/health`
- **Initial Delay**: 0 seconds
- **Period**: 10 seconds
- **Timeout**: 3 seconds
- **Failure Threshold**: 30 (5 minutes total)

## Auto-Scaling

HorizontalPodAutoscaler (HPA) is enabled by default:

- **Min Replicas**: 2
- **Max Replicas**: 10
- **CPU Target**: 70%
- **Memory Target**: 80%

### Custom Scaling Behavior

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 20
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

## Ingress

### Basic Ingress

```yaml
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
```

### Ingress with TLS

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: api-tls
      hosts:
        - api.example.com
```

## Resource Management

### Resource Limits and Requests

```yaml
resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 512Mi
```

### Node Selector

```yaml
nodeSelector:
  node-type: compute
```

### Affinity Rules

```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - ai-agent-connector
        topologyKey: kubernetes.io/hostname
```

## Environment Variables

### Via ConfigMap

```yaml
configMap:
  enabled: true
  data:
    LOG_LEVEL: "INFO"
    MAX_CONNECTIONS: "100"
```

### Via Values

```yaml
env:
  FLASK_ENV: production
  PORT: "5000"
  HOST: "0.0.0.0"
  DATABASE_URL: "postgresql://user:pass@db:5432/dbname"
```

### Via Secrets

```yaml
secrets:
  enabled: true
  SECRET_KEY: "base64-encoded-value"
  ENCRYPTION_KEY: "base64-encoded-value"
  OPENAI_API_KEY: "base64-encoded-value"
```

## Upgrading

```bash
# Upgrade with same values
helm upgrade ai-agent-connector ./helm/ai-agent-connector

# Upgrade with new values
helm upgrade ai-agent-connector ./helm/ai-agent-connector -f new-values.yaml

# Check upgrade status
helm status ai-agent-connector
```

## Uninstalling

```bash
helm uninstall ai-agent-connector

# Remove namespace (if created)
kubectl delete namespace production
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -l app.kubernetes.io/name=ai-agent-connector
```

### View Logs

```bash
kubectl logs -l app.kubernetes.io/name=ai-agent-connector --tail=100
```

### Check Events

```bash
kubectl get events --sort-by='.lastTimestamp'
```

### Port Forward for Testing

```bash
kubectl port-forward svc/ai-agent-connector 5000:5000
```

### Check HPA Status

```bash
kubectl get hpa ai-agent-connector
kubectl describe hpa ai-agent-connector
```

### Common Issues

1. **Pods not starting**: Check secrets are created
2. **Health checks failing**: Verify `/api/health` endpoint is accessible
3. **Auto-scaling not working**: Check HPA resource and metrics server
4. **Image pull errors**: Verify image repository and pull secrets

## Production Recommendations

1. **Use external secret management**: External Secrets Operator or Sealed Secrets
2. **Enable resource limits**: Set appropriate CPU and memory limits
3. **Configure pod anti-affinity**: Distribute pods across nodes
4. **Use persistent volumes**: If storing data locally
5. **Enable monitoring**: Prometheus metrics and Grafana dashboards
6. **Set up backup**: For persistent data
7. **Use TLS**: Enable TLS for ingress
8. **Configure network policies**: Restrict network access
9. **Set resource quotas**: Limit namespace resources
10. **Enable pod disruption budgets**: For high availability

## Examples

### Development

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
```

### Production

```yaml
replicaCount: 3
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
resources:
  limits:
    cpu: 4000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 1Gi
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
        - key: app
          operator: In
          values:
          - ai-agent-connector
      topologyKey: kubernetes.io/hostname
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/universal-agent-connector/issues
- Documentation: https://docs.example.com
