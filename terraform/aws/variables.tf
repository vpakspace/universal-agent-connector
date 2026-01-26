variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ai-agent-connector"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones_count" {
  description = "Number of availability zones"
  type        = number
  default     = 2
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "node_instance_types" {
  description = "EC2 instance types for EKS nodes"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "Desired number of nodes"
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum number of nodes"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum number of nodes"
  type        = number
  default     = 10
}

variable "ecr_repository_name" {
  description = "ECR repository name"
  type        = string
  default     = "ai-agent-connector"
}

variable "helm_release_name" {
  description = "Helm release name"
  type        = string
  default     = "ai-agent-connector"
}

variable "helm_chart_path" {
  description = "Local path to Helm chart (empty to use remote)"
  type        = string
  default     = ""
}

variable "helm_chart_version" {
  description = "Helm chart version"
  type        = string
  default     = "1.0.0"
}

variable "kubernetes_namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "production"
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

variable "replica_count" {
  description = "Number of replicas"
  type        = number
  default     = 2
}
