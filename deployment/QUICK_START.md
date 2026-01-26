# One-Click Cloud Deployment - Quick Start Guide

Deploy AI Agent Connector to AWS, GCP, or Azure with a single command.

## 🚀 Quick Start (5 Minutes)

### Prerequisites

Install these tools first:

```bash
# Required tools
- Terraform >= 1.0
- kubectl
- Helm 3.0+
- Docker

# Cloud-specific CLIs
- AWS: AWS CLI
- GCP: gcloud CLI
- Azure: Azure CLI
```

### One-Click Deployment

#### Option 1: Using Deployment Scripts (Recommended)

**Linux/Mac:**
```bash
cd deployment
chmod +x deploy.sh
./deploy.sh aws    # or gcp, azure
```

**Windows:**
```powershell
cd deployment
.\deploy.ps1 -Provider aws    # or gcp, azure
```

#### Option 2: Using Terraform Directly

**AWS:**
```bash
cd terraform/aws
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform apply
```

**GCP:**
```bash
cd terraform/gcp
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform apply
```

**Azure:**
```bash
cd terraform/azure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform apply
```

#### Option 3: Using CloudFormation (AWS Only)

```bash
aws cloudformation create-stack \
  --stack-name ai-agent-connector \
  --template-body file://cloudformation/aws/eks-stack.yaml \
  --parameters ParameterKey=ProjectName,ParameterValue=ai-agent-connector \
               ParameterKey=AvailabilityZones,ParameterValue=us-east-1a,us-east-1b \
  --capabilities CAPABILITY_IAM
```

## 📋 Pre-Deployment Checklist

### AWS
- [ ] AWS CLI configured (`aws configure`)
- [ ] AWS account with permissions for EKS, ECR, VPC, IAM
- [ ] At least 2 availability zones in your region

### GCP
- [ ] gcloud CLI installed and authenticated (`gcloud auth login`)
- [ ] GCP project created with billing enabled
- [ ] Required APIs enabled (script handles this automatically)

### Azure
- [ ] Azure CLI installed and logged in (`az login`)
- [ ] Azure subscription selected (`az account set --subscription <id>`)
- [ ] Resource group permissions

## 🎯 What Gets Deployed

Each deployment creates:

### Infrastructure
- ✅ **VPC/Network**: Virtual network with public/private subnets
- ✅ **Kubernetes Cluster**: Managed K8s (EKS/GKE/AKS)
- ✅ **Node Pools**: Auto-scaling worker nodes
- ✅ **Container Registry**: ECR/Artifact Registry/ACR
- ✅ **Load Balancer**: For external access
- ✅ **Security Groups/NSGs**: Network security rules

### Application
- ✅ **Helm Chart**: AI Agent Connector application
- ✅ **ConfigMaps**: Application configuration
- ✅ **Secrets**: Secure credential storage (you'll need to create these)
- ✅ **HPA**: Horizontal Pod Autoscaler
- ✅ **Ingress**: Optional ingress controller

## ⚙️ Configuration

### Minimal Configuration

Each provider has a `terraform.tfvars.example` file. Copy and edit:

**AWS (`terraform/aws/terraform.tfvars`):**
```hcl
aws_region = "us-east-1"
project_name = "ai-agent-connector"
```

**GCP (`terraform/gcp/terraform.tfvars`):**
```hcl
gcp_project_id = "your-project-id"
gcp_region = "us-central1"
```

**Azure (`terraform/azure/terraform.tfvars`):**
```hcl
azure_region = "eastus"
project_name = "ai-agent-connector"
```

### Advanced Configuration

See provider-specific guides for advanced options:
- [AWS Deployment Guide](AWS_DEPLOYMENT_GUIDE.md)
- [GCP Deployment Guide](GCP_DEPLOYMENT_GUIDE.md)
- [Azure Deployment Guide](AZURE_DEPLOYMENT_GUIDE.md)

## 🔐 Post-Deployment Setup

### 1. Configure kubectl

The deployment outputs the command to configure kubectl:

```bash
# AWS
aws eks update-kubeconfig --region <region> --name <cluster-name>

# GCP
gcloud container clusters get-credentials <cluster-name> --region <region> --project <project-id>

# Azure
az aks get-credentials --resource-group <rg-name> --name <cluster-name>
```

### 2. Create Application Secrets

```bash
kubectl create secret generic ai-agent-connector-secret \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
  --from-literal=OPENAI_API_KEY="your-key-here" \
  --namespace production
```

### 3. Verify Deployment

```bash
# Check pods
kubectl get pods -n production

# Check services
kubectl get svc -n production

# View logs
kubectl logs -n production -l app.kubernetes.io/name=ai-agent-connector
```

### 4. Access Application

**Port Forward:**
```bash
kubectl port-forward -n production svc/ai-agent-connector 5000:5000
# Access at http://localhost:5000
```

**LoadBalancer:**
```bash
# Get LoadBalancer IP/URL
kubectl get svc -n production ai-agent-connector
# Access via the EXTERNAL-IP
```

## 🧹 Cleanup

### Terraform
```bash
cd terraform/<provider>
terraform destroy
```

### CloudFormation (AWS)
```bash
aws cloudformation delete-stack --stack-name ai-agent-connector
```

## 💰 Cost Estimation

Approximate monthly costs (varies by region and usage):

- **AWS**: $150-300/month (EKS + EC2 nodes + NAT gateways)
- **GCP**: $150-300/month (GKE + Compute Engine)
- **Azure**: $150-300/month (AKS + VM nodes)

**Cost Optimization Tips:**
- Use smaller instance types for development
- Use preemptible/spot instances (GCP/AWS)
- Scale down nodes during off-hours
- Use single availability zone for dev/test

## 🔧 Troubleshooting

### Common Issues

**Terraform fails to initialize:**
- Check cloud provider CLI is configured
- Verify credentials have necessary permissions

**kubectl connection fails:**
- Ensure cluster is fully provisioned (can take 10-15 minutes)
- Verify kubectl is configured correctly

**Pods not starting:**
- Check pod logs: `kubectl logs <pod-name> -n production`
- Verify secrets are created
- Check resource quotas: `kubectl describe quota -n production`

**Image pull errors:**
- Verify Docker image is pushed to registry
- Check registry authentication
- Verify image tag matches deployment

### Get Help

1. Check provider-specific deployment guides
2. Review Terraform/CloudFormation logs
3. Check Kubernetes events: `kubectl get events -n production --sort-by='.lastTimestamp'`

## 📚 Next Steps

- [Configure application settings](../helm/ai-agent-connector/values.yaml)
- [Set up monitoring and logging](../helm/ai-agent-connector/README.md)
- [Configure ingress for external access](../helm/ai-agent-connector/README.md#ingress)
- [Review security best practices](README.md#security-considerations)

## 🎓 Learn More

- [Full Deployment Guide](README.md)
- [AWS Deployment Guide](AWS_DEPLOYMENT_GUIDE.md)
- [GCP Deployment Guide](GCP_DEPLOYMENT_GUIDE.md)
- [Azure Deployment Guide](AZURE_DEPLOYMENT_GUIDE.md)
- [Helm Chart Documentation](../helm/ai-agent-connector/README.md)

