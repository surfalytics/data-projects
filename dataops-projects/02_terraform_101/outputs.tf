# ============================================================================
# Terraform Outputs
# ============================================================================
# WHY: Outputs allow you to extract and display information about your infrastructure
# WHAT: After 'terraform apply', these values are displayed and can be used by:
# - Other Terraform configurations (via terraform_remote_state data source)
# - CI/CD pipelines
# - External scripts (via 'terraform output -json')
# - Human operators for reference

# Example 1: Simple string output
output "random_suffix" {
  description = "The random suffix generated for this deployment (demonstrates simple output)"
  value       = random_string.suffix.result
}

# Example 2: Object/resource attribute output
output "example_file_path" {
  description = "Path to the example file created (shows how to output resource attributes)"
  value       = local_file.example.filename
}

# Example 3: Local value output
output "resource_prefix" {
  description = "Common resource prefix used across resources (demonstrates outputting local values)"
  value       = local.resource_prefix
}

# Example 4: Complex object output (sensitive data)
# Use 'sensitive = true' to hide values containing secrets
output "common_tags" {
  description = "Common tags applied to resources (map/object output example)"
  value       = local.common_tags
  sensitive   = false
}

# Example 5: List output using for expression
# For loops allow you to transform and extract data from multiple resources
output "multiple_files" {
  description = "List of multiple files created with count (demonstrates list output)"
  value       = [for file in local_file.multiple_files : file.filename]
}

# Example 6: Map output using for_each
output "config_files_map" {
  description = "Map of config files created with for_each (demonstrates map output)"
  value = {
    for key, file in local_file.config_files : key => {
      filename = file.filename
      id       = file.id
    }
  }
}

# Example 7: Conditional output
# Only includes production file if it was created
output "production_file" {
  description = "Production-only file path (null if not in prod environment)"
  value       = var.environment == "prod" ? local_file.production_only[0].filename : null
}

# Example 8: Computed values from locals
output "environment_info" {
  description = "Environment information (demonstrates structured output)"
  value = {
    environment      = var.environment
    is_production    = local.is_production
    resource_prefix  = local.resource_prefix
    formatted_name   = local.resource_name_format
    project_name     = var.project_name
  }
}

# Example 9: Output with complex for expression
output "all_created_files" {
  description = "All files created by this configuration (comprehensive list)"
  value = concat(
    [local_file.example.filename],
    [for file in local_file.multiple_files : file.filename],
    [for key, file in local_file.config_files : file.filename],
    var.environment == "prod" ? [local_file.production_only[0].filename] : []
  )
}

# Example 10: Sensitive output
# Demonstrates how to mark sensitive data
# Access with: terraform output -raw sensitive_example
output "sensitive_example" {
  description = "Example of sensitive output (won't be displayed by default)"
  value       = "This could be a password or API key"
  sensitive   = true
}

# ============================================================================
# Best Practices for Outputs:
# ============================================================================
# 1. Always provide clear descriptions
# 2. Mark sensitive data with 'sensitive = true'
# 3. Use structured outputs (maps/objects) for related data
# 4. Output values that other systems will need
# 5. Don't output sensitive data unless necessary
# 6. Use 'terraform output -json' for machine-readable format
# 7. Consider using output values for terraform_remote_state data sources
