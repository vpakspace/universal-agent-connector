# Cloud Deployment Templates Feature

## Overview

One-click deployment templates for AWS, GCP, and Azure to automate the setup of AI Agent Connector infrastructure and application deployment.

## Acceptance Criteria

✅ **Terraform/CloudFormation templates**
- Terraform templates for AWS, GCP, and Azure
- CloudFormation template for AWS
- Configurable variables for all providers
- Infrastructure-as-Code best practices

✅ **Deployment guides**
- Comprehensive guides for each cloud provider
- Step-by-step instructions
- Troubleshooting sections
- Security best practices

## Implementation

### Terraform Templates

#### AWS (`terraform/aws/`)

**Files:**
- `main.tf`: Main infrastructure definition
  - VPC with public/private subnets
  - EKS cluster
  - EKS node group
  - ECR repository
  - IAM roles and policies
  - Helm chart deployment
- `variables.tf`: Input variables
- `outputs.tf`: Output values
- `helm-values.yaml.tpl`: Helm values template
- `terraform.tfvars.example`: Example configuration

**Features:**
- Multi-AZ deployment
- NAT gateways for private subnets
- EKS cluster with managed node groups
- ECR for container images
- Automatic Helm chart deployment

#### GCP (`terraform/gcp/`)

**Files:**
- `main.tf`: Main infrastructure definition
  - VPC network
  - GKE cluster
  - Node pool
  - Artifact Registry repository
  - Helm chart deployment
- `variables.tf`: Input variables
- `helm-values.yaml.tpl`: Helm values template
- `terraform.tfvars.example`: Example configuration

**Features:**
- Private GKE cluster
- Workload Identity
- Cluster autoscaling
- Vertical Pod Autoscaling
- Artifact Registry for images

#### Azure (`terraform/azure/`)

**Files:**
- `main.tf`: Main infrastructure definition
  - Resource group
  - Virtual network and subnet
  - AKS cluster
  - Azure Container Registry
  - Log Analytics workspace
  - Helm chart deployment
- `variables.tf`: Input variables
- `helm-values.yaml.tpl`: Helm values template
- `terraform.tfvars.example`: Example configuration

**Features:**
- AKS cluster with managed identity
- Azure Container Registry
- Network security groups
- Log Analytics integration
- Auto-scaling node pools

### CloudFormation Template

#### AWS (`cloudformation/aws/eks-stack.yaml`)

**Resources:**
- VPC with public/private subnets
- Internet Gateway and NAT Gateways
- Route tables
- EKS cluster
- EKS node group
- ECR repository
- IAM roles and policies

**Features:**
- Parameterized configuration
- Outputs for cluster information
- IAM capabilities handling

### Deployment Guides

#### AWS Deployment Guide (`deployment/AWS_DEPLOYMENT_GUIDE.md`)

**Sections:**
- Prerequisites
- Terraform deployment steps
- CloudFormation deployment steps
- Building and pushing Docker images
- Creating secrets
- Accessing the application
- Monitoring
- Updating deployment
- Troubleshooting
- Cleanup
- Cost optimization
- Security best practices

#### GCP Deployment Guide (`deployment/GCP_DEPLOYMENT_GUIDE.md`)

**Sections:**
- Prerequisites
- GCP project setup
- Terraform deployment steps
- Building and pushing Docker images
- Creating secrets
- Accessing the application
- Monitoring
- Updating deployment
- Troubleshooting
- Cleanup
- Cost optimization
- Security best practices

#### Azure Deployment Guide (`deployment/AZURE_DEPLOYMENT_GUIDE.md`)

**Sections:**
- Prerequisites
- Azure setup
- Terraform deployment steps
- Building and pushing Docker images
- Creating secrets
- Accessing the application
- Monitoring
- Updating deployment
- Troubleshooting
- Cleanup
- Cost optimization
- Security best practices

### Deployment Scripts

#### Bash Script (`deployment/deploy.sh`)

**Features:**
- Prerequisites checking
- Provider-specific deployment functions
- Automatic Terraform initialization
- kubectl configuration
- Docker image build and push
- Colored output for better UX

**Usage:**
```bash
./deploy.sh aws
./deploy.sh gcp
./deploy.sh azure
```

#### PowerShell Script (`deployment/deploy.ps1`)

**Features:**
- Windows-compatible deployment script
- Same functionality as Bash script
- Parameter validation
- Error handling

**Usage:**
```powershell
.\deploy.ps1 -Provider aws
.\deploy.ps1 -Provider gcp
.\deploy.ps1 -Provider azure
```

## Infrastructure Components

### Network

**AWS:**
- VPC with public and private subnets
- Internet Gateway
- NAT Gateways (one per AZ)
- Route tables

