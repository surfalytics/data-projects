terraform {
  required_version = ">= 1.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

# Example provider configuration
# Uncomment and modify based on your cloud provider
# provider "aws" {
#   region = var.aws_region
# }

# provider "azurerm" {
#   features {}
# }

# provider "google" {
#   project = var.gcp_project_id
#   region  = var.gcp_region
# }
