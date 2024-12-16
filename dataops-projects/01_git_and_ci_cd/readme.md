# Getting started with Git and CI/CD

## Objective

During this project we want to better understand DevOps concepts for Data Analytics and Data Engineering. We will use term DataOps for this purpose.

## Key Terms

- DataOps - Short for Data Operations. A set of practices combining DevOps, Agile, and Lean methodologies tailored for data analytics and engineering workflows.

Key elements of DataOps include:

1. Automation: Streamlining repetitive tasks like data ingestion, transformation, and testing.
2. Collaboration: Encouraging cross-team collaboration between data engineers, analysts, and operations teams.
3. Version Control: Using tools like Git for versioning data pipelines, queries, and models.
4. CI/CD for Data Pipelines: Automating deployment and testing of changes in data workflows.
5. Monitoring and Observability: Tracking data quality, pipeline performance, and analytics reliability.
6. Agile Methodologies: Iterative development, faster delivery, and feedback loops for continuous improvement.

- CI/CD - Short for Continuous Integration/Continuous Deployment. Automates testing, integration, and deployment of code and data pipelines for faster and safer releases.
- Observability - Practice of monitoring, tracking, and logging data pipeline health, performance, and errors.
- Data Quality - Accuracy, consistency, and reliability of data throughout its lifecycle.
- IaC - Infrastructure as Code: Managing infrastructure (e.g., servers, databases) using code (e.g., Terraform, CloudFormation).
- Version Control - Tracking changes to code, configurations, or data models over time (e.g., Git).

Some metrics:

- DORA Metrics - Used to assess DevOps/DataOps efficiency:
  - Deployment Frequency
  - Lead Time for Changes
  - Mean Time to Restore
  - Change Failure Rate
- SLA/SLO/SLI - Service-Level Agreement/Objective/Indicator: Terms for defining and measuring data system reliability and performance.
- MTTD / MTTR - Mean Time to Detect / Mean Time to Resolve: Metrics for identifying and fixing data pipeline issues.
- TCO - Total Cost of Ownership: Measuring the overall cost of maintaining a data system.

## Prerequisites

- [DuckDB basics]()
- [GitHub basics]()
- [Docker basics]()
- [CLI basics]()

## Implementation

### Local development

Let's try to test everything locally.  We would need to install DuckDB.

Using terminal, we can go into the folder:

```bash
cd dataops-projects/01_git_and_ci_cd
```

> Ideally we should create a new repo in GitHub and place conten of the `01_git_and_ci_cd ` folder into the repo. Got to github, create new repo and copy files into the repo.

Make sure we have duckdb

```bash
duckdb --version
v1.1.3 19864453f7
```

