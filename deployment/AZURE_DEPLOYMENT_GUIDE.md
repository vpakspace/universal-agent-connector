# Azure Deployment Guide

Complete guide for deploying AI Agent Connector to Microsoft Azure using Terraform.

## Prerequisites

- Azure Subscription
- Azure CLI installed and configured
- Terraform >= 1.0
- kubectl installed
- Helm 3.0+ installed
- Docker installed

## Step 1: Set Up Azure

### Login to Azure

```bash
az login
```

### Set Subscription

```bash
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

### Create Resource Group (Optional)

```bash
az group create --name ai-agent-connector-rg --location eastus
```

## Step 2: Configure Terraform

### Step 1: Copy Variables File

```bash
cd terraform/azure
cp terraform.tfvars.example terraform.tfvars
```

### Step 2: Edit Variables

Edit `terraform.tfvars`:

```hcl
azure_region = "eastus"
project_name = "ai-agent-connector"
vnet_address_space = "10.0.0.0/16"
subnet_address_prefix = "10.0.1.0/24"
node_count = 2
node_min_count = 1
node_max_count = 10
node_vm_size = "Standard_D2s_v3"
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
- Resource group
- Virtual network and subnet
- AKS cluster
- Azure Container Registry (ACR)
- Deploys Helm chart

## Step 6: Configure kubectl

```bash
az aks get-credentials \
  --resource-group ai-agent-connector-rg \
  --name ai-agent-connector-aks
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

### Step 1: Login to ACR

```bash
# Get ACR login server
ACR_NAME=$(terraform output -raw acr_login_server | cut -d'.' -f1)

# Login
az acr login --name $ACR_NAME
```

### Step 2: Build and Push Image

```bash
# Get ACR login server
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)

# Build image
docker build -t ai-agent-connector:latest .

# Tag image
docker tag ai-agent-connector:latest $ACR_LOGIN_SERVER/ai-agent-connector:latest

# Push image
docker push $ACR_LOGIN_SERVER/ai-agent-connector:latest
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

### Azure Portal

- AKS: https://portal.azure.com/#view/Microsoft_Azure_ContainerService/AksArmorDashboard
- ACR: https://portal.azure.com/#view/Microsoft_Azure_ContainerRegistries
- Logs: Azure Monitor in portal

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
# Verify ACR access
az acr repository list --name $ACR_NAME

# Check image exists
az acr repository show-tags --name $ACR_NAME --repository ai-agent-connector
```

### Network Issues

```bash
# Check VNet
az network vnet list --resource-group ai-agent-connector-rg

# Check network security groups
az network nsg list --resource-group ai-agent-connector-rg
```

## Cleanup

```bash
terraform destroy
```

## Cost Optimization

1. **Spot Instances**: Use spot node pools for non-production
2. **Right-size VMs**: Adjust VM sizes based on workload
3. **Auto-scaling**: Configure appropriate min/max counts
4. **Reserved Instances**: Consider reserved instances for predictable workloads

## Security Best Practices

1. **Private Clusters**: Enable private AKS clusters
2. **Managed Identity**: Use managed identities for service accounts
3. **Network Policies**: Implement Kubernetes network policies
4. **Secrets Management**: Use Azure Key Vault
5. **Container Security**: Enable Azure Defender for containers

## Next Steps

- Set up CI/CD with Azure DevOps
- Configure monitoring with Azure Monitor
- Set up backup and disaster recovery
- Implement security scanning
- Configure autoscaling policies
