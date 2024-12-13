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

Let's try to test everything locally.  We would need to unstall DuckDB.

Using terminal, we can 

```bash
cd dataops-projects/01_git_and_ci_cd 
```

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
### Creating PR for Code Reivew



```bash
# create the branch
git checkout -b feature/covid-analysis

# git status
git status
```

```bash

```


## Materials



All discussions and weekly meetings will be in the Discord channel - **data-engineering-projects**.a