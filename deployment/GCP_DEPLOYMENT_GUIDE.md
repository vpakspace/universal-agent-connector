# GCP Deployment Guide

Complete guide for deploying AI Agent Connector to Google Cloud Platform using Terraform.

## Prerequisites

- GCP Project with billing enabled
- gcloud CLI installed and configured
- Terraform >= 1.0
- kubectl installed
- Helm 3.0+ installed
- Docker installed

## Step 1: Set Up GCP Project

### Enable Required APIs

```bash
gcloud services enable \
  compute.googleapis.com \
  container.googleapis.com \
  containerregistry.googleapis.com \
  iam.googleapis.com \
  --project=YOUR_PROJECT_ID
```

### Set Project

```bash
gcloud config set project YOUR_PROJECT_ID
```

## Step 2: Configure Terraform

### Step 1: Copy Variables File

```bash
cd terraform/gcp
cp terraform.tfvars.example terraform.tfvars
```

### Step 2: Edit Variables

Edit `terraform.tfvars`:

```hcl
gcp_project_id = "your-gcp-project-id"
gcp_region = "us-central1"
project_name = "ai-agent-connector"
subnet_cidr = "10.0.0.0/16"
node_count = 2
node_min_count = 1
node_max_count = 10
node_machine_type = "e2-medium"
```

## Step 3: Initialize Terraform

```bash
terraform init
```

## Step 4: Review Plan

```bash
terraform plan
```

## Step 5: Apply Infrastructure

```bash
terraform apply
```

This creates:
- VPC network
- GKE cluster
- Node pool
- Artifact Registry repository
- Deploys Helm chart

## Step 6: Configure kubectl

```bash
gcloud container clusters get-credentials ai-agent-connector-cluster \
  --region us-central1 \
  --project YOUR_PROJECT_ID
```

Or use the output command:

```bash
terraform output -raw configure_kubectl | bash
```

## Step 7: Verify Deployment

```bash
# Check pods
kubectl get pods -n production

# Check services
kubectl get svc -n production

# Check HPA
kubectl get hpa -n production
```

## Building and Pushing Docker Image

### Step 1: Configure Docker for Artifact Registry

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Step 2: Build and Push Image

```bash
# Get repository URL
REPO_URL=$(terraform output -raw artifact_registry_url)

# Build image
docker build -t ai-agent-connector:latest .

# Tag image
docker tag ai-agent-connector:latest $REPO_URL/ai-agent-connector:latest

# Push image
docker push $REPO_URL/ai-agent-connector:latest
```

## Creating Secrets

### Step 1: Generate Encryption Key

```bash
ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

### Step 2: Create Kubernetes Secret

```bash
kubectl create secret generic ai-agent-connector-secret \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=ENCRYPTION_KEY="$ENCRYPTION_KEY" \
  --from-literal=OPENAI_API_KEY="your-openai-key" \
  --namespace production
```

## Accessing the Application

### Option 1: LoadBalancer Service

```bash
# Get LoadBalancer IP
kubectl get svc -n production ai-agent-connector -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

### Option 2: Port Forward

```bash
kubectl port-forward -n production svc/ai-agent-connector 5000:5000
```

Access: `http://localhost:5000`

### Option 3: Ingress

Configure DNS to point to the ingress controller's LoadBalancer IP.

## Monitoring

### View Logs

```bash
kubectl logs -n production -l app.kubernetes.io/name=ai-agent-connector --tail=100 -f
```

### Check Resource Usage

```bash
kubectl top pods -n production
kubectl top nodes
```

### GCP Console

- GKE: https://console.cloud.google.com/kubernetes
- Artifact Registry: https://console.cloud.google.com/artifacts
- Logs: https://console.cloud.google.com/logs

## Updating Deployment

### Update Helm Chart

```bash
helm upgrade ai-agent-connector ../../helm/ai-agent-connector \
  --namespace production \
  --set image.tag=new-tag
```

### Update Infrastructure

```bash
terraform plan
terraform apply
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n production

# Describe pod
kubectl describe pod <pod-name> -n production

# Check events
kubectl get events -n production --sort-by='.lastTimestamp'
```

### Image Pull Errors

```bash
# Verify Artifact Registry access
gcloud artifacts repositories list

# Check image exists
gcloud artifacts docker images list us-central1-docker.pkg.dev/YOUR_PROJECT_ID/ai-agent-connector
```

### Network Issues

```bash
# Check VPC
gcloud compute networks list

# Check firewall rules
gcloud compute firewall-rules list
```

## Cleanup

```bash
terraform destroy
```

## Cost Optimization

1. **Preemptible Nodes**: Use preemptible nodes for non-production
2. **Right-size Nodes**: Adjust node machine types
3. **Auto-scaling**: Configure appropriate min/max counts
4. **Commitments**: Use committed use discounts for predictable workloads

## Security Best Practices

1. **Private Clusters**: Enable private GKE clusters
2. **Workload Identity**: Use Workload Identity for service accounts
3. **Network Policies**: Implement Kubernetes network policies
4. **Secrets Management**: Use Google Secret Manager
5. **Binary Authorization**: Enable Binary Authorization for production

## Next Steps

- Set up CI/CD with Cloud Build
- Configure monitoring with Cloud Monitoring
- Set up backup and disaster recovery
- Implement security scanning
- Configure autoscaling policies
