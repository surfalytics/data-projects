# Open Source BI with Metabase

In this project, we will focus on traditional BI use cases using open-source software OSS. Whenever we want to implement a BI solution, we have a choice between free options and costly vendor solutions. Obviously, vendor solutions are often better, faster to implement, and easier to use. However, sometimes budget constraints make open-source BI an appealing option, especially for small companies or startups.

The three most popular open-source BI tools are:

- [Redash OSS](https://www.metabase.com/docs/latest/installation-and-operation/running-metabase-on-docker) (SQL-based development)
- [Metabase OSS](https://redash.io/) (SQL-based development)
- [Apache Superset](https://superset.apache.org/) (Python-based development)

Each of these also offers a managed (cloud) version.

For this project, let's focus on **Metabase**.

Keep in mind - we have several goals:
- Learn Metabase
- Practice Docker and CLI
- Learn about Open Source Software (OSS) use case. You should be able to talk about pros and cons of OSS vs Tableau/Looker/Power BI and think about cool use cases.

## Week 1

Imagine you've joined a startup company. They have a database with some data—possibly our favorite [Superstore dataset on PostgreSQL, either on a local machine or in a Docker container](https://github.com/surfalytics/analytics-course/tree/main/02_getting_started_with_databases/02_connecting_databases) from Module 02.

Your goal is to build a dashboard for Superstore sales using Metabase. Before building anything, we need to ensure that Metabase is installed and running.

There are three options:

## Option 1: Using Java (requires Java 11+)

```
# Download the JAR file
wget https://downloads.metabase.com/v0.47.8/metabase.jar

# Run Metabase
java -jar metabase.jar
```

## Option 2: Using Docker

[Metabase Documentation](https://www.metabase.com/docs/latest/installation-and-operation/running-metabase-on-docker)

```
docker pull metabase/metabase:latest

docker run -d -p 3000:3000 --name metabase metabase/metabase

docker logs -f metabase

# will open on http://localhost:3000.

# To run your Open Source Metabase on a different port, say port 12345:

docker run -d -p 12345:3000 --name metabase metabase/metabase
```

## Option 3: Using Docker Compose

In this case, we are using Postrges DB as a backend for Metabase. This is the prefered method. Same method will work for Production. 

```
version: "3.9"
services:
  metabase:
    image: metabase/metabase:latest
    container_name: metabase
    hostname: metabase
    volumes:
      - /dev/urandom:/dev/random:ro
    ports:
      - 3000:3000
    environment:
      MB_DB_TYPE: postgres
      MB_DB_DBNAME: metabaseappdb
      MB_DB_PORT: 5432
      MB_DB_USER: metabase
      MB_DB_PASS: mysecretpassword
      MB_DB_HOST: postgres
    networks:
      - metanet1
    healthcheck:
      test: curl --fail -I http://localhost:3000/api/health || exit 1
      interval: 15s
      timeout: 5s
      retries: 5
  postgres:
    image: postgres:latest
    container_name: postgres
    hostname: postgres
    environment:
      POSTGRES_USER: metabase
      POSTGRES_DB: metabaseappdb
      POSTGRES_PASSWORD: mysecretpassword
    networks:
      - metanet1
networks:
  metanet1:
    driver: bridge
```

You can decide how it will work. There are options:
- Install Postgres with SuperStore Locally and connect with Metabase in Docker.
- Add Postgres Database into Docker Compose.
- Deploy Postgres in the Cloud such as AWS RDS, or Azure Postgres, or GCP Cloud SQL.

Next week, we will learn about the building SuperStore dashboard in Metabase.

  
