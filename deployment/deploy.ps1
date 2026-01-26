# One-click deployment script for AI Agent Connector (PowerShell)
# Supports AWS, GCP, and Azure

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("aws", "gcp", "azure")]
    [string]$Provider
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    $missing = @()
    
    if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
        $missing += "Terraform"
    }
    
    if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
        $missing += "kubectl"
    }
    
    if (-not (Get-Command helm -ErrorAction SilentlyContinue)) {
        $missing += "Helm"
    }
    
    if ($missing.Count -gt 0) {
        Write-Error "Missing prerequisites: $($missing -join ', ')"
        exit 1
    }
    
    Write-Info "All prerequisites met"
}

# AWS deployment
function Deploy-AWS {
    Write-Info "Deploying to AWS..."
    
    Push-Location terraform\aws
    
    try {
        # Check if terraform.tfvars exists
        if (-not (Test-Path terraform.tfvars)) {
            Write-Warn "terraform.tfvars not found, creating from example..."
            Copy-Item terraform.tfvars.example terraform.tfvars
            Write-Warn "Please edit terraform.tfvars with your values"
            exit 1
        }
        
        # Initialize Terraform
        Write-Info "Initializing Terraform..."
        terraform init
        
        # Plan
        Write-Info "Planning deployment..."
        terraform plan
        
        # Apply
        Write-Info "Applying infrastructure..."
        terraform apply -auto-approve
        
        # Configure kubectl
        Write-Info "Configuring kubectl..."
        $configureCmd = terraform output -raw configure_kubectl
        Invoke-Expression $configureCmd
        
        # Get ECR repository URL
        $ecrRepo = terraform output -raw ecr_repository_url
        Write-Info "ECR Repository: $ecrRepo"
        
        # Build and push image
        Write-Info "Building and pushing Docker image..."
        $region = terraform output -raw aws_region
        aws ecr get-login-password --region $region | docker login --username AWS --password-stdin $ecrRepo
        
        docker build -t ai-agent-connector:latest ..\..\.
        docker tag ai-agent-connector:latest "$ecrRepo:latest"
        docker push "$ecrRepo:latest"
        
        Write-Info "AWS deployment complete!"
        Write-Info "ECR Repository: $ecrRepo"
        $clusterName = terraform output -raw cluster_name
        Write-Info "Cluster: $clusterName"
    }
    finally {
        Pop-Location
    }
}

# GCP deployment
function Deploy-GCP {
    Write-Info "Deploying to GCP..."
    
    Push-Location terraform\gcp
    
    try {
        # Check if terraform.tfvars exists
        if (-not (Test-Path terraform.tfvars)) {
            Write-Warn "terraform.tfvars not found, creating from example..."
            Copy-Item terraform.tfvars.example terraform.tfvars
            Write-Warn "Please edit terraform.tfvars with your values"
            exit 1
        }
        
        # Initialize Terraform
        Write-Info "Initializing Terraform..."
        terraform init
        
        # Plan
        Write-Info "Planning deployment..."
        terraform plan
        
        # Apply
        Write-Info "Applying infrastructure..."
        terraform apply -auto-approve
        
        # Configure kubectl
        Write-Info "Configuring kubectl..."
        $configureCmd = terraform output -raw configure_kubectl
        Invoke-Expression $configureCmd
        
        # Get Artifact Registry URL
        $repoUrl = terraform output -raw artifact_registry_url
        Write-Info "Artifact Registry: $repoUrl"
        
        # Build and push image
        Write-Info "Building and pushing Docker image..."
        $region = terraform output -raw gcp_region
        gcloud auth configure-docker "${region}-docker.pkg.dev"
        
        docker build -t ai-agent-connector:latest ..\..\.
        docker tag ai-agent-connector:latest "$repoUrl/ai-agent-connector:latest"
        docker push "$repoUrl/ai-agent-connector:latest"
        
        Write-Info "GCP deployment complete!"
        Write-Info "Artifact Registry: $repoUrl"
        $clusterName = terraform output -raw cluster_name
        Write-Info "Cluster: $clusterName"
    }
    finally {
        Pop-Location
    }
}

# Azure deployment
function Deploy-Azure {
    Write-Info "Deploying to Azure..."
    
    Push-Location terraform\azure
    
    try {
        # Check if terraform.tfvars exists
        if (-not (Test-Path terraform.tfvars)) {
            Write-Warn "terraform.tfvars not found, creating from example..."
            Copy-Item terraform.tfvars.example terraform.tfvars
            Write-Warn "Please edit terraform.tfvars with your values"
            exit 1
        }
        
        # Initialize Terraform
        Write-Info "Initializing Terraform..."
        terraform init
        
        # Plan
        Write-Info "Planning deployment..."
        terraform plan
        
        # Apply
        Write-Info "Applying infrastructure..."
        terraform apply -auto-approve
        
        # Configure kubectl
        Write-Info "Configuring kubectl..."
        $configureCmd = terraform output -raw configure_kubectl
        Invoke-Expression $configureCmd
        
        # Get ACR login server
        $acrLoginServer = terraform output -raw acr_login_server
        $acrName = $acrLoginServer.Split('.')[0]
        Write-Info "ACR: $acrLoginServer"
        
        # Build and push image
        Write-Info "Building and pushing Docker image..."
        az acr login --name $acrName
        
        docker build -t ai-agent-connector:latest ..\..\.
        docker tag ai-agent-connector:latest "$acrLoginServer/ai-agent-connector:latest"
        docker push "$acrLoginServer/ai-agent-connector:latest"
        
        Write-Info "Azure deployment complete!"
        Write-Info "ACR: $acrLoginServer"
        $clusterName = terraform output -raw cluster_name
        Write-Info "Cluster: $clusterName"
    }
    finally {
        Pop-Location
    }
}

# Main
Test-Prerequisites

switch ($Provider) {
    "aws" {
        Deploy-AWS
    }
    "gcp" {
        Deploy-GCP
    }
    "azure" {
        Deploy-Azure
    }
    default {
        Write-Error "Unknown provider: $Provider"
        exit 1
    }
}
