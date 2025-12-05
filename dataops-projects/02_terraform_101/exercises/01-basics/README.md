# Exercise 1: Terraform Basics

## Goal
Learn the fundamental concepts of Terraform using local providers (no cloud account needed).

## What You'll Learn
- Resource creation and dependencies
- Variables and their types
- Outputs
- Local values
- Meta-arguments (count, for_each)
- Conditional resources

## Prerequisites
- Terraform installed (>= 1.0)
- Text editor
- Terminal/Command line

## Instructions

### Step 1: Initialize Terraform
```bash
cd exercises/01-basics
terraform init
```

This downloads the required providers (local and random).

### Step 2: Review the Code
Open and read through the files in order:
1. **providers.tf** - Defines required Terraform version and providers
2. **variables.tf** - Input variables with different types
3. **main.tf** - Resource definitions with detailed examples
4. **outputs.tf** - Output values to display after applying

### Step 3: Validate Configuration
```bash
terraform validate
```

### Step 4: Plan the Changes
```bash
terraform plan
```

Review what Terraform will create. Notice:
- How many resources will be created?
- What are their names?
- What dependencies exist?

### Step 5: Apply the Configuration
```bash
terraform apply
```

Type `yes` when prompted.

### Step 6: Explore the Results
```bash
# View all outputs
terraform output

# View specific output
terraform output random_suffix

# View as JSON
terraform output -json

# Check created files
ls -la output/
cat output/example-*.txt
```

### Step 7: Modify and Re-apply
Try making changes:

**Change 1: Modify Environment**
```bash
terraform apply -var="environment=staging"
```

Notice what changes? Which resources get recreated?

**Change 2: Add More Files**
Edit `main.tf` and change line with `count = 3` to `count = 5`

```bash
terraform plan
terraform apply
```

How many new files will be created?

### Step 8: View State
```bash
# List all resources in state
terraform state list

# Show details of a specific resource
terraform state show random_string.suffix

# Show entire state
terraform show
```

### Step 9: Clean Up
```bash
terraform destroy
```

Type `yes` to confirm.

## Key Concepts Demonstrated

### 1. Resource Dependencies
In `main.tf`, the `local_file.example` resource references `random_string.suffix.result`. Terraform automatically determines the correct order to create these resources.

### 2. Variable Types
- **string**: `var.environment`, `var.project_name`
- **map**: `var.tags`
- **number**: `var.instance_count`
- **bool**: `var.enable_monitoring`

### 3. Meta-Arguments
- **count**: Creates multiple similar resources (0-indexed)
- **for_each**: Creates resources from a map or set (keyed by name)

### 4. Local Values
The `locals` block computes values once and reuses them:
```hcl
local.resource_prefix = "terraform-101-dev"
```

### 5. Outputs
Export values to:
- Display to users
- Use in other Terraform configurations
- Pass to CI/CD pipelines

## Challenges

Try these exercises to reinforce learning:

### Challenge 1: Add a New Variable
1. Add a new variable `owner_email` in `variables.tf`
2. Add it to the `common_tags` local
3. Apply and verify in outputs

### Challenge 2: Conditional Logic
1. Create a resource that only exists in "prod" environment
2. Test with different environment values

### Challenge 3: For Expression
1. Add an output that lists all file IDs using a for expression
2. Create a map output with filename as key and content as value

## Common Issues

### Issue: Provider not found
**Solution**: Run `terraform init`

### Issue: Resource already exists
**Solution**: Check your state file or run `terraform refresh`

### Issue: Count cannot be computed
**Solution**: Count must be known at plan time; use static values or simple conditions

## Next Steps
Once comfortable with these basics, move to:
- **Exercise 2**: Simple AWS resources
- Learn how to create real cloud infrastructure

## Additional Resources
- [Terraform Language Documentation](https://www.terraform.io/language)
- [Resource Meta-Arguments](https://www.terraform.io/language/meta-arguments/count)
- [Built-in Functions](https://www.terraform.io/language/functions)
