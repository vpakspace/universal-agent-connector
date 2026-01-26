image:
  repository: ${image_repository}
  tag: ${image_tag}
  pullPolicy: Always

replicaCount: ${replica_count}

service:
  type: LoadBalancer
  port: 5000

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: ai-agent-connector.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: ai-agent-connector-tls
      hosts:
        - ai-agent-connector.example.com

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 512Mi

env:
  FLASK_ENV: production
  PORT: "5000"
  HOST: "0.0.0.0"
  AWS_REGION: ${aws_region}

configMap:
  enabled: true
  data:
    LOG_LEVEL: "INFO"

secrets:
  enabled: true
