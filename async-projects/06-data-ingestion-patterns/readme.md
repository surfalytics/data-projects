# Data Ingestion Patterns: From API to Snowflake

A comprehensive 6-week project exploring multiple data ingestion approaches using GitHub API as the data source and Snowflake as the target data warehouse.

## Project Overview

Goal: Load data into Snowflake using multiple approaches and understand different data ingestion patterns.

Duration: 6 weeks (core) + 2 optional weeks (Airflow orchestration)

Data Source: GitHub API (free tier)
Target: Snowflake (6-month free trial)
Cloud Platform: AWS (free tier)

## Prerequisites

- ✅ AWS account
- ✅ VSCode
- ✅ GitHub account
- ⏳ [Snowflake trial account](https://www.coursera.org/professional-certificates/snowflake-generative-ai) (6 months free via Coursera).
- ⏳ Docker container

You would need AWS and Snowflake starting week 3.

> Tip: Use Claude Code or Cursor to accelerate development. They can help with AWS CLI commands to create roles, resources, and more.

> Tip: If CLI, IDE, Github and Docker are new for you. Please check [Surfalytics Module 0](https://www.youtube.com/watch?v=LJIiCLu2gr8&list=PLNCDg7zJiXhP5Z_-TXUdorz2n7sjYHHKE&index=1)

## Architecture Overview

![Data Ingestion Architecture](https://placehold.co/800x400/4A90E2/FFFFFF/png?text=Data+Ingestion+Architecture)

*Create your own architecture diagram using [draw.io](http://draw.io), [Excalidraw](https://excalidraw.com/), or similar tools*

## Data Source Definition

Source: GitHub API
- Endpoint: `https://api.github.com/repositories`
- Data Type: JSON
- Purpose: Repository metadata including stars, language, creation date, etc.

Sample Data Structure:

```json
{
  "id": 1,
  "name": "grit",
  "full_name": "mojombo/grit",
  "html_url": "https://github.com/mojombo/grit",
  "description": "Grit is no longer maintained",
  "stargazers_count": 2000,
  "language": "Ruby",
  "created_at": "2007-10-29T14:37:16Z",
  "updated_at": "2023-01-02T15:21:22Z"
}
```

### What is API? (For Complete Beginners)

What is an API?

Imagine you want to order pizza, but you don't know how to cook. You call the pizza place and say "I want a large pepperoni pizza." The person on the phone takes your order and brings you the pizza. You don't need to know how to make pizza or go into their kitchen!

That's exactly what an API is:
- You: "I want data about GitHub repositories"
- API: "Here's the data you asked for!"
- You: Get nice, clean data in JSON without knowing how it's stored

Why do we use APIs instead of going directly to databases?

Think of it like this:

🏠 Direct Database Access = Breaking into someone's house
- You need special keys and passwords
- You might break something
- You could see private stuff you shouldn't
- It's complicated and scary

🚪 API = Knocking on the door politely
- You just ask for what you need
- They give you only what you're allowed to see
- It's safe and easy
- You don't need special keys

Real-world example:
- ❌ Bad way: Try to hack into GitHub's computers to get data
- ✅ Good way: Use GitHub's API to ask for data nicely

Bottom line: APIs are like having a helpful friend who goes and gets data for you, so you don't have to figure out how to do it yourself!

## Business Questions to Answer

- What is the total number of repositories on GitHub?
- What are the top 10 most-starred repositories on GitHub?
- What are the most popular repositories for a specific programming language (e.g., Python, JavaScript)?
- How many public repositories and accounts does a specific user or organization have?
- What are the trending repositories by creation date?
- Which programming languages are most popular over time?

## Implementation Approaches

### Implementation 1: Local Python + AWS S3 (CSV)
- Week 1: Local IDE with Python requests library
- Week 2: Docker containerization

### Implementation 2: AWS Lambda + S3 (CSV)
- Week 3: Serverless data extraction

### Implementation 3: AWS Lambda + S3 (Polars/DuckDB)
- Week 4: Enhanced data processing with modern Python libraries

### Implementation 4: AWS Lambda + Snowflake
- Week 5: Direct data warehouse integration

### Implementation 5: AWS Batch + Step Functions
- Week 6: Scheduled batch processing

### Implementation 6: AWS Glue + Athena
- Week 6: Data lake approach with PySpark

### Implementation 7: Fivetran (No-Code)
- Week 6: Managed data integration platform

### Implementation 8: Using Airflow for Orchestration
- Week 7: Using local Airflow to run the Python code
- Week 8: Using managed Airflow to run 

---

## Week 1: Local Python Development

### Goals
- Set up all required accounts and services
- Create GitHub repository for the project
- Develop local Python script to extract GitHub API data
- Upload data to AWS S3 in CSV format

### Prerequisites Setup

1. Snowflake Account Setup
   - Sign up for Snowflake trial account
   - Complete Coursera course for 6-month free trial
   - Note down connection details

2. AWS Account Setup
   - Create AWS account if not already done
   - Set up IAM user with S3 permissions
   - Create S3 bucket for data storage
   - Configure AWS CLI locally

3. GitHub Repository Setup
   - Create new repository: `data-ingestion-github-to-snowflake`
   - Initialize with README.md
   - Set up proper branch structure (main, develop)

### Development Tasks

1. Create Python Environment

> Tip: [What is VENV?](https://realpython.com/python-virtual-environments-a-primer/). We want to have Virtual Environment to avoid packages mess on our local machine and we can share dependencies with others. Alternatives for VENV are Poetry (very popular), uv (fastest) and etc.
   
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install requests boto3 pandas
   ```

2. Create Requirements File

What this does: It's like a shopping list that tells your computer exactly which Python libraries (tools) it needs to install.

What you need to do:
- Create a file called "requirements.txt" in your project folder
- List all the Python libraries you need:
  - requests (for talking to GitHub API)
  - boto3 (for talking to AWS)
  - pandas (for working with data)
- After installing packages, run: `pip freeze > requirements.txt` to automatically create the file

Think of it like this: It's like giving someone a shopping list so they can buy all the ingredients you need to cook a specific recipe.

3. Develop Data Extraction Script
   - Create `src/extract_github_data.py`
   - Implement GitHub API calls with pagination
   - Handle rate limiting (60 requests/hour for unauthenticated)
   - Add error handling and logging

4. Create S3 Upload Functionality
   - Implement S3 upload with proper naming convention
   - Add data validation before upload
   - Create timestamped file names

5. Data Quality Checks
   - Validate JSON structure
   - Check for required fields
   - Implement basic data quality rules

### Deliverables
- [ ] GitHub repository with proper structure
- [ ] Python script that extracts GitHub repository data
- [ ] S3 bucket with sample CSV files
- [ ] Documentation of API rate limits and data structure
- [ ] Basic error handling and logging

### Success Criteria
- Successfully extract 1000+ GitHub repositories
- Upload data to S3 in CSV format
- Handle API rate limiting gracefully
- Document all steps and findings

## Week 2: Docker Containerization

### Goals
- Containerize the Python application
- Create reproducible environment
- Set up requirements.txt and Dockerfile
- Test containerized data extraction

### Development Tasks

1. Update Requirements File

What you need to do:
- Update your existing "requirements.txt" from Week 1
- Add `python-dotenv` to the list for managing environment variables securely
- Your final requirements.txt should include:
  - requests
  - boto3
  - pandas
  - python-dotenv

> Tip: Run `pip install python-dotenv` and then `pip freeze > requirements.txt` to update the file with exact versions.

2. Create Dockerfile

What Dockerfile does: It's like a recipe that tells Docker how to build a container with everything your program needs to run.

What you need to do:
- Create a file called "Dockerfile"
- Tell it to use Python 3.11 as the base
- Set up a working directory called "app"
- Copy your requirements.txt file
- Install all the Python libraries from requirements.txt
- Copy your Python code into the container
- Tell it what command to run when the container starts

Think of it like this: It's like writing instructions for someone to build a complete kitchen with all the tools and ingredients needed to cook your specific dish, then package it all up in a box.

3. Environment Configuration
   - Create `.env` file for sensitive data
   - Add `.env` to `.gitignore`
   - Create `.env.example` template

4. Docker Commands

What these commands do: They tell Docker to build your container and run your program inside it.

What you need to do:
- Build your container: `docker build -t github-data-extractor .`
  - This creates a container image with your program and all its dependencies
- Run your container: `docker run --env-file .env github-data-extractor`
  - This starts your container and runs your data extraction program
- Debug mode: `docker run -it --env-file .env github-data-extractor bash`
  - This lets you go inside the container to troubleshoot if something goes wrong

Think of it like this: Building is like constructing a house, running is like moving in and living there, and debug mode is like being able to walk around inside the house to see what's happening.

### Deliverables
- [ ] Dockerfile and requirements.txt
- [ ] Environment configuration files
- [ ] Containerized application working locally
- [ ] Documentation for running the container

### Success Criteria
- Container runs successfully with environment variables
- Data extraction works in containerized environment
- Easy to reproduce and share the setup

---

## Learning Outcomes  of the project

By the end of this project, you will understand:

1. Data Ingestion Patterns: Multiple approaches to move data from APIs to data warehouses
2. Cloud Services: AWS Lambda, S3, Glue, Batch, Step Functions
3. Modern Data Tools: Polars, DuckDB, PySpark
4. Data Warehousing: Snowflake integration and best practices
5. Containerization: Docker for reproducible environments
6. Orchestration: Workflow management and scheduling
7. No-Code Solutions: Fivetran and managed services
8. Performance Optimization: Comparing different approaches
9. Cost Management: Understanding trade-offs between solutions
10. Production Readiness: Error handling, monitoring, and scalability

---

## Resources and References

### Documentation
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [Polars Documentation](https://pola.rs/)
- [DuckDB Documentation](https://duckdb.org/docs/)

### Tools and Services
- [AWS Free Tier](https://aws.amazon.com/free/)
- [Snowflake Free Trial](https://signup.snowflake.com/)
- [Fivetran Free Trial](https://fivetran.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Learning Resources
- [AWS Data Engineering Learning Path](https://aws.amazon.com/training/learning-paths/data-engineering/)
- [Snowflake Learning Resources](https://learn.snowflake.com/)

---