# Exercise 4: Environment Separation (Dev/Prod)

## Goal
Learn how to manage multiple environments (dev, staging, prod) with different configurations while sharing common code.

## What You'll Learn
- Environment-specific configurations
- Workspace vs directory-based approach
- Using backend configuration for state isolation
- Different instance types/sizes per environment
- Environment-specific security rules
- Cost optimization strategies per environment

## Project Structure

```
04-environments/
├── dev/
│   ├── backend.tf       # Dev backend configuration
│   ├── terraform.tfvars # Dev-specific values
│   └── main.tf          # Points to shared modules
├── prod/
│   ├── backend.tf       # Prod backend configuration
│   ├── terraform.tfvars # Prod-specific values
│   └── main.tf          # Points to shared modules
└── README.md            # This file
```

##Two Approaches to Environment Management

### Approach 1: Separate Directories (This Exercise)
```
project/
├── dev/
│   ├── main.tf
│   └── terraform.tfvars
└── prod/
    ├── main.tf
    └── terraform.tfvars
```
**Pros**:
- Complete state isolation
- Different backends per environment
- Clear separation
- Difficult to accidentally affect prod

**Cons**:
- Code duplication
- Must maintain multiple directories

### Approach 2: Terraform Workspaces
```
terraform workspace new dev
terraform workspace new prod
```
**Pros**:
- Single codebase
- Less duplication

**Cons**:
- Same backend (risky)
- Easy to forget which workspace you're in
- State in same bucket

**Recommendation**: Use separate directories for dev/prod (Approach 1)

## Setup

### Step 1: Deploy to Dev First
```bash
cd exercises/04-environments/dev
terraform init
terraform plan
terraform apply
```

### Step 2: Review Dev Resources
```bash
terraform output
# Note the smaller instance type, relaxed security
```

### Step 3: Deploy to Prod
```bash
cd ../prod
terraform init
terraform plan
terraform apply
```

### Step 4: Compare Environments
```bash
# Compare outputs
cd ../dev && terraform output > /tmp/dev-outputs.txt
cd ../prod && terraform output > /tmp/prod-outputs.txt
diff /tmp/dev-outputs.txt /tmp/prod-outputs.txt
```

## Environment Differences

| Aspect | Dev | Prod |
|--------|-----|------|
| **Instance Type** | t2.micro | t3.small |
| **Monitoring** | Disabled | Enabled |
| **SSH Access** | Your IP | Bastion/VPN only |
| **Backups** | Disabled | Enabled |
| **High Availability** | Single AZ | Multi-AZ |
| **Encryption** | Optional | Mandatory |
| **Cost** | ~$8/month | ~$30/month |

## Best Practices

### 1. State Isolation
Each environment should have its own state file, ideally in separate S3 buckets:
```hcl
# dev/backend.tf
terraform {
  backend "s3" {
    bucket = "mycompany-terraform-state-dev"
    key    = "app/terraform.tfstate"
    region = "us-east-1"
  }
}

# prod/backend.tf
terraform {
  backend "s3" {
    bucket = "mycompany-terraform-state-prod"
    key    = "app/terraform.tfstate"
    region = "us-east-1"
  }
}
```

### 2. Variable Files
Use `.tfvars` files for environment-specific values:
```hcl
# dev.tfvars
environment   = "dev"
instance_type = "t2.micro"
min_size      = 1
max_size      = 2

# prod.tfvars
environment   = "prod"
instance_type = "t3.small"
min_size      = 2
max_size      = 10
```

### 3. Naming Conventions
Include environment in all resource names:
```hcl
resource "aws_instance" "web" {
  tags = {
    Name = "${var.project}-${var.environment}-web"
    Environment = var.environment
  }
}
```

### 4. Access Control
- **Dev**: Developers have full access
- **Prod**: Limited access, changes via CI/CD only

