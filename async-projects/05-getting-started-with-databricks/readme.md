# Getting Started with Databricks

During this project we will work with Databricks. We will cover different aspects of this platform and learn key concepts.


## 🧰 Tools & Services

🔥 Apache Spark

Apache Spark is an open-source distributed computing engine designed for big data processing. It's built for speed and ease of use and supports a wide range of data processing tasks like:

- Batch processing
- Streaming
- SQL
- Machine learning
- Graph analytics

Key features:

- Works in memory (much faster than traditional MapReduce)
- Can run on Hadoop, Kubernetes, or standalone
- APIs in Python (PySpark), Scala, Java, R

✅ Use Spark when you need to process large datasets across multiple nodes, especially for ETL, data analysis, or ML.

☁️ Databricks

Databricks is a cloud-based platform built on top of Apache Spark. It simplifies working with big data by offering:

- A collaborative notebook interface (similar to Jupyter, but built for teams and production)
- Optimized Spark runtime (faster than open-source)
- Built-in tools for data engineering, machine learning, and analytics
- Native integrations with cloud storage, Delta Lake, and MLflow

Key features:

- Auto-scaling clusters
- Managed infrastructure
- Delta Lake for ACID transactions on data lakes
- Unity Catalog for governance and security

✅ Use Databricks when you want a production-ready, collaborative environment for building scalable data pipelines, ML models, and analytics dashboards without managing infrastructure manually.

## Week 1: Starting with Databricks Community Edition

### 🎯 Objectives

- Setup Databricks Community Workspace on Azure or AWS
- Connect AWS S3 or Storage account
- Learn about Workspace, Notebooks, Clusters, SQL Interface
- Query, transform and query the data

### 🏗️ Tasks Breakdown

#### 1. Setup Databricks Community Edition

Let's [create](https://login.databricks.com/?dbx_source=CE&intent=CE_SIGN_UP) new Databricks Community edition account. 

Explore tabs:

- Clusters
- Notebooks
- Catalog
- etc.

Cluster is a Virtual Machine and with community edition you have limited compute. Each cluster with have Apache Spark pre-installed. Make sure you create new cluster.

Learn about [DBFS](https://docs.databricks.com/aws/en/dbfs/). It is a storage account (for example AWS S3) connected to your workspace. You can upload any `CSV` or `PARQUET` file you like into it.

#### 2. Work with data with PySpark and Catalog

Create a new notebook and use `spark` commands to read, transform and etc. I.e. PySpark. 

Write result into the DBFS and create a new table in Catalog. Make sure it is `EXTERNAL TABLE` in `PARQUET` format.

Find where spark wrote files and explore them.

Create a new `DELTA` table, using same source but the table should be in `DELAT` format now.

Check if Databrikcs Community Edition supports Unitity Catalog.

#### 3. Use SQL to query your data

Query your data using SQL UI and SQL Warehouse. Check if Serverless Warehosue (Cluster) avialable for you. Check the difference between Serverless and Physical one.

You can also visualize the data. Initially, Databricks aquired Redash (SQL BI similar to Metabase) and call it SQL Analytics.

Next week, we will learn about Medallien Architecture.



