# Terraform 101

A beginner-friendly introduction to Infrastructure as Code (IaC) using Terraform.

## Overview

This project provides a comprehensive, hands-on introduction to Terraform through progressive exercises that take you from basic concepts to production-ready infrastructure code.

### What You'll Learn
- Terraform fundamentals (providers, resources, variables, outputs)
- AWS infrastructure creation (EC2, S3, IAM)
- Professional code organization
- Multi-environment management (dev/prod)
- Reusable Terraform modules
- Infrastructure as Code best practices

### Two Learning Paths

**Path 1: Quick Start (Root Directory)**
Start here if you want a quick overview of Terraform basics using local providers (no cloud account needed).

**Path 2: Progressive Exercises (exercises/ Directory)**
Follow the structured exercises to build expertise from beginner to advanced:
1. **Exercise 1**: Terraform basics (local providers)
2. **Exercise 2**: Simple AWS resources (EC2, S3, IAM in one file)
3. **Exercise 3**: Structured AWS (proper file organization)
4. **Exercise 4**: Environment separation (dev/prod)
5. **Exercise 5**: Terraform modules (reusable components)

👉 **[Start the Progressive Exercises →](./exercises/)**

## Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.0
- Basic understanding of command line interface
- (Optional) Cloud provider account (AWS, Azure, or GCP) for cloud resource examples

## Project Structure

```
02_terraform_101/
├── exercises/              # Progressive learning exercises
│   ├── 01-basics/         # Terraform fundamentals (local providers)
│   ├── 02-simple-aws/     # AWS resources in single file
│   ├── 03-structured-aws/ # Professional file organization
│   ├── 04-environments/   # Dev/prod environment separation
│   ├── 05-modules/        # Reusable Terraform modules
│   └── README.md          # Exercises guide and learning path
├── providers.tf           # Provider configuration
├── variables.tf           # Variable definitions with examples
├── main.tf               # Example resources with detailed explanations
├── outputs.tf            # Output definitions with examples
├── Makefile              # Convenient commands (make help)
├── .gitignore            # Terraform-specific gitignore
└── README.md             # This file
```

## Getting Started

### Choose Your Learning Path

**For Structured Learning** (Recommended):
```bash
cd exercises
cat README.md  # Read the exercises guide
cd 01-basics   # Start with basics
```

**For Quick Demo** (Root directory):

### 1. Initialize Terraform

Initialize the Terraform working directory and download required providers:

```bash
terraform init
```

### 2. Validate Configuration

Check if the configuration is syntactically valid:

```bash
terraform validate
```

### 3. Format Code

Format Terraform files to canonical format:

```bash
terraform fmt
```

### 4. Plan Changes

Preview the changes Terraform will make:

```bash
terraform plan
```

### 5. Apply Changes

Create the resources:

```bash
terraform apply
```

Type `yes` when prompted to confirm.

### 6. View Outputs

After applying, view the output values:

```bash
terraform output
```

### 7. Destroy Resources

Clean up all resources when done:

```bash
terraform destroy
```

## What This Project Creates

By default, this project creates:
- A random string suffix for unique resource naming
- An example text file with timestamp and environment info
- Multiple text files demonstrating the use of `count`

These are simple local resources for learning purposes. The code includes commented examples for AWS, Azure, and GCP resources.

## Customization

### Using Different Environments

```bash
terraform apply -var="environment=staging"
```

### Using a Variables File

Create a `terraform.tfvars` file:

```hcl
environment  = "prod"
project_name = "my-terraform-project"

tags = {
  ManagedBy = "Terraform"
  Project   = "DataOps"
  Team      = "Platform"
}
```

Then apply:

```bash
terraform apply
```

## Key Terraform Concepts

### Providers
Providers are plugins that allow Terraform to interact with cloud platforms, SaaS providers, and APIs.

### Resources
Resources are the most important element in Terraform. Each resource block describes one or more infrastructure objects.

### Variables
Variables allow you to parameterize your Terraform configurations without altering the source code.

### Outputs
Outputs allow you to export structured data about your resources.

### State
Terraform stores information about your infrastructure in a state file (`terraform.tfstate`). Never commit this to version control.

## Best Practices

1. **Use Version Control**: Always commit your `.tf` files to Git
2. **Ignore Sensitive Files**: Never commit `terraform.tfstate`, `*.tfvars`, or provider credentials
3. **Use Remote State**: For team environments, use remote state backends (S3, Azure Blob, GCS)
4. **Plan Before Apply**: Always run `terraform plan` before `terraform apply`
5. **Use Variables**: Avoid hardcoding values; use variables for flexibility
6. **Document Your Code**: Add comments and maintain a good README
7. **Format Consistently**: Run `terraform fmt` before committing
8. **Validate Often**: Run `terraform validate` to catch errors early

## Progressive Learning Exercises

This project includes 5 comprehensive exercises that teach Terraform from basics to advanced concepts:

### [Exercise 1: Terraform Basics](./exercises/01-basics/)
- Duration: 30 minutes | Cost: Free
- Learn core concepts using local providers (no cloud account needed)
- Topics: variables, outputs, count, for_each, conditionals

### [Exercise 2: Simple AWS Resources](./exercises/02-simple-aws/)
- Duration: 45 minutes | Cost: $0 (free tier)
- Create your first AWS infrastructure (EC2, S3, IAM)
- Single file approach for simplicity

### [Exercise 3: Structured AWS](./exercises/03-structured-aws/)
- Duration: 1 hour | Cost: $0.01/hour
- Learn professional file organization
- Topics: data sources, dynamic blocks, template files, lifecycle policies

### [Exercise 4: Environment Separation](./exercises/04-environments/)
- Duration: 1 hour | Cost: $0.03/hour
- Manage dev and prod environments separately
- Topics: environment-specific configs, state isolation, cost optimization

### [Exercise 5: Terraform Modules](./exercises/05-modules/)
- Duration: 2 hours | Cost: $0.03/hour
- Create reusable, production-ready modules
- Topics: module creation, composition, versioning, testing

**[View Complete Exercises Guide →](./exercises/README.md)**

## Quick Commands (Makefile)

This project includes a Makefile for convenient operations:

```bash
make help        # Show all available commands
make setup       # Initialize, validate, and format
make plan        # Preview changes
make apply       # Apply changes
make output      # Show outputs
make destroy     # Destroy all resources
make clean       # Clean up Terraform files
```

## Common Commands

```bash
# Initialize working directory
terraform init

# Validate configuration
terraform validate

# Format code
terraform fmt

# Plan changes
terraform plan

# Apply changes
terraform apply

# Show current state
terraform show

# List resources
terraform state list

# View outputs
terraform output

# Destroy all resources
terraform destroy

# Refresh state
terraform refresh

# Import existing resource
terraform import <resource_type>.<name> <resource_id>
```

## Troubleshooting

### Error: Terraform not initialized
Run `terraform init` first.

### Error: Provider configuration not found
Check that providers are properly configured in `providers.tf`.

### State Lock Errors
If using remote state, ensure no other processes are running Terraform commands.

### Permission Errors
Verify your cloud provider credentials and IAM permissions.

## Resources for Learning

- [Terraform Documentation](https://www.terraform.io/docs)
- [Terraform Registry](https://registry.terraform.io/)
- [HashiCorp Learn](https://learn.hashicorp.com/terraform)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)

## CI/CD Integration

This project can be integrated with CI/CD pipelines:

### GitHub Actions Example

```yaml
name: Terraform

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2

      - name: Terraform Init
        run: terraform init

      - name: Terraform Format
        run: terraform fmt -check

      - name: Terraform Validate
        run: terraform validate

      - name: Terraform Plan
        run: terraform plan
```

## Contributing

Feel free to submit issues or pull requests to improve this project.

## License

This project is for educational purposes.
