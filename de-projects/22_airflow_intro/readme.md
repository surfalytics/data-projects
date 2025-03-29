# Getting started with Airflow

## Prerequisites
For working on the project, everyone needs the following things installed / available before the webinar:
 
- Python
- VS Code
- Docker Desktop

## Instructions

1. Download the repo and open it in VS Code

2. Navigate to the `/data-projects/de-projects/22_airflow_intro/` project folder

3. Run docker compose

```bash
docker compose up -d
```

4. Verify successful setup

```bash
docker compose ps -a
```

5. Open Airflow UI at http://localhost:8080/ 

6. Run all dags


## Useful commands

View airflow logs for all services

```bash
docker compose logs
```

View airflow logs for specific service

```bash
docker compose logs airflow-webserver
```

View airflow logs for all services in real time (live streaming)

```bash
docker compose logs airflow-webserver -f
```

Log in to container running airflow service

```bash
docker compose exec -it airflow-webserver bash
```

Shut down all services

```bash
docker compose down
```

## Useful materials
 
 - ["Getting Started with Apache Airflow" article](https://medium.com/@kazarmax/getting-started-with-apache-airflow-b2fba7dbd45a)

 - ["ETL with Airflow" project](https://medium.com/@kazarmax/extracting-and-processing-job-market-data-etl-with-apache-airflow-and-adzuna-api-d7feae752bf9)