If now, we can [download](https://duckdb.org/docs/installation/).

Let's download the file:

```bash
wget -O "./covid_data.csv" "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"
```

Start duckdb with external database `analysis.db`

```bash
duckdb analysis.db
```
Run commands in SQL

```sql
-- Import CSV data
IMPORT FROM 'covid_data.csv';

-- Basic analysis queries
CREATE TABLE covid_data AS SELECT * FROM read_csv_auto('covid_data.csv');

-- Total cases and deaths by location
CREATE VIEW location_summary AS
SELECT
    location,
    MAX(total_cases) as max_total_cases,
    MAX(total_deaths) as max_total_deaths,
    MAX(total_cases_per_million) as max_cases_per_million
FROM covid_data
WHERE continent IS NOT NULL
GROUP BY location
ORDER BY max_total_cases DESC
LIMIT 20;

-- Output results to CSV
COPY (SELECT * FROM location_summary)
TO './top_20_locations.csv'
WITH (HEADER, DELIMITER ',');

-- Generate some statistics
SELECT
    COUNT(DISTINCT location) as total_locations,
    MIN(date) as earliest_date,
    MAX(date) as latest_date
FROM covid_data
WHERE continent IS NOT NULL;
```

Clean up the files.

### Running Similar in Docker Container

```bash
# build container
docker build -t duckdb-data-analysis -f .docker/Dockerfile .

# start container and run program
docker run -it --rm duckdb-data-analysis
# start bash in container
#docker run -it --rm duckdb-data-analysis bash
```
We can add make file

```bash
touch make
```

```bash
# Define ANSI color codes
YELLOW = \033[1;33m
GREEN = \033[1;32m
RESET = \033[0m

# Target to build the Docker container
.PHONY: build
build:
	@echo "$(YELLOW)Building the Docker container...$(RESET)"
	docker build -t duckdb-data-analysis -f .docker/Dockerfile .
	@echo "$(GREEN)Build completed successfully!$(RESET)"

# Target to run the Docker container
.PHONY: run
run:
	@echo "$(YELLOW)Starting the Docker container...$(RESET)"
	docker run -it --rm duckdb-data-analysis
	@echo "$(GREEN)Program executed successfully!$(RESET)"

# Target to display help
.PHONY: help
help:
	@echo "$(YELLOW)Available commands:$(RESET)"
	@echo "  $(GREEN)make build$(RESET) - Build the Docker container."
	@echo "  $(GREEN)make run$(RESET)   - Start the Docker container and run the program."
```

> In a Makefile, .PHONY is a special target that marks other targets as “phony.” A phony target is not associated with any actual file; instead, it serves as a label for commands to execute. Declaring a target as .PHONY tells make that this target does not represent a file and should always run the associated commands, regardless of whether a file with the same name exists in the directory.

### Creating PR for Code Reivew

Let's start from adding the PR template in the root folder of repo

```bash
touch pull_request_template.md
```

PR template

```yaml
# Description of change

# Links

# Testing

# Before Merge

---
# Diligence

- [ ] I have checked affected models for appropriate tests and metadata
- [ ] Project has been built locally
- [ ] Project has been tested locally
- [ ] Each model has YAML file with model description, tests
- [ ] dbt CI pass
```

```bash
# create the branch
git checkout -b feature/covid-analysis

# git status
git status

git add .

git commit -m "Docker container"

git push --set-upstream origin feature/covid-analysis
```

We can review and merge.

We just used Git system, and we have **code version** anf **code review**.

## Enforce local code quality

Let's add pre-commit to enforce the quality of SQL, YAML files.

```bash
pip3 install pre-commit sqlfmt
```

Adding file `.pre-commit-config.yaml`


```yaml
# Pre-commit that runs locally
fail_fast: false

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: check-yaml

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        files: '\.(yaml|yml)$'

  # SQL Formatter (sqlfmt)
  - repo: https://github.com/tconbeer/sqlfmt
    rev: v0.24.0
    hooks:
      - id: sqlfmt
        name: sqlfmt
        entry: sqlfmt
        language: python
        files: \.sql$
```

> you can review version by checking release

Install pre-commit from repo root folder

```bash
pre-commit install

#result
pre-commit installed at .git/hooks/pre-commit
```

We can run manually `pre-commit run --all-files`. Ideally it should be run when we do `git commit`.

Example:

```bash
git commit -m "Adding more files"
trim trailing whitespace.................................................Passed
check yaml...............................................................Passed
prettier.................................................................Failed
- hook id: prettier
- files were modified by this hook

sqlfmt...................................................................Failed
- hook id: sqlfmt
- files were modified by this hook

1 file formatted.
0 files left unchanged.
dataops-projects/01_git_and_ci_cd/queries/analysis.sql formatted.
```

## Enforce the quality in GitHub with Continius Integration

Now we want to make sure it is working remote. We should run same checks as soon as code is pushing to the remote.

```bash
touch .github/workflows/pre-commit.yml
```

GitHub Actions pipeline

```yaml
name: Run Pre-commit Hooks

on:
  pull_request:
    branches:
      - main
  push:
    branches:
      - main

jobs:
  pre-commit:
    runs-on: ubuntu-latest

    steps:
      # Checkout the code and fetch all branches
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0 # Ensure the full history is fetched, not just the last commit

      # Set up Python environment
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      # Install dependencies and pre-commit hooks
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pre-commit

      # Fetch the main branch to ensure it's available for comparison
      - name: Fetch main branch
        run: git fetch origin main

      # Run pre-commit hooks
      - name: Run pre-commit hooks
        run: |
          # Show pre-commit version
          pre-commit --version

      # Run pre-commit on all files changed between the current branch and main
      - name: Run pre-commit on all changed files
        run: |
          # Get the list of files changed between the current branch and main
          files=$(git diff --name-only origin/main)
          if [ -n "$files" ]; then
            pre-commit run --files $files
          else
            echo "No modified files to check."
          fi
```

It shoudl run pre-commit for all files in branch on every push.

We can also add the INTEGRATION test to make sure the result is matching. We would need to add another workflow:

> 	Integration Test: Tests how multiple components (e.g., your script, the DuckDB engine, and Docker) work together. Ensures that the entire pipeline produces the expected result.

> Unit tests are designed to test small, isolated pieces of code (like functions or methods) in isolation, without involving external systems or environments. They ensure that individual components of your application work as expected.

```yaml
name: Verify DuckDB Output

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  verify-duckdb:
    runs-on: ubuntu-latest

    steps:
      # Checkout the code
      - name: Checkout code
        uses: actions/checkout@v4

      # Build the Docker container (USE YOUR PATH)
      - name: Build Docker Image
        run: |
          docker build -t duckdb-data-analysis -f .docker/Dockerfile .

      # Run the Docker container and capture the output
      - name: Run Docker Container
        id: run-container
        run: |
          # Run the container and capture output to a file
          docker run --rm duckdb-data-analysis > output.txt
          # Print the captured output
          cat output.txt

      # Verify the output matches the expected result
      - name: Verify DuckDB Output
        run: |
          # Define the expected output
            expected_output="│ total_locations │ earliest_date │ latest_date │
          │      int64      │     date      │    date     │
          ├─────────────────┼───────────────┼─────────────┤
          │             243 │ 2020-01-01    │ 2024-08-14  │
          └─────────────────┴───────────────┴─────────────┘"

            # Compare the actual output with the expected output
            actual_output=$(cat output.txt | grep -A4 "total_locations")
            if [ "$actual_output" = "$expected_output" ]; then
              echo "Output matches expected values."
            else
              echo "Output does not match expected values!"
              echo "Actual output:"
              echo "$actual_output"
              echo "Expected output:"
              echo "$expected_output"
              exit 1
            fi
```


## Deploy the image with Continius Deployment


## Cut a Release