# Exercise 5: Terraform Modules

## Goal
Learn to create reusable Terraform modules for maximum code reuse and maintainability.

## What You'll Learn
- Creating custom modules
- Module inputs and outputs
- Module composition
- Versioning modules
- Module testing
- Publishing modules (optional)

## Project Structure

```
05-modules/
├── modules/
│   ├── ec2/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── s3/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── iam/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── dev/
│   │   └── main.tf
│   └── prod/
│       └── main.tf
└── README.md
```

## What is a Terraform Module?

A module is a container for multiple resources that are used together. Every Terraform configuration has at least one module (the "root" module).

### Benefits:
1. **Reusability**: Write once, use many times
2. **Consistency**: Same configuration across environments
3. **Abstraction**: Hide complexity
4. **Testing**: Test modules independently
5. **Versioning**: Version control your infrastructure patterns

## Module Structure

### Input Variables (variables.tf)
```hcl
variable "environment" {
  description = "Environment name"
  type        = string
}
```

### Resources (main.tf)
```hcl
resource "aws_instance" "this" {
  ami = var.ami_id
  # ...
}
```

### Outputs (outputs.tf)
```hcl
output "instance_id" {
  value = aws_instance.this.id
}
```

## Using Modules

### Local Module
```hcl
module "web_server" {
  source = "../../modules/ec2"

  environment   = "dev"
  instance_type = "t2.micro"
}
```

### Remote Module (Terraform Registry)
```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"
}
```

### Git Module
```hcl
module "web_server" {
  source = "git::https://github.com/company/terraform-modules.git//ec2?ref=v1.0.0"

  environment = "prod"
}
```

## Instructions

### Step 1: Review Module Structure
Examine each module:
- **modules/ec2**: EC2 instance with security group
- **modules/s3**: S3 bucket with security settings
- **modules/iam**: IAM role for EC2

### Step 2: Deploy Dev Environment
```bash
cd exercises/05-modules/environments/dev
terraform init
terraform plan
terraform apply
```

### Step 3: Deploy Prod Environment
```bash
cd ../prod
terraform init
terraform plan
terraform apply
```

Notice how both environments use the same modules but with different configurations!

### Step 4: Modify a Module
Update `modules/ec2/main.tf` to add a new tag.
Both dev and prod will inherit this change on next apply.

## Module Best Practices

### 1. Module Naming
- Lowercase, hyphens
- Format: `terraform-<PROVIDER>-<NAME>`
- Example: `terraform-aws-ec2-instance`

### 2. README for Each Module
```markdown
# EC2 Instance Module

## Usage
\`\`\`hcl
module "web" {
  source = "./modules/ec2"

  environment = "prod"
  instance_type = "t3.small"
}
\`\`\`

## Inputs
| Name | Type | Default | Description |
|------|------|---------|-------------|
| environment | string | - | Environment name |

## Outputs
| Name | Description |
|------|-------------|
| instance_id | EC2 instance ID |
```

### 3. Semantic Versioning
```
v1.0.0 - Major.Minor.Patch
v1.1.0 - New feature (backward compatible)
v2.0.0 - Breaking change
```

### 4. Input Validation
```hcl
variable "environment" {
  type = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Must be dev or prod"
  }
}
```

### 5. Output Everything Useful
```hcl
output "instance_id" {
  value = aws_instance.this.id
}

output "public_ip" {
  value = aws_instance.this.public_ip
}

output "arn" {
  value = aws_instance.this.arn
}
```

## Advanced Module Patterns

### Pattern 1: Conditional Resources
```hcl
resource "aws_eip" "this" {
  count = var.assign_eip ? 1 : 0

  instance = aws_instance.this.id
}
```

### Pattern 2: Dynamic Module Composition
```hcl
module "web_servers" {
  for_each = var.servers

  source = "./modules/ec2"

  name = each.key
  size = each.value.size
}
```

### Pattern 3: Module Chaining
```hcl
module "network" {
  source = "./modules/network"
}

module "compute" {
  source = "./modules/compute"

  vpc_id    = module.network.vpc_id
  subnet_id = module.network.subnet_id
}
```

## Testing Modules

### Manual Testing
```bash
cd modules/ec2
terraform init
terraform plan
# Create test fixtures in examples/ directory
```

### Automated Testing (Terratest)
```go
func TestEC2Module(t *testing.T) {
    opts := &terraform.Options{
        TerraformDir: "../modules/ec2",
    }

    defer terraform.Destroy(t, opts)
    terraform.InitAndApply(t, opts)

    instanceID := terraform.Output(t, opts, "instance_id")
    assert.NotEmpty(t, instanceID)
}
```

## Publishing Modules

### Option 1: Private Git Repository
```hcl
module "web" {
  source = "git::ssh://git@github.com/company/modules.git//ec2?ref=v1.0.0"
}
```

### Option 2: Terraform Registry
1. Create GitHub repo: `terraform-aws-ec2-instance`
2. Tag releases: `v1.0.0`
3. Publish to registry.terraform.io

### Option 3: Private Registry
- Terraform Cloud/Enterprise
- Artifactory
- Custom solution

## Real-World Module Structure

```
terraform-modules/
├── aws/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── README.md
│   │   └── examples/
│   │       └── complete/
│   │           └── main.tf
│   ├── ec2/
│   ├── rds/
│   └── s3/
└── azure/
    ├── vm/
    └── storage/
```

## Common Pitfalls

### 1. Too Much Abstraction
❌ Bad: One module for everything
✅ Good: Focused, single-purpose modules

### 2. Hard-Coded Values
❌ Bad: `region = "us-east-1"`
✅ Good: `region = var.aws_region`

### 3. No Versioning
❌ Bad: `source = "git::https://..."`
✅ Good: `source = "git::https://...?ref=v1.0.0"`

### 4. Circular Dependencies
❌ Bad: Module A depends on Module B, Module B depends on Module A
✅ Good: Clear dependency hierarchy

## Module Documentation

### Auto-Generate Docs
```bash
# Install terraform-docs
brew install terraform-docs

# Generate docs
terraform-docs markdown table ./modules/ec2 > ./modules/ec2/README.md
```

### Example Output
```markdown
## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| aws | ~> 5.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| environment | Environment name | `string` | n/a | yes |
```

## Exercises

### Exercise 1: Create a New Module
Create a module for RDS database
- modules/rds/main.tf
- Support for engine, size, backup settings
- Outputs: endpoint, port, name

### Exercise 2: Add Module Examples
Create `examples/` directory in each module showing usage

### Exercise 3: Implement Module Testing
Write tests using Terratest or kitchen-terraform

### Exercise 4: Version Your Modules
- Tag releases in Git
- Document changes in CHANGELOG.md
- Follow semantic versioning

## Next Steps
- Explore [Terraform Registry](https://registry.terraform.io/)
- Review popular modules for best practices
- Consider contributing to open source modules

## Additional Resources
- [Module Best Practices](https://www.terraform.io/docs/modules/index.html)
- [Module Composition](https://www.terraform.io/docs/modules/composition.html)
- [Terratest](https://terratest.gruntwork.io/)
- [terraform-docs](https://terraform-docs.io/)
