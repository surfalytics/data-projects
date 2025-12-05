# Define ANSI color codes
YELLOW = \033[1;33m
GREEN = \033[1;32m
BLUE = \033[1;34m
RESET = \033[0m

# Default target
.DEFAULT_GOAL := help

# Initialize Terraform
.PHONY: init
init:
	@echo "$(YELLOW)Initializing Terraform...$(RESET)"
	terraform init
	@echo "$(GREEN)Terraform initialized successfully!$(RESET)"

# Validate Terraform configuration
.PHONY: validate
validate:
	@echo "$(YELLOW)Validating Terraform configuration...$(RESET)"
	terraform validate
	@echo "$(GREEN)Configuration is valid!$(RESET)"

# Format Terraform files
.PHONY: fmt
fmt:
	@echo "$(YELLOW)Formatting Terraform files...$(RESET)"
	terraform fmt -recursive
	@echo "$(GREEN)Files formatted successfully!$(RESET)"

# Check if files are formatted
.PHONY: fmt-check
fmt-check:
	@echo "$(YELLOW)Checking Terraform file formatting...$(RESET)"
	terraform fmt -check -recursive
	@echo "$(GREEN)All files are properly formatted!$(RESET)"

# Plan Terraform changes
.PHONY: plan
plan:
	@echo "$(YELLOW)Planning Terraform changes...$(RESET)"
	terraform plan
	@echo "$(GREEN)Plan completed successfully!$(RESET)"

# Apply Terraform changes
.PHONY: apply
apply:
	@echo "$(YELLOW)Applying Terraform changes...$(RESET)"
	terraform apply
	@echo "$(GREEN)Changes applied successfully!$(RESET)"

# Apply changes without confirmation (use with caution)
.PHONY: apply-auto
apply-auto:
	@echo "$(YELLOW)Auto-applying Terraform changes...$(RESET)"
	terraform apply -auto-approve
	@echo "$(GREEN)Changes applied successfully!$(RESET)"

# Show current state
.PHONY: show
show:
	@echo "$(YELLOW)Showing Terraform state...$(RESET)"
	terraform show

# List resources
.PHONY: list
list:
	@echo "$(YELLOW)Listing Terraform resources...$(RESET)"
	terraform state list

# Show outputs
.PHONY: output
output:
	@echo "$(YELLOW)Showing Terraform outputs...$(RESET)"
	terraform output

# Destroy all resources
.PHONY: destroy
destroy:
	@echo "$(YELLOW)Destroying Terraform resources...$(RESET)"
	terraform destroy
	@echo "$(GREEN)Resources destroyed successfully!$(RESET)"

# Destroy all resources without confirmation (use with caution)
.PHONY: destroy-auto
destroy-auto:
	@echo "$(YELLOW)Auto-destroying Terraform resources...$(RESET)"
	terraform destroy -auto-approve
	@echo "$(GREEN)Resources destroyed successfully!$(RESET)"

# Clean up Terraform files
.PHONY: clean
clean:
	@echo "$(YELLOW)Cleaning up Terraform files...$(RESET)"
	rm -rf .terraform
	rm -f .terraform.lock.hcl
	rm -f terraform.tfstate*
	rm -f *.tfplan
	rm -rf output/*
	@echo "$(GREEN)Cleanup completed successfully!$(RESET)"

# Full setup: init, validate, format
.PHONY: setup
setup: init validate fmt
	@echo "$(GREEN)Terraform setup completed!$(RESET)"

# CI workflow: init, validate, format-check, plan
.PHONY: ci
ci: init validate fmt-check plan
	@echo "$(GREEN)CI checks passed!$(RESET)"

# Display help
.PHONY: help
help:
	@echo "$(BLUE)╔══════════════════════════════════════════════════════════╗$(RESET)"
	@echo "$(BLUE)║          Terraform 101 - Available Commands              ║$(RESET)"
	@echo "$(BLUE)╚══════════════════════════════════════════════════════════╝$(RESET)"
	@echo ""
	@echo "$(YELLOW)Setup & Initialization:$(RESET)"
	@echo "  $(GREEN)make init$(RESET)        - Initialize Terraform working directory"
	@echo "  $(GREEN)make setup$(RESET)       - Full setup (init + validate + format)"
	@echo ""
	@echo "$(YELLOW)Code Quality:$(RESET)"
	@echo "  $(GREEN)make validate$(RESET)    - Validate Terraform configuration"
	@echo "  $(GREEN)make fmt$(RESET)         - Format Terraform files"
	@echo "  $(GREEN)make fmt-check$(RESET)   - Check if files are properly formatted"
	@echo ""
	@echo "$(YELLOW)Planning & Deployment:$(RESET)"
	@echo "  $(GREEN)make plan$(RESET)        - Preview changes Terraform will make"
	@echo "  $(GREEN)make apply$(RESET)       - Apply Terraform changes (with confirmation)"
	@echo "  $(GREEN)make apply-auto$(RESET)  - Apply changes without confirmation"
	@echo ""
	@echo "$(YELLOW)Inspection:$(RESET)"
	@echo "  $(GREEN)make show$(RESET)        - Show current Terraform state"
	@echo "  $(GREEN)make list$(RESET)        - List all resources in state"
	@echo "  $(GREEN)make output$(RESET)      - Show output values"
	@echo ""
	@echo "$(YELLOW)Cleanup:$(RESET)"
	@echo "  $(GREEN)make destroy$(RESET)     - Destroy all resources (with confirmation)"
	@echo "  $(GREEN)make destroy-auto$(RESET) - Destroy resources without confirmation"
	@echo "  $(GREEN)make clean$(RESET)       - Remove all Terraform files and state"
	@echo ""
	@echo "$(YELLOW)CI/CD:$(RESET)"
	@echo "  $(GREEN)make ci$(RESET)          - Run CI checks (init + validate + fmt-check + plan)"
	@echo ""
	@echo "$(YELLOW)Quick Start:$(RESET)"
	@echo "  1. $(GREEN)make setup$(RESET)     - Initialize and validate"
	@echo "  2. $(GREEN)make plan$(RESET)      - Review planned changes"
	@echo "  3. $(GREEN)make apply$(RESET)     - Apply the changes"
	@echo "  4. $(GREEN)make output$(RESET)    - View outputs"
	@echo "  5. $(GREEN)make destroy$(RESET)   - Clean up when done"
	@echo ""
