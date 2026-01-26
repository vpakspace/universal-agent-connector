# GCP Terraform Configuration for AI Agent Connector
# Creates GKE cluster, GCR repository, and supporting infrastructure

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "containerregistry.googleapis.com",
    "iam.googleapis.com"
  ])

  project = var.gcp_project_id
  service = each.value

  disable_dependent_services = false
}

# VPC Network
resource "google_compute_network" "main" {
  name                    = "${var.project_name}-vpc"
  auto_create_subnetworks = false

  depends_on = [google_project_service.required_apis]
}

# Subnet
resource "google_compute_subnetwork" "main" {
  name          = "${var.project_name}-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.gcp_region
  network       = google_compute_network.main.id
  private_ip_google_access = true
}

# GKE Cluster
resource "google_container_cluster" "main" {
  name     = "${var.project_name}-cluster"
  location = var.gcp_region

  # Remove default node pool
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.main.name
  subnetwork = google_compute_subnetwork.main.name

  # Enable private cluster
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block   = var.master_ipv4_cidr_block
  }

  # Enable network policy
  network_policy {
    enabled = true
  }

  # Enable workload identity
  workload_identity_config {
    workload_pool = "${var.gcp_project_id}.svc.id.goog"
  }

  # Enable autoscaling
  cluster_autoscaling {
    enabled = true
    resource_limits {
      resource_type = "cpu"
      minimum       = 1
      maximum       = 10
    }
    resource_limits {
      resource_type = "memory"
      minimum       = 1
      maximum       = 50
    }
  }

  # Enable vertical pod autoscaling
  vertical_pod_autoscaling {
    enabled = true
  }

  # Enable horizontal pod autoscaling
  addons_config {
    horizontal_pod_autoscaling {
      disabled = false
    }
    http_load_balancing {
      disabled = false
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Node Pool
resource "google_container_node_pool" "main" {
  name       = "${var.project_name}-node-pool"
  location   = var.gcp_region
  cluster    = google_container_cluster.main.name
  node_count = var.node_count

  autoscaling {
    min_node_count = var.node_min_count
    max_node_count = var.node_max_count
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    preemptible  = var.preemptible_nodes
    machine_type = var.node_machine_type
    disk_size_gb = var.node_disk_size
    disk_type    = "pd-standard"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      project = var.project_name
    }

    tags = [var.project_name]
  }
}

# Service Account for GKE
resource "google_service_account" "gke" {
  account_id   = "${var.project_name}-gke-sa"
  display_name = "GKE Service Account"
}

resource "google_project_iam_member" "gke_service_account" {
  for_each = toset([
    "roles/container.nodeServiceAccount",
    "roles/storage.objectViewer"
  ])

  project = var.gcp_project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke.email}"
}

# Artifact Registry Repository
resource "google_artifact_registry_repository" "app" {
  location      = var.gcp_region
  repository_id = var.project_name
  description   = "Docker repository for AI Agent Connector"
  format        = "DOCKER"
}

# Kubernetes Provider
provider "kubernetes" {
  host                   = "https://${google_container_cluster.main.endpoint}"
  token                  = data.google_client_config.current.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.main.master_auth[0].cluster_ca_certificate)
}

data "google_client_config" "current" {}

# Helm Provider
provider "helm" {
  kubernetes {
    host                   = "https://${google_container_cluster.main.endpoint}"
    token                  = data.google_client_config.current.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.main.master_auth[0].cluster_ca_certificate)
  }
}

# Deploy Helm Chart
resource "helm_release" "ai_agent_connector" {
  name       = var.helm_release_name
  repository = var.helm_chart_path != "" ? null : "https://charts.example.com"
  chart      = var.helm_chart_path != "" ? var.helm_chart_path : "ai-agent-connector"
  version    = var.helm_chart_version
  namespace  = var.kubernetes_namespace
  create_namespace = true

  values = [
    templatefile("${path.module}/helm-values.yaml", {
      image_repository = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.app.repository_id}/${var.project_name}:${var.image_tag}"
      image_tag        = var.image_tag
      replica_count    = var.replica_count
      gcp_region       = var.gcp_region
      gcp_project_id   = var.gcp_project_id
    })
  ]

  depends_on = [
    google_container_node_pool.main,
    google_artifact_registry_repository.app
  ]
}

# Outputs
output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.main.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.main.endpoint
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL"
  value       = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.app.repository_id}"
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.main.name} --region ${var.gcp_region} --project ${var.gcp_project_id}"
}

output "gcp_region" {
  description = "GCP region"
  value       = var.gcp_region
}