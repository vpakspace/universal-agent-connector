variable "azure_region" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ai-agent-connector"
}

variable "vnet_address_space" {
  description = "Address space for VNet"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_address_prefix" {
  description = "Address prefix for subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "node_count" {
  description = "Initial number of nodes"
  type        = number
  default     = 2
}

variable "node_min_count" {
  description = "Minimum number of nodes"
  type        = number
  default     = 1
}

variable "node_max_count" {
  description = "Maximum number of nodes"
  type        = number
  default     = 10
}

variable "node_vm_size" {
  description = "VM size for nodes"
  type        = string
  default     = "Standard_D2s_v3"
}

variable "node_os_disk_size_gb" {
  description = "OS disk size for nodes (GB)"
  type        = number
  default     = 50
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
