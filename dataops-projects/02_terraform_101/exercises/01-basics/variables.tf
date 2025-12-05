# ============================================================================
# Terraform Input Variables
# ============================================================================
# WHY: Variables make your Terraform code reusable and flexible
# WHAT: Input variables allow you to parameterize your configurations without
# changing the actual code. They can be set via:
# - terraform.tfvars files
# - -var command line flags
# - Environment variables (TF_VAR_name)
# - Default values (if specified)

# ============================================================================
# Example 1: Simple String Variable with Default
# ============================================================================
# KEY CONCEPTS:
# - 'type' constrains what values are allowed
# - 'default' provides a fallback value
# - 'description' documents the purpose (shows in terraform plan)
# USAGE: terraform apply -var="environment=prod"

variable "environment" {
  description = "Environment name (dev, staging, prod) - affects resource naming and conditional logic"
  type        = string
  default     = "dev"

  # Optional: Add validation rules
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# ============================================================================
# Example 2: String Variable with Validation
# ============================================================================
# WHY: Validation prevents invalid values from being applied
# BEST PRACTICE: Add validation for critical variables

variable "project_name" {
  description = "Name of the project - used for resource naming and tagging"
  type        = string
  default     = "terraform-101"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

# ============================================================================
# Example 3: Map Variable (Key-Value Pairs)
# ============================================================================
# WHY: Maps are perfect for tags, configuration options, or multiple related values
# KEY CONCEPT: map(string) means all values must be strings

variable "tags" {
  description = "Common tags to apply to all resources (map allows flexible key-value pairs)"
  type        = map(string)
  default = {
    ManagedBy = "Terraform"
    Project   = "DataOps"
  }
}

# ============================================================================
# Example 4: Number Variable
# ============================================================================
# WHY: For numeric values like instance counts, port numbers, or sizes

variable "instance_count" {
  description = "Number of instances to create (demonstrates numeric type)"
  type        = number
  default     = 3

  validation {
    condition     = var.instance_count > 0 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}

# ============================================================================
# Example 5: Boolean Variable
# ============================================================================
# WHY: For feature flags or enable/disable switches

variable "enable_monitoring" {
  description = "Enable monitoring resources (demonstrates boolean type)"
  type        = bool
  default     = false
}

# ============================================================================
# Example 6: List Variable
# ============================================================================
# WHY: For ordered collections of values (like availability zones, subnets)

variable "allowed_ips" {
  description = "List of allowed IP addresses (demonstrates list type)"
  type        = list(string)
  default     = ["10.0.0.0/8", "172.16.0.0/12"]
}

# ============================================================================
# Example 7: Object Variable (Complex Structure)
# ============================================================================
# WHY: For grouping related configuration values with different types

variable "app_config" {
  description = "Application configuration (demonstrates complex object type)"
  type = object({
    name         = string
    port         = number
    replicas     = number
    environment  = string
    enable_https = bool
  })
  default = {
    name         = "my-app"
    port         = 8080
    replicas     = 2
    environment  = "dev"
    enable_https = false
  }
}

# ============================================================================
# Example 8: Variable Without Default (Required)
# ============================================================================
# WHY: Force users to provide critical values
# NOTE: Terraform will prompt for this value if not provided

# variable "required_config" {
#   description = "This variable has no default and must be provided (demonstrates required variable)"
#   type        = string
#   # No default = required variable
# }

# ============================================================================
# Example 9: Sensitive Variable
# ============================================================================
# WHY: Hide sensitive values from logs and console output

variable "api_key_example" {
  description = "Example API key (demonstrates sensitive variable)"
  type        = string
  default     = "dummy-key-for-example"
  sensitive   = true
}

# ============================================================================
# Example 10: Optional with Nullable
# ============================================================================
# WHY: Allow variables to be explicitly set to null

variable "optional_config" {
  description = "Optional configuration (can be null, demonstrates nullable)"
  type        = string
  default     = null
  nullable    = true
}

# ============================================================================
# Cloud Provider Variables (Commented Examples)
# ============================================================================
# Uncomment and modify based on your cloud provider needs

# AWS Examples
# variable "aws_region" {
#   description = "AWS region for resource deployment"
#   type        = string
#   default     = "us-east-1"
#
#   validation {
#     condition     = can(regex("^[a-z]{2}-[a-z]+-\\d{1}$", var.aws_region))
#     error_message = "AWS region must be valid (e.g., us-east-1)."
#   }
# }

# GCP Examples
# variable "gcp_project_id" {
#   description = "GCP project ID for resource deployment"
#   type        = string
#   # No default - this should be required
#
#   validation {
#     condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.gcp_project_id))
#     error_message = "GCP project ID must be 6-30 characters and match naming rules."
#   }
# }

# variable "gcp_region" {
#   description = "GCP region for resource deployment"
#   type        = string
#   default     = "us-central1"
# }

# Azure Examples
# variable "azure_location" {
#   description = "Azure location for resource deployment"
#   type        = string
#   default     = "eastus"
# }

# variable "azure_resource_group_name" {
#   description = "Name of the Azure resource group"
#   type        = string
# }

# ============================================================================
# Best Practices for Variables:
# ============================================================================
# 1. Always provide clear descriptions
# 2. Use appropriate types (string, number, bool, list, map, object)
# 3. Add validation rules for critical variables
# 4. Use defaults for optional variables
# 5. Mark sensitive variables with 'sensitive = true'
# 6. Group related variables together
# 7. Document expected formats and constraints
# 8. Use nullable for truly optional configurations
