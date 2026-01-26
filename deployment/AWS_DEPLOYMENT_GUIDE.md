# AWS Deployment Guide

Complete guide for deploying AI Agent Connector to AWS using Terraform or CloudFormation.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Terraform >= 1.0 (for Terraform deployment)
- kubectl installed
- Helm 3.0+ installed
- Docker installed (for building/pushing images)

## Option 1: Terraform Deployment

### Step 1: Configure Variables

1. Copy the example variables file:
```bash
cd terraform/aws
cp terraform.tfvars.example terraform.tfvars
```

2. Edit `terraform.tfvars` with your values:
```hcl
aws_region = "us-east-1"
project_name = "ai-agent-connector"
vpc_cidr = "10.0.0.0/16"
availability_zones_count = 2
node_instance_types = ["t3.medium"]
node_desired_size = 2
node_min_size = 1
node_max_size = 10
```

### Step 2: Initialize Terraform

```bash
terraform init
```

### Step 3: Review Plan

```bash
terraform plan
```

### Step 4: Apply Infrastructure

```bash
terraform apply
```

This will create:
- VPC with public and private subnets
- EKS cluster
- EKS node group
- ECR repository
- All necessary IAM roles and policies
- Deploy Helm chart

### Step 5: Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name ai-agent-connector-cluster
```

### Step 6: Verify Deployment

```bash
# Check pods
kubectl get pods -n production

# Check services
kubectl get svc -n production

# Check HPA
kubectl get hpa -n production
```

## Option 2: CloudFormation Deployment

### Step 1: Create Stack

```bash
aws cloudformation create-stack \
  --stack-name ai-agent-connector-stack \
  --template-body file://cloudformation/aws/eks-stack.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=ai-agent-connector \
    ParameterKey=VpcCidr,ParameterValue=10.0.0.0/16 \
    ParameterKey=NodeInstanceType,ParameterValue=t3.medium \
    ParameterKey=NodeDesiredSize,ParameterValue=2 \
    ParameterKey=NodeMinSize,ParameterValue=1 \
    ParameterKey=NodeMaxSize,ParameterValue=10 \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

### Step 2: Wait for Stack Creation

```bash
aws cloudformation wait stack-create-complete \
  --stack-name ai-agent-connector-stack \
  --region us-east-1
```

### Step 3: Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name ai-agent-connector-stack \
  --region us-east-1 \
  --query 'Stacks[0].Outputs'
```

### Step 4: Configure kubectl

```bash
# Get cluster name from outputs
CLUSTER_NAME=$(aws cloudformation describe-stacks \
  --stack-name ai-agent-connector-stack \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`EKSClusterName`].OutputValue' \
  --output text)

aws eks update-kubeconfig --region us-east-1 --name $CLUSTER_NAME
```

### Step 5: Deploy Helm Chart

```bash
# Get ECR repository URL from outputs
ECR_REPO=$(aws cloudformation describe-stacks \
  --stack-name ai-agent-connector-stack \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryURI`].OutputValue' \
  --output text)

# Install Helm chart
helm install ai-agent-connector ../../helm/ai-agent-connector \
  --namespace production \
  --create-namespace \
  --set image.repository=$ECR_REPO \
  --set image.tag=latest
```

## Building and Pushing Docker Image

### Step 1: Build Image

```bash
# Get ECR repository URL
ECR_REPO=$(terraform output -raw ecr_repository_url)

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REPO

# Build image
docker build -t ai-agent-connector:latest .

# Tag image
docker tag ai-agent-connector:latest $ECR_REPO:latest

# Push image
docker push $ECR_REPO:latest
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

If using LoadBalancer service type:

```bash
# Get LoadBalancer URL
kubectl get svc -n production ai-agent-connector -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### Option 2: Port Forward

```bash
kubectl port-forward -n production svc/ai-agent-connector 5000:5000
```

Then access: `http://localhost:5000`

### Option 3: Ingress

If ingress is enabled, configure DNS to point to the ingress controller's LoadBalancer.

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

### Check HPA Status

```bash
kubectl get hpa -n production
kubectl describe hpa -n production ai-agent-connector
```

## Updating Deployment

### Update Helm Chart

```bash
helm upgrade ai-agent-connector ../../helm/ai-agent-connector \
  --namespace production \
  --set image.tag=new-tag
```

### Update Infrastructure

```bash
# Update Terraform
terraform plan
terraform apply

# Update CloudFormation
aws cloudformation update-stack \
  --stack-name ai-agent-connector-stack \
  --template-body file://cloudformation/aws/eks-stack.yaml \
  --parameters ... \
  --capabilities CAPABILITY_IAM
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
# Verify ECR access
aws ecr describe-repositories --region us-east-1

# Check node IAM role has ECR permissions
# Verify image exists in ECR
aws ecr describe-images --repository-name ai-agent-connector --region us-east-1
```

### Network Issues

```bash
# Check VPC configuration
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=ai-agent-connector"

# Check security groups
aws ec2 describe-security-groups --filters "Name=tag:Project,Values=ai-agent-connector"
```

## Cleanup

### Terraform

```bash
terraform destroy
```

### CloudFormation

```bash
aws cloudformation delete-stack \
  --stack-name ai-agent-connector-stack \
  --region us-east-1
```

## Cost Optimization

1. **Use Spot Instances**: Configure node groups to use spot instances
2. **Right-size Nodes**: Adjust node instance types based on workload
3. **Auto-scaling**: Configure appropriate min/max node counts
4. **Reserved Instances**: Consider reserved instances for predictable workloads

## Security Best Practices

1. **Enable Encryption**: Enable EBS encryption and ECR encryption
2. **Network Policies**: Implement Kubernetes network policies
3. **Secrets Management**: Use AWS Secrets Manager or external-secrets operator
4. **IAM Roles**: Use IAM roles for service accounts (IRSA)
5. **Private Endpoints**: Use private EKS endpoints for production

## Next Steps

- Set up CI/CD pipeline
- Configure monitoring and alerting
- Set up backup and disaster recovery
- Implement security scanning
- Configure autoscaling policies
