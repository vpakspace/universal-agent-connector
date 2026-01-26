#!/bin/bash
# One-click deployment script for AI Agent Connector
# Supports AWS, GCP, and Azure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    local missing=0
    
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed"
        missing=1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        missing=1
    fi
    
    if ! command -v helm &> /dev/null; then
        print_error "Helm is not installed"
        missing=1
    fi
    
    if [ $missing -eq 1 ]; then
        print_error "Please install missing prerequisites"
        exit 1
    fi
    
    print_info "All prerequisites met"
}

# AWS deployment
deploy_aws() {
    print_info "Deploying to AWS..."
    
    cd terraform/aws
    
    # Check if terraform.tfvars exists
    if [ ! -f terraform.tfvars ]; then
        print_warn "terraform.tfvars not found, creating from example..."
        cp terraform.tfvars.example terraform.tfvars
        print_warn "Please edit terraform.tfvars with your values"
        exit 1
    fi
    
    # Initialize Terraform
    print_info "Initializing Terraform..."
    terraform init
    
    # Plan
    print_info "Planning deployment..."
    terraform plan
    
    # Apply
    print_info "Applying infrastructure..."
    terraform apply -auto-approve
    
    # Configure kubectl
    print_info "Configuring kubectl..."
    eval $(terraform output -raw configure_kubectl)
    
    # Get ECR repository URL
    ECR_REPO=$(terraform output -raw ecr_repository_url)
    print_info "ECR Repository: $ECR_REPO"
    
    # Build and push image
    print_info "Building and pushing Docker image..."
    aws ecr get-login-password --region $(terraform output -raw aws_region) | \
        docker login --username AWS --password-stdin $ECR_REPO
    
    docker build -t ai-agent-connector:latest ../../.
    docker tag ai-agent-connector:latest $ECR_REPO:latest
    docker push $ECR_REPO:latest
    
    print_info "AWS deployment complete!"
    print_info "ECR Repository: $ECR_REPO"
    print_info "Cluster: $(terraform output -raw cluster_name)"
}

# GCP deployment
deploy_gcp() {
    print_info "Deploying to GCP..."
    
    cd terraform/gcp
    
    # Check if terraform.tfvars exists
    if [ ! -f terraform.tfvars ]; then
        print_warn "terraform.tfvars not found, creating from example..."
        cp terraform.tfvars.example terraform.tfvars
        print_warn "Please edit terraform.tfvars with your values"
        exit 1
    fi
    
    # Initialize Terraform
    print_info "Initializing Terraform..."
    terraform init
    
    # Plan
    print_info "Planning deployment..."
    terraform plan
    
    # Apply
    print_info "Applying infrastructure..."
    terraform apply -auto-approve
    
    # Configure kubectl
    print_info "Configuring kubectl..."
    eval $(terraform output -raw configure_kubectl)
    
    # Get Artifact Registry URL
    REPO_URL=$(terraform output -raw artifact_registry_url)
    print_info "Artifact Registry: $REPO_URL"
    
    # Build and push image
    print_info "Building and pushing Docker image..."
    gcloud auth configure-docker $(terraform output -raw gcp_region)-docker.pkg.dev
    
    docker build -t ai-agent-connector:latest ../../.
    docker tag ai-agent-connector:latest $REPO_URL/ai-agent-connector:latest
    docker push $REPO_URL/ai-agent-connector:latest
    
    print_info "GCP deployment complete!"
    print_info "Artifact Registry: $REPO_URL"
    print_info "Cluster: $(terraform output -raw cluster_name)"
}

# Azure deployment
deploy_azure() {
    print_info "Deploying to Azure..."
    
    cd terraform/azure
    
    # Check if terraform.tfvars exists
    if [ ! -f terraform.tfvars ]; then
        print_warn "terraform.tfvars not found, creating from example..."
        cp terraform.tfvars.example terraform.tfvars
        print_warn "Please edit terraform.tfvars with your values"
        exit 1
    fi
    
    # Initialize Terraform
    print_info "Initializing Terraform..."
    terraform init
    
    # Plan
    print_info "Planning deployment..."
    terraform plan
    
    # Apply
    print_info "Applying infrastructure..."
    terraform apply -auto-approve
    
    # Configure kubectl
    print_info "Configuring kubectl..."
    eval $(terraform output -raw configure_kubectl)
    
    # Get ACR login server
    ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)
    ACR_NAME=$(echo $ACR_LOGIN_SERVER | cut -d'.' -f1)
    print_info "ACR: $ACR_LOGIN_SERVER"
    
    # Build and push image
    print_info "Building and pushing Docker image..."
    az acr login --name $ACR_NAME
    
    docker build -t ai-agent-connector:latest ../../.
    docker tag ai-agent-connector:latest $ACR_LOGIN_SERVER/ai-agent-connector:latest
    docker push $ACR_LOGIN_SERVER/ai-agent-connector:latest
    
    print_info "Azure deployment complete!"
    print_info "ACR: $ACR_LOGIN_SERVER"
    print_info "Cluster: $(terraform output -raw cluster_name)"
}

# Main
main() {
    if [ $# -eq 0 ]; then
        print_error "Usage: $0 [aws|gcp|azure]"
        exit 1
    fi
    
    PROVIDER=$1
    
    check_prerequisites
    
    case $PROVIDER in
        aws)
            deploy_aws
            ;;
        gcp)
            deploy_gcp
            ;;
        azure)
            deploy_azure
            ;;
        *)
            print_error "Unknown provider: $PROVIDER"
            print_error "Supported providers: aws, gcp, azure"
            exit 1
            ;;
    esac
}

main "$@"