### 5. Approval Process
```bash
# Dev: Direct apply
terraform apply

# Prod: Require approval
terraform plan -out=prod.tfplan
# Get approval from team
terraform apply prod.tfplan
```

## Exercises

### Exercise 1: Add Staging Environment
1. Create a `staging/` directory
2. Copy files from `dev/`
3. Adjust values to be between dev and prod
4. Deploy and verify

### Exercise 2: Implement Backend State
1. Create S3 buckets for state
2. Add backend configuration
3. Migrate existing state: `terraform init -migrate-state`

### Exercise 3: Add Environment-Specific Features
Create resources that only exist in prod:
```hcl
resource "aws_cloudwatch_alarm" "cpu" {
  count = var.environment == "prod" ? 1 : 0
  # ...
}
```

### Exercise 4: Cost Tagging
Add cost allocation tags:
```hcl
default_tags {
  tags = {
    Environment  = var.environment
    CostCenter   = var.environment == "prod" ? "production" : "development"
    AutoShutdown = var.environment != "prod" ? "true" : "false"
  }
}
```

## Managing Multiple Environments

### Daily Workflow
```bash
# Work on dev
cd dev
terraform plan
terraform apply

# Promote to prod (after testing)
cd ../prod
terraform plan  # Review carefully!
terraform apply # With approval
```

### Drift Detection
```bash
# Check if infrastructure matches state
cd dev
terraform plan -detailed-exitcode
# Exit code 0 = no changes
# Exit code 2 = changes detected
```

### Disaster Recovery
```bash
# Export dev state
cd dev
terraform state pull > dev-state-backup.json

# Recreate from state
terraform import aws_instance.web i-1234567890abcdef0
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Terraform

on:
  push:
    branches: [main]
    paths: ['environments/dev/**']

jobs:
  terraform-dev:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2

      - name: Terraform Init
        run: terraform init
        working-directory: ./environments/dev

      - name: Terraform Plan
        run: terraform plan
        working-directory: ./environments/dev

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main'
        run: terraform apply -auto-approve
        working-directory: ./environments/dev
```

### Production Deployment (Manual Approval)
```yaml
jobs:
  terraform-prod:
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      # ... same as dev but in prod directory
```

## Security Considerations

### 1. State File Security
- Enable encryption at rest
- Use versioning
- Restrict access with IAM
- Enable MFA delete

### 2. Credentials
- Never commit `.tfvars` with secrets
- Use AWS Secrets Manager or SSM Parameter Store
- Use different AWS accounts for dev/prod

### 3. Network Isolation
- Separate VPCs per environment
- Prod in private subnets
- Use VPN/bastion for prod access

## Cost Management

### Dev Environment Cost Savings
1. Stop instances after hours
2. Use smaller instance types
3. Disable unnecessary features
4. Delete when not in use

### Automation Script
```bash
#!/bin/bash
# stop-dev-resources.sh

# Stop dev EC2 instances at 6 PM
aws ec2 stop-instances \
  --instance-ids $(aws ec2 describe-instances \
    --filters "Name=tag:Environment,Values=dev" \
    --query 'Reservations[].Instances[].InstanceId' \
    --output text)
```

## Troubleshooting

### Issue: State lock error
**Solution**: Check if another process is running, or force-unlock:
```bash
terraform force-unlock LOCK_ID
```

### Issue: Resources exist in AWS but not in state
**Solution**: Import them:
```bash
terraform import aws_instance.web i-1234567890abcdef0
```

### Issue: Different results in dev vs prod
**Solution**: Check `terraform.tfvars` values and AWS account settings

## Next Steps
Move to **Exercise 5** to learn about Terraform modules for maximum code reuse.

## Additional Resources
- [Terraform Workspaces](https://www.terraform.io/docs/language/state/workspaces.html)
- [Backend Configuration](https://www.terraform.io/docs/language/settings/backends/configuration.html)
- [AWS Multi-Account Strategy](https://aws.amazon.com/organizations/)
