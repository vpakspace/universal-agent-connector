# Cloud Deployment Templates

One-click deployment templates for AWS, GCP, and Azure to deploy AI Agent Connector.

## 🚀 Quick Start

**New to cloud deployment?** Start here: [Quick Start Guide](QUICK_START.md)

## Quick Start

### AWS

**Using Terraform:**
```bash
cd terraform/aws
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

**Using CloudFormation:**
```bash
aws cloudformation create-stack \
  --stack-name ai-agent-connector-stack \
  --template-body file://cloudformation/aws/eks-stack.yaml \
  --capabilities CAPABILITY_IAM
```

**Using Deployment Script:**
```bash
./deploy.sh aws
# or on Windows
.\deploy.ps1 -Provider aws
```

### GCP

```bash
cd terraform/gcp
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

**Using Deployment Script:**
```bash
./deploy.sh gcp
# or on Windows
.\deploy.ps1 -Provider gcp
```

### Azure

```bash
cd terraform/azure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

**Using Deployment Script:**
```bash
./deploy.sh azure
# or on Windows
.\deploy.ps1 -Provider azure
```

## Detailed Guides

- [AWS Deployment Guide](AWS_DEPLOYMENT_GUIDE.md)
- [GCP Deployment Guide](GCP_DEPLOYMENT_GUIDE.md)
- [Azure Deployment Guide](AZURE_DEPLOYMENT_GUIDE.md)

## What Gets Deployed

Each deployment creates:

### Infrastructure
- **VPC/Network**: Virtual network with public and private subnets
- **Kubernetes Cluster**: Managed Kubernetes service (EKS/GKE/AKS)
- **Node Pools**: Auto-scaling worker nodes
- **Container Registry**: ECR/Artifact Registry/ACR for Docker images
- **Load Balancer**: For external access
- **Security Groups/NSGs**: Network security rules

### Application
- **Helm Chart**: Deploys the AI Agent Connector application
- **ConfigMaps**: Application configuration
- **Secrets**: Secure credential storage
- **HPA**: Horizontal Pod Autoscaler
- **Ingress**: Optional ingress controller

## Prerequisites

### Common
- Terraform >= 1.0
- kubectl
- Helm 3.0+
- Docker

### AWS Specific
- AWS CLI configured
- AWS account with appropriate permissions

### GCP Specific
- gcloud CLI installed and configured
- GCP project with billing enabled

### Azure Specific
- Azure CLI installed and configured
- Azure subscription

## Configuration

### Terraform Variables

Each provider has a `terraform.tfvars.example` file. Copy it to `terraform.tfvars` and customize:

**AWS (`terraform/aws/terraform.tfvars`):**
```hcl
aws_region = "us-east-1"
project_name = "ai-agent-connector"
vpc_cidr = "10.0.0.0/16"
node_instance_types = ["t3.medium"]
node_desired_size = 2
```

**GCP (`terraform/gcp/terraform.tfvars`):**
```hcl
gcp_project_id = "your-project-id"
gcp_region = "us-central1"
node_machine_type = "e2-medium"
node_count = 2
```

**Azure (`terraform/azure/terraform.tfvars`):**
```hcl
azure_region = "eastus"
node_vm_size = "Standard_D2s_v3"
node_count = 2
```

## Deployment Scripts

### Bash Script (`deploy.sh`)

Automates the entire deployment process:

```bash
chmod +x deploy.sh
./deploy.sh aws
./deploy.sh gcp
./deploy.sh azure
```

The script:
1. Checks prerequisites
2. Initializes Terraform
3. Plans and applies infrastructure
4. Configures kubectl
5. Builds and pushes Docker image
6. Deploys Helm chart

### PowerShell Script (`deploy.ps1`)

Windows equivalent:

```powershell
.\deploy.ps1 -Provider aws
.\deploy.ps1 -Provider gcp
.\deploy.ps1 -Provider azure
```

## Post-Deployment

### Create Secrets

After deployment, create Kubernetes secrets:

```bash
kubectl create secret generic ai-agent-connector-secret \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
  --from-literal=OPENAI_API_KEY="your-key" \
  --namespace production
```

### Access Application

**Port Forward:**
```bash
kubectl port-forward -n production svc/ai-agent-connector 5000:5000
```

**LoadBalancer:**
```bash
# Get LoadBalancer IP/URL
kubectl get svc -n production ai-agent-connector
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n production

# Check services
kubectl get svc -n production

# Check HPA
kubectl get hpa -n production

# View logs
kubectl logs -n production -l app.kubernetes.io/name=ai-agent-connector
```

## Updating

### Update Application

```bash
# Build new image
docker build -t ai-agent-connector:new-tag .

# Push to registry
# (Use the appropriate command for your provider)

# Update Helm release
helm upgrade ai-agent-connector ../../helm/ai-agent-connector \
  --namespace production \
  --set image.tag=new-tag
```

### Update Infrastructure

```bash
# Modify terraform.tfvars or variables
terraform plan
terraform apply
```

## Cleanup

### Destroy Infrastructure

```bash
terraform destroy
```

**Warning:** This will delete all resources created by Terraform.

### CloudFormation (AWS)

```bash
aws cloudformation delete-stack \
  --stack-name ai-agent-connector-stack
```

## Cost Estimation

Approximate monthly costs (varies by region and usage):

- **AWS**: $150-300/month (EKS + EC2 nodes)
- **GCP**: $150-300/month (GKE + Compute Engine)
- **Azure**: $150-300/month (AKS + VM nodes)

Costs depend on:
- Node instance types
- Number of nodes
- Data transfer
- Storage

## Security Considerations

1. **Secrets Management**: Use cloud-native secret managers (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault)
2. **Network Policies**: Implement Kubernetes network policies
3. **Private Clusters**: Use private clusters for production
4. **IAM/RBAC**: Follow least privilege principle
5. **Image Scanning**: Enable container image scanning
6. **Encryption**: Enable encryption at rest and in transit

## Troubleshooting

See provider-specific deployment guides for troubleshooting:
- [AWS Troubleshooting](AWS_DEPLOYMENT_GUIDE.md#troubleshooting)
- [GCP Troubleshooting](GCP_DEPLOYMENT_GUIDE.md#troubleshooting)
- [Azure Troubleshooting](AZURE_DEPLOYMENT_GUIDE.md#troubleshooting)

## Support

For issues or questions:
1. Check the provider-specific deployment guides
2. Review Terraform/CloudFormation logs
3. Check Kubernetes events: `kubectl get events -n production`
