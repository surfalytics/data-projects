# Terraform 101 - Basic Examples
# This file demonstrates core Terraform concepts using simple, local providers
# to help you understand the fundamentals before working with cloud resources.

# ============================================================================
# Example 1: Resource Creation & Dependencies
# ============================================================================
# WHY: Understanding resource creation is fundamental to Terraform.
# WHAT: This creates a random string that will be used by other resources.
# KEY CONCEPT: Terraform automatically handles resource dependencies when one
# resource references another (e.g., local_file references random_string.suffix).
# This ensures resources are created in the correct order.

resource "random_string" "suffix" {
  length  = 8
  special = false  # No special characters for cleaner file names
  upper   = false  # Lowercase only for consistency

  # Keepers force new random value when changed
  keepers = {
    environment = var.environment
  }
}

# ============================================================================
# Example 2: String Interpolation & Built-in Functions
# ============================================================================
# WHY: Real infrastructure code requires dynamic values and string manipulation.
# WHAT: Demonstrates how to use variables, functions, and heredoc syntax.
# KEY CONCEPTS:
# - ${var.name} syntax for variable interpolation
# - ${resource_type.name.attribute} for resource attribute references
# - timestamp() function for dynamic values
# - path.module for portable file paths
# - <<-EOT heredoc for multi-line strings

resource "local_file" "example" {
  filename = "${path.module}/output/example-${random_string.suffix.result}.txt"

  # Heredoc syntax for multi-line content
  content = <<-EOT
    Environment: ${var.environment}
    Project: ${var.project_name}
    Generated at: ${timestamp()}

    This is a sample file created by Terraform.
    You can use this pattern to generate configuration files,
    documentation, or any text-based resources.

    Common use cases:
    - Generating application config files
    - Creating cloud-init scripts
    - Building Kubernetes manifests
    - Templating infrastructure documentation
  EOT

  file_permission = "0644"

  # This resource depends on random_string.suffix
  # Terraform automatically detects this dependency
}

# ============================================================================
# Example 3: Local Values (Computed Values)
# ============================================================================
# WHY: Avoid repeating complex expressions and make code more maintainable.
# WHAT: Local values are like temporary variables that compute once and can
# be reused throughout your configuration.
# KEY CONCEPTS:
# - locals {} block for defining reusable computed values
# - merge() function for combining maps
# - String interpolation in local values
# BEST PRACTICE: Use locals for values used multiple times or complex logic

locals {
  # Computed resource prefix used across all resources
  resource_prefix = "${var.project_name}-${var.environment}"

  # Merge base tags with environment-specific tags
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Timestamp   = timestamp()
      ManagedBy   = "Terraform"
    }
  )

  # Example: Conditional logic in locals
  is_production = var.environment == "prod"

  # Example: Complex computed values
  resource_name_format = lower(replace(local.resource_prefix, "_", "-"))
}

# ============================================================================
# Example 4: Meta-Arguments - Count (Creating Multiple Resources)
# ============================================================================
# WHY: Often need to create multiple similar resources without duplicating code.
# WHAT: The 'count' meta-argument creates multiple instances of a resource.
# KEY CONCEPTS:
# - count.index provides the current iteration number (0-based)
# - Creates resources named: resource_type.name[0], resource_type.name[1], etc.
# - Useful for creating similar resources with slight variations
# LIMITATION: If you remove an item from the middle, Terraform will recreate
# all subsequent resources. Use for_each for more stability.

resource "local_file" "multiple_files" {
  count = 3

  filename        = "${path.module}/output/file-${count.index}.txt"
  content         = <<-EOT
    File Number: ${count.index + 1}
    Zero-based Index: ${count.index}
    Resource Name: ${local.resource_prefix}

    This demonstrates the 'count' meta-argument.
    Count is useful when you need N identical resources.
  EOT
  file_permission = "0644"
}

# ============================================================================
# Example 5: Meta-Arguments - for_each (Creating Multiple Resources with Map)
# ============================================================================
# WHY: for_each is more stable than count when resource order might change.
# WHAT: Creates one resource instance per map key or set element.
# KEY CONCEPTS:
# - each.key and each.value provide access to current item
# - Resources are named by their keys (more stable than numeric indices)
# - Better for managing resources that might be added/removed dynamically
# BEST PRACTICE: Prefer for_each over count for most use cases

resource "local_file" "config_files" {
  for_each = {
    development = "dev.example.com"
    staging     = "staging.example.com"
    production  = "prod.example.com"
  }

  filename = "${path.module}/output/config-${each.key}.txt"
  content  = <<-EOT
    Environment: ${each.key}
    Endpoint: ${each.value}
    Resource Prefix: ${local.resource_prefix}

    This demonstrates the 'for_each' meta-argument.
    for_each is better than count when resources need stable names.
  EOT

  file_permission = "0644"
}

# ============================================================================
# Example 6: Conditional Resources (count with condition)
# ============================================================================
# WHY: Sometimes you want to create resources only in certain conditions.
# WHAT: Using count with a conditional expression (ternary operator).
# KEY CONCEPT: count = 0 means "don't create this resource"
# USE CASE: Create monitoring resources only in production, or
# create different resource types based on environment

resource "local_file" "production_only" {
  # Create this file only if environment is "prod"
  count = var.environment == "prod" ? 1 : 0

  filename        = "${path.module}/output/production-config.txt"
  content         = "This file only exists in production environment"
  file_permission = "0644"
}

# ============================================================================
# Example 7: Data Sources vs Resources
# ============================================================================
# WHY: Sometimes you need to reference existing resources rather than create new ones.
# WHAT: This shows the pattern (using local example since we can't query real data sources).
# KEY CONCEPT: 'data' blocks READ existing infrastructure, 'resource' blocks CREATE/MANAGE it.
# Real examples: data.aws_ami, data.azurerm_subscription, data.google_project

# This is a simulated example - in real scenarios you'd query existing cloud resources
# data "aws_ami" "ubuntu" {
#   most_recent = true
#   owners      = ["099720109477"] # Canonical
#   filter {
#     name   = "name"
#     values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
#   }
# }

# Example: Add your cloud resources here
# resource "aws_s3_bucket" "example" {
#   bucket = "${local.resource_prefix}-bucket"
#   tags   = local.common_tags
# }

# resource "google_storage_bucket" "example" {
#   name     = "${local.resource_prefix}-bucket"
#   location = var.gcp_region
#   labels   = local.common_tags
# }