**GCP:**
- VPC network
- Subnet with private Google access
- Firewall rules (implicit)

**Azure:**
- Virtual network
- Subnet
- Network security group

### Kubernetes Clusters

**AWS (EKS):**
- Managed Kubernetes service
- Node groups with auto-scaling
- IAM roles for service accounts support

**GCP (GKE):**
- Private cluster
- Workload Identity
- Cluster autoscaling
- Vertical Pod Autoscaling

**Azure (AKS):**
- Managed Kubernetes service
- System-assigned managed identity
- Auto-scaling node pools
- Log Analytics integration

### Container Registries

**AWS:**
- Amazon ECR
- Image scanning enabled

**GCP:**
- Artifact Registry
- Docker format repository

**Azure:**
- Azure Container Registry (ACR)
- Basic SKU
- Role-based access control

### Application Deployment

All providers deploy the Helm chart with:
- Configurable replica count
- Auto-scaling (HPA)
- Resource limits and requests
- Environment variables
- ConfigMaps and Secrets
- Ingress configuration (optional)

## Configuration

### Terraform Variables

Each provider supports extensive configuration:

**Common:**
- Project name
- Region
- Kubernetes version
- Node configuration (count, size, auto-scaling)
- Image tag
- Replica count

**Provider-specific:**
- AWS: VPC CIDR, availability zones, instance types
- GCP: Project ID, machine types, preemptible nodes
- Azure: Resource group, VM sizes, disk sizes

### Helm Values

Templated Helm values files for each provider:
- Image repository and tag
- Replica count
- Service configuration
- Ingress configuration
- Auto-scaling settings
- Resource limits
- Environment variables
- ConfigMap and Secret configuration

## Security Features

1. **Network Security:**
   - Private subnets for nodes
   - Security groups/NSGs
   - Network policies support

2. **Identity and Access:**
   - IAM roles (AWS)
   - Workload Identity (GCP)
   - Managed Identity (Azure)

3. **Secrets Management:**
   - Kubernetes secrets
   - Integration with cloud secret managers

4. **Container Security:**
   - Image scanning (ECR)
   - Private registries
   - Non-root containers

## Cost Optimization

1. **Auto-scaling:**
   - Cluster autoscaling
   - Horizontal Pod Autoscaling
   - Vertical Pod Autoscaling (GCP)

2. **Instance Types:**
   - Configurable node sizes
   - Spot/preemptible instances support

3. **Resource Management:**
   - Resource limits and requests
   - Efficient resource allocation

## Monitoring and Observability

1. **Logging:**
   - Cloud-native logging integration
   - Log Analytics (Azure)

2. **Metrics:**
   - Kubernetes metrics
   - Cloud provider metrics

3. **Health Checks:**
   - Liveness probes
   - Readiness probes
   - Startup probes

## Best Practices

1. **Infrastructure as Code:**
   - Version-controlled templates
   - Reproducible deployments
   - State management

2. **Security:**
   - Least privilege IAM
   - Network segmentation
   - Encryption at rest and in transit

3. **Reliability:**
   - Multi-AZ deployment
   - Auto-scaling
   - Health checks

4. **Maintainability:**
   - Clear documentation
   - Modular templates
   - Configuration examples

## Usage Examples

### AWS Terraform

```bash
cd terraform/aws
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init
terraform apply
```

### AWS CloudFormation

```bash
aws cloudformation create-stack \
  --stack-name ai-agent-connector \
  --template-body file://cloudformation/aws/eks-stack.yaml \
  --capabilities CAPABILITY_IAM
```

### GCP Terraform

```bash
cd terraform/gcp
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init
terraform apply
```

### Azure Terraform

```bash
cd terraform/azure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init
terraform apply
```

### One-Click Deployment

```bash
# Bash
./deploy.sh aws

# PowerShell
.\deploy.ps1 -Provider aws
```

## Testing

Templates can be validated using:

1. **Terraform Validate:**
   ```bash
   terraform validate
   ```

2. **Terraform Plan:**
   ```bash
   terraform plan
   ```

3. **CloudFormation Validate:**
   ```bash
   aws cloudformation validate-template \
     --template-body file://cloudformation/aws/eks-stack.yaml
   ```

## Future Enhancements

Potential improvements:
- CI/CD pipeline integration
- Multi-region deployment
- Disaster recovery templates
- Cost monitoring dashboards
- Security scanning automation
- Blue-green deployment support

## Conclusion

The cloud deployment templates provide a complete, production-ready solution for deploying AI Agent Connector to AWS, GCP, and Azure. The templates follow infrastructure-as-code best practices and include comprehensive documentation for easy adoption.
