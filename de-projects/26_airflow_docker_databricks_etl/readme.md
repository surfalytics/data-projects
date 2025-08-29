# Airflow ETL Project

## About project

This project showcases an ETL pipeline built using Apache Airflow to retrieve job listing data from the Adzuna API, transform it, and load it into a Databricks delta table. The entire setup runs in Docker, ensuring a consistent and reproducible environment for extracting, transforming, and loading data.

For more details, check https://medium.com/@kazarmax/hands-on-project-building-a-simple-api-to-delta-pipeline-with-airflow-and-databricks-connect-028881ba3585

## Prerequisites

To run this project, you need the following:
 - Adzuna API account at `https://developer.adzuna.com/` with `Application ID` and `Application Key`
 - Databricks Free Edition account `https://www.databricks.com/learn/free-edition`
 - Docker and VS Code installed


## How to Run the Pipeline

1. Clone the project github repo
```
git clone https://github.com/kazarmax/airflow_databricks_etl.git
```

2. Open the project folder in VS Code

3. Run Airflow services in docker

```
docker compose up -d
```

4. Open Airflow UI at `http://localhost:8080/` (login/password: airflow/airflow)

5. In Airflow UI, add and fill in variables `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` using values from your Adzuna API account

6. In your Databricks Free Edition account, create and save securely Personal Access Token (PAT)
* Go to Settings → User Settings → Access Tokens
* Click Generate New Token
* Copy and save it securely

7. In Airflow UI, add a Connection to Databricks: 
* Connection ID = `databricks_default`
* Connection Type = `Databricks`
* Host - take it from your Databricks Free Edition account URL, for example `https://abc123.cloud.databricks.com`
* Password - use your Databricks token

8. Create catalog, schema and table in databricks unity catalog by running the following command in the terminal locally:

```
docker compose exec -T airflow-scheduler python /opt/python/scripts/databricks_ddl.py
```

9. In Airflow UI, open and run the `adzuna_etl_dag` DAG

10. Upon successful execution of the DAG, log in to Databricks and check if the table `adzuna.prj.jobs` exists and contains data.
