# Typical Data Warehouse on Azure

This project simulates a typical data warehouse architecture using Azure services as the source systems and Snowflake as the target cloud data warehouse. The goal is to incrementally build a modern data platform by following weekly tasks.

## 🧰 Tools & Services

We will use:
- Azure Cloud
    - Azure Data Factory (orchestration tool)
    - Azure SQL (relational database)
    - CosmosDB (NoSQL database)
    - Blob Storage (intermediate file storage)
    - Synapse Analytics (CosmosDB analytics layer)
    - Azure Bicep (infrastructure as a code)
    - Azure DevOps (Repos and Pipelines)
    - Azure Key Vault (Secrets)
    - Azure Log Analytics (Data Observability)
    - Azure Purview
- Snowflake (data warehouse)
- Snowflake Stored Procedures

## Week 1: Initial Setup and Data Ingestion from Azure SQL to Snowflake

### 🎯 Objectives

- Set up the foundational infrastructure on Azure and Snowflake.
- Create and populate source tables in **Azure SQL Database**.
- Configure **Azure Data Factory (ADF)** to perform a **COPY** activity from Azure SQL to Snowflake.
- Perform an initial data load into `raw.azure_sql.orders`.

### 🏗️ Tasks Breakdown

#### 1. Azure Environment Setup

- Create an **Azure Resource Group**.
- Create an **Azure SQL Database** (and SQL Server).
- Create **Azure Key Vault** to securely store credentials.
- Create **Azure Blob Storage** (used by ADF for staging).
- Create **Azure Data Factory**.

Please use the [Azure Naming Convention](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming).

#### 2. Snowflake Environment

- Set up a **Snowflake Trial Account** (if you don’t have one). You can get up to 6 months of a Trial using [Coursera](https://www.coursera.org/learn/intro-generative-ai-course-snowflake).
- Create the target database and schema:

```sql
CREATE DATABASE IF NOT EXISTS RAW;
CREATE SCHEMA IF NOT EXISTS RAW.azure_sql;
```


####  3. Source Tables in Azure SQL

Create the following tables in Azure SQL. Use sample data (approx. 20 rows per table). Ensure orders contains diverse updated_at values to simulate data updates.


Customers
```sql
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    created_at DATETIME
);
```

Products
```sql
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10,2),
    created_at DATETIME
);
```

Orders

```sql
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    product_id INT,
    quantity INT,
    total_price DECIMAL(10,2),
    created_at DATETIME,
    updated_at DATETIME
);
```

#### 4. Insert sample data manually or via script. The orders table should have a variety of timestamps for testing future incremental ingestion.


```sql
INSERT INTO customers (customer_id, name, email, created_at) VALUES
(1, 'Alice Johnson', 'alice.j@example.com', '2023-01-10 08:23:45'),
(2, 'Bob Smith', 'bob.smith@example.com', '2023-01-12 14:11:09'),
(3, 'Charlie Davis', 'charlie.d@example.com', '2023-01-15 09:37:22'),
(4, 'Diana Cruz', 'diana.c@example.com', '2023-02-01 17:02:18'),
(5, 'Ethan Lee', 'ethan.l@example.com', '2023-02-10 11:45:30');


INSERT INTO products (product_id, name, category, price, created_at) VALUES
(101, 'Laptop Pro 15"', 'Electronics', 1499.99, '2023-01-01 10:05:10'),
(102, 'Wireless Mouse', 'Accessories', 29.99, '2023-01-03 15:25:40'),
(103, 'Noise Cancelling Headphones', 'Electronics', 199.95, '2023-01-05 12:14:50'),
(104, 'Office Desk', 'Furniture', 299.99, '2023-01-08 09:09:09'),
(105, 'LED Monitor 24"', 'Electronics', 159.99, '2023-01-09 18:30:00');


INSERT INTO orders (order_id, customer_id, product_id, quantity, total_price, created_at, updated_at) VALUES
(1001, 1, 101, 1, 1499.99, '2023-01-11 10:15:23', '2023-01-11 12:45:30'),
(1002, 2, 102, 2, 59.98, '2023-01-13 08:20:40', '2023-01-15 09:10:15'),
(1003, 3, 103, 1, 199.95, '2023-01-16 14:50:10', '2023-01-18 16:22:55'),
(1004, 4, 104, 1, 299.99, '2023-02-02 13:14:00', '2023-02-02 13:14:00'),
(1005, 5, 105, 2, 319.98, '2023-02-12 11:11:11', '2023-02-14 15:01:20'),
(1006, 1, 102, 3, 89.97, '2023-03-01 07:07:07', '2023-03-04 08:08:08');
```

#### 4. Prepare ADF

In Azure Data Factory, configure the following linked services:

- Azure SQL DB (credentials from Key Vault)
- Azure Blob Storage
- Snowflake (credentials from Key Vault)

Create a new ADF Pipeline that includes:

- Source: Azure SQL orders table (create a Data Set)
- Sink: Snowflake `raw.azure_sql.orders` table (create a Data Set)

Use the Copy Data activity to move data from SQL Server to Snowflake. It means we did a Full Reload (Load) of the data.

Use Blob Storage as intermediate staging in the Copy Activity. 

## Week 2: Planning and Building an Incremental ETL Process

### 🎯 Goals

- Prepare for incremental data ingestion from Azure SQL to Snowflake.
- Create **temporary (staging)** tables and **final** tables with audit columns.
- Create a **WATERMARK** table to track the last loaded timestamps.
- Prepare for **idempotent** ETL using ADF and Snowflake Stored Procedures.

---

### 🏗️ Tasks Breakdown

#### 1. Create Snowflake Tables for Incremental Processing

For each of the 3 source tables (`orders`, `customers`, `products`), create:

- **TMP tables**: raw ingestion (always truncated and reloaded).
- **Final tables**: hold production-level clean data + ETL metadata.

---

#### 2. Table Structure

Example for Orders:

##### TMP Table (`raw.azure_sql.tmp_orders`)

```sql
CREATE OR REPLACE TABLE raw.azure_sql.tmp_orders (
    order_id INT,
    customer_id INT,
    product_id INT,
    quantity INT,
    total_price DECIMAL(10,2),
    created_at DATETIME,
    updated_at DATETIME
);


CREATE OR REPLACE TABLE raw.azure_sql.orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    product_id INT,
    quantity INT,
    total_price DECIMAL(10,2),
    created_at DATETIME,
    updated_at DATETIME,
    etl_timestamp_utc TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);
```

> Note: The etl_timestamp_utc column will automatically populate when inserting or merging data.

Repeat the same pattern for customers and products.

#### 3. Create WATERMARK table and CONFIG schema


```sql
CREATE OR REPLACE TABLE raw.config.watermark (
    pipeline_name STRING,
    schema_name STRING,
    table_name STRING,
    last_created_at TIMESTAMP_NTZ,
    last_updated_at TIMESTAMP_NTZ,
    pipeline_start_ts TIMESTAMP_NTZ,
    pipeline_end_ts TIMESTAMP_NTZ,
    source STRING,
    target STRING
);
```

Also, we need a Stored Procedure to update this table:

```sql
CREATE OR REPLACE PROCEDURE raw.config.sp_insert_watermark(
    p_pipeline_name STRING,
    p_schema_name STRING,
    p_table_name STRING,
    p_last_created_at TIMESTAMP_NTZ,
    p_last_updated_at TIMESTAMP_NTZ,
    p_pipeline_start_ts TIMESTAMP_NTZ,
    p_pipeline_end_ts TIMESTAMP_NTZ,
    p_source STRING,
    p_target STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
    INSERT INTO raw.config.watermark (
        pipeline_name,
        schema_name,
        table_name,
        last_created_at,
        last_updated_at,
        pipeline_start_ts,
        pipeline_end_ts,
        source,
        target
    )
    VALUES (
        p_pipeline_name,
        p_schema_name,
        p_table_name,
        p_last_created_at,
        p_last_updated_at,
        p_pipeline_start_ts,
        p_pipeline_end_ts,
        p_source,
        p_target
    );
    
    RETURN 'WATERMARK INSERTED SUCCESSFULLY';
$$;
```



#### 4. Snowflake Stored Procedure

Assume our pipeline will extract data from the source table in Azure SQL and save the result into the TMP table in Snowflake. Our goal is to extract only the newest records, and that's why we want to store our increment in TMP table. 
Next, we will MERGE TMP table (fresh records) into the historical table. To automate this process we will use Stored Procedure. This is a kind of fucntion that will run our SQL logic.

Example of stored procedure DDL:

```sql
CREATE OR REPLACE PROCEDURE raw.azure_sql.sp_merge_orders()
RETURNS STRING
LANGUAGE SQL
AS
$$
MERGE INTO raw.azure_sql.orders AS target
USING raw.azure_sql.tmp_orders AS source
ON target.order_id = source.order_id
WHEN MATCHED THEN
    UPDATE SET 
        customer_id = source.customer_id,
        product_id = source.product_id,
        quantity = source.quantity,
        total_price = source.total_price,
        created_at = source.created_at,
        updated_at = source.updated_at,
        etl_timestamp_utc = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (
        order_id,
        customer_id,
        product_id,
        quantity,
        total_price,
        created_at,
        updated_at,
        etl_timestamp_utc
    )
    VALUES (
        source.order_id,
        source.customer_id,
        source.product_id,
        source.quantity,
        source.total_price,
        source.created_at,
        source.updated_at,
        CURRENT_TIMESTAMP()
    );
$$;
```

To run this, you can run 

```sql
CALL raw.azure_sql.sp_merge_orders()
```

We can even use Snowflake to schedule this Stored Procedure.

Repeat similar stored procedures for `customers` and `products`.

The most important part of a Stored Procedure in our case is the Unique Key which is a Primary Key for each table. Alternative option for the Incremental load is `DELETE+INSERT`, which is great for Event-based tables that never change in the past. In our case, we have to use `MERGE` because our orders could be changed in the past (`updated` timestamp will signal it)

#### 5. High-level design of the incremental pipeline

We have almost all the building blocks, and next we should put this into the Azure Data Factory Pipeline. 

The high-level pipeline will consist of:
1. Activity to get the last timestamp(s) for our table/pipeline from the WATERMARK table and save it into an ADF variable
2. Copy the command to query Azure SQL with `WHERE` condition that will query only fresh data to avoid querying the full table. It will save result into `TMP_` snwoflake table. Make sure it runs  `TRUNCATE TABLE` for `TMP` table. You may notice that ADF is saving data into a Blob and then runs the `COPY` command to save data to Snowflake.
3. Execute Snowflake Stored procedure that will run `MERGE`
4. Activity to get the last timestamp(s) after `MERGE` and assign them to ADF variables.
5. Execute Snowflake Stored procedure to insert the values about the most recent pipeline run. Example of command:

```sql
CALL raw.config.sp_insert_watermark(
    'orders_pipeline',
    'raw.azure_sql',
    'orders',
    '2023-01-15 00:00:00',
    '2023-01-18 00:00:00',
    CURRENT_TIMESTAMP(),
    CURRENT_TIMESTAMP(),
    'azure_sql',
    'snowflake_raw'
);
```

But we will use ADF variables. The idea is to use variables/parameters as much as possible in our pipeline to avoid manually copy-paste it. Think about ADF pipeline name, activity name and everything else to make it reusable as much as possible to follow DRY (do not repeat) principles. 

#### 6. Debug Pipeline

In ADF, we can test the pipeline.

1. Make sure new tables are empty.
2. Let's make a first record for `orders` table in `watermark` table:
```sql
INSERT INTO raw.config.watermark (
    pipeline_name,
    schema_name,
    table_name,
    last_created_at,
    last_updated_at,
    pipeline_start_ts,
    pipeline_end_ts,
    source,
    target
)
VALUES (
    'orders_pipeline',
    'raw.azure_sql',
    'orders',
    '2000-01-15 00:00:00', -- Example last_created_at
    '2000-01-18 00:00:00', -- Example last_updated_at
    CURRENT_TIMESTAMP(),   -- pipeline_start_ts (can also use exact timestamp if needed)
    CURRENT_TIMESTAMP(),   -- pipeline_end_ts
    'azure_sql',
    'snowflake'
);
```
3. Run the pipeline and fix the problems on the go.
4. Let's add more records to Azure SQL and then run the pipeline, it should add these new rows into Snowfalke table and update Watermark table.
```sql
INSERT INTO orders (order_id, customer_id, product_id, quantity, total_price, created_at, updated_at) VALUES
(1017, 6, 106, 1, 499.99, '2023-03-06 10:10:10', '2023-03-06 10:12:15'),
(1018, 7, 107, 2, 159.98, '2023-03-07 11:15:20', '2023-03-07 12:00:00'),
(1019, 8, 108, 1, 349.99, '2023-03-08 14:45:50', '2023-03-08 15:20:10'),
(1020, 9, 109, 1, 229.99, '2023-03-09 09:35:05', '2023-03-09 10:10:20'),
(1021, 10, 110, 3, 299.97, '2023-03-10 13:50:40', '2023-03-10 14:15:55');
```
5. We can create pipelines for `products` and `customers` as well. Some fresh data:
```sql
INSERT INTO products (product_id, name, category, price, created_at) VALUES
(106, 'Standing Desk', 'Furniture', 499.99, '2023-02-20 10:10:10'),
(107, 'Bluetooth Keyboard', 'Accessories', 79.99, '2023-02-22 13:25:00'),
(108, '4K Ultra HD Monitor', 'Electronics', 349.99, '2023-02-24 15:45:15'),
(109, 'Ergonomic Chair', 'Furniture', 229.99, '2023-02-26 09:55:30'),
(110, 'Webcam HD 1080p', 'Accessories', 99.99, '2023-02-28 17:05:45');

INSERT INTO customers (customer_id, name, email, created_at) VALUES
(6, 'Fiona Gallagher', 'fiona.g@example.com', '2023-03-01 09:30:25'),
(7, 'George Martin', 'george.m@example.com', '2023-03-02 16:45:50'),
(8, 'Hannah Price', 'hannah.p@example.com', '2023-03-03 14:20:35'),
(9, 'Ian Wright', 'ian.w@example.com', '2023-03-04 11:15:05'),
(10, 'Julia Roberts', 'julia.r@example.com', '2023-03-05 13:40:55');
```

#### 7. Schedule pipeline.

We can schedule a pipeline using `Trigger`. There are different types of them. Quite a popular interview question:)

| Trigger Type             | Purpose / When to Use                                                                                      |
|---------------------------|-----------------------------------------------------------------------------------------------------------|
| **Schedule Trigger**      | Runs pipelines on a schedule (daily, hourly, every 5 min, etc.). Ideal for regular batch processing.       |
| **Tumbling Window Trigger** | Runs pipelines in a sliding "window" fashion, with fixed-size intervals that **don't overlap**. Good for time-partitioned data ingestion (like hourly loads). |
| **Event-Based Trigger**   | Starts pipelines when an **event happens** in Azure Storage (Blob creation/deletion) or Event Grid events. Useful for **real-time ingestion**. |
| **Manual Trigger**        | Runs pipeline manually (button click or API call). Good for ad-hoc runs or testing.                        |
| **Dependency Trigger**    | Starts a pipeline **after another pipeline** finishes. Useful for chaining multiple pipelines together.    |


Examples:

- **Schedule Trigger**  
  → Run ETL every day at 2:00 AM UTC.

- **Tumbling Window Trigger**  
  → Process hourly ingestion of logs with strict non-overlapping windows.

- **Event-Based Trigger**  
  → Automatically run the pipeline when a new file arrives in Blob Storage.

- **Manual Trigger**  
  → Developer manually starts a pipeline run from the UI or API.

- **Dependency Trigger**  
  → After the "Load Orders" pipeline succeeds, start the "Transform Orders" pipeline.


#### 8. Add Alerts on Activity Failure

We can enable Diagnostics for ADF, or we can create an Alert Rule. Let's do both.

Enable Diagnostics for ADF

- Navigate to **Data Factory** → **Monitoring** → **Diagnostic Settings**.
- Create a new **Diagnostic Setting** and send logs to **Azure Monitor** or **Log Analytics**.
- Ensure you enable **PipelineRuns** and **ActivityRuns** logs.

It will start to send logs into Log Analytics, and we can query logs and create our own rules and dashboards for monitoring of pipelines.

Create an Alert Rule

- Go to **Azure Portal** → **Monitor** → **Alerts** → **+ Create Alert Rule**.
- **Resource**: Choose your Data Factory instance.
- **Condition**:  
  - Select **Signal Type** → **Metric** or **Log**.
  - Example: Use metric **Pipeline failed runs** or query where `PipelineRunStatus == 'Failed'`.
- **Action Group**:  
  - Create or select an existing Action Group.
  - Add notification channels (Email, SMS, Webhook, etc.).

- You can configure alerts **per pipeline**.
- Assign **Severity levels** (Sev 0 - Sev 4).
- Integrate with ITSM systems (PagerDuty, ServiceNow, Slack) using Webhooks.


## Week 3: Soft Deletes and External API Integration

### 🎯 Goals

- Handle **soft deletes** by identifying removed customers during full sync and flagging them as deleted in Snowflake.
- Start ingesting data from a **public REST API (GitHub)** into Snowflake using ADF.
- Explore more advanced **merge logic** and **data comparison** techniques.

---

### 🏗️ Tasks Breakdown

#### 1. Modify `customers` Table to Track Deletions

We’ll handle full sync for `customers`, and flag any records that are no longer in the source.

```sql
ALTER TABLE raw.azure_sql.customers
ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE,
ADD COLUMN deleted_ts TIMESTAMP_LTZ;
```

#### 2. Updated MERGE Procedure for customers with Soft Delete Logic

In our Stored Procedure, we’ll:

Merge incoming rows from `tmp_customers`.

Mark customers that exist in `final` but not in `tmp` as `is_deleted = TRUE`.

```sql
CREATE OR REPLACE PROCEDURE raw.azure_sql.sp_merge_customers()
RETURNS STRING
LANGUAGE SQL
AS
$$
-- Step 1: Upsert (INSERT or UPDATE)
MERGE INTO raw.azure_sql.customers AS target
USING raw.azure_sql.tmp_customers AS source
ON target.customer_id = source.customer_id
WHEN MATCHED THEN
    UPDATE SET 
        name = source.name,
        email = source.email,
        created_at = source.created_at,
        is_deleted = FALSE,
        deleted_ts = NULL,
        etl_timestamp_utc = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (
        customer_id,
        name,
        email,
        created_at,
        is_deleted,
        deleted_ts,
        etl_timestamp_utc
    )
    VALUES (
        source.customer_id,
        source.name,
        source.email,
        source.created_at,
        FALSE,
        NULL,
        CURRENT_TIMESTAMP()
    );

-- Step 2: Mark soft-deleted customers
UPDATE raw.azure_sql.customers
SET is_deleted = TRUE,
    deleted_ts = CURRENT_TIMESTAMP()
WHERE customer_id NOT IN (
    SELECT customer_id FROM raw.azure_sql.tmp_customers
);
$$;
```

#### 3. External API Ingestion: GitHub Example

We’ll now use ADF to fetch public data from a REST API (GitHub) and stage it in Snowflake.

Steps:

Create ADF Web Activity or REST Dataset with:

```bash
URL: https://api.github.com/repos/octocat/Hello-World/commits?per_page=100
Method: GET
Dump the response to Blob Storage (as JSON).
```

You can test in CLI JSON respond for API:

```bash
curl -s "https://api.github.com/repos/octocat/Hello-World/commits?per_page=100
```

Use Copy Activity or Snowflake COPY INTO to ingest the file into a raw table.

Add basic parsing logic (flatten arrays, extract fields).

> 📌 This introduces the concept of semi-structured ETL and JSON handling.

As a result, you should:
1. Update customers' tables and procedures to handle data deletion. For testing purpose, you need to delete a single `customer_id` from SQL Server.
2. Using the public GitHub API, we should leverage ADF and ingest data into Snowflake.

## Week 4: CosmosDB NoSQL Database Integration

In this week, we will work with Microsoft NoSQL database. Read about [CosmosDB](https://learn.microsoft.com/en-us/azure/cosmos-db/introduction)

Azure Cosmos DB is Microsoft’s globally distributed, multi-model NoSQL database designed for OLTP (online transactional processing) scenarios. It is highly available (99.999%), horizontally scalable, and offers low-latency reads/writes across the globe.

✅ Key Features:
- NoSQL / Document-based (JSON format by default)
- Multi-region replication
- Guaranteed <10ms latency for reads and writes
- Multiple APIs: SQL (Core), MongoDB, Cassandra, Gremlin, Table
- Auto-scaling throughput (RU/s)
- TTL (time to live) and change feed support

In Data Engineering, CosmosDB is often treated as a source OLTP system that feeds data into an OLAP (analytics) system like Snowflake, Synapse, or Databricks.

📈 Data Engineering Use Case Example
Let’s say you're building a Customer 360 view:

- Cosmos DB stores app-generated data: purchases, behavior logs, sessions
- Azure SQL stores CRM data
- Snowflake stores marketing data

Your data pipeline:
- Extract data from Cosmos DB (via ADF, Synapse, or custom Spark job)
- Flatten/clean the JSON documents
- Merge into bronze → silver → gold Snowflake tables
- Join with CRM and marketing data
- Build dashboards in Looker or Power BI

In our case, we will just ingest sample CosmosDB data into Snowflake using an existing pattern. The closest alternative could be MongoDB database.

### 🎯 Goals

- Create a **NoSQL** database using **Azure Cosmos DB**
- Add a sample **container** with documents (JSON format)
- Ingest CosmosDB data into **Snowflake** using ADF
- Use **Synapse Analytics** as an intermediary layer to query CosmosDB efficiently





---

### 🏗️ Tasks Breakdown

---

#### 1. Create Azure Cosmos DB (NoSQL API)

1. Go to the **Azure Portal** → **Create a Resource** → Search for `Cosmos DB`.
2. Choose **Azure Cosmos DB for NoSQL**.
3. Fill in:
   - **Resource Group**
   - **Account Name** (e.g., `cosmosdw-week4`)
   - **Region** (choose closest to you)
4. Set **Capacity Mode** → *Provisioned throughput*
5. Leave defaults, click **Review + Create**, then **Create**

> 🔹 Cosmos DB for NoSQL uses document (JSON-based) storage and can be queried using SQL-like syntax.

---

#### 2. Create Sample Container and Data

1. Go to your Cosmos DB account → **Data Explorer**
2. Click **New Container**
   - Database Name: `orders_db`
   - Container Name: `orders_container`
   - Partition Key: `/customer_id`
   - Throughput: 400 RU/s (default)
3. Add sample documents:

```json
{
  "id": "order_1001",
  "customer_id": "cust_01",
  "product_id": "prod_01",
  "quantity": 2,
  "total_price": 199.98,
  "order_date": "2023-03-05T14:30:00Z",
  "status": "Shipped"
}
```



> 🔁 Add 5–10 sample orders with different id, customer_id, status, and order_date

#### 3. Create ADF Pipeline to Load CosmosDB → Snowflake

In Snowflake add new schema in database `RAW`: `cosmsodb`. And create two new tables
- `tmp_orders`
- `orders`

Add a new Snowflake Stored Procedure that will MERGE `tmp_orders` into `orders`.

In Azure Data Factory, create a new pipeline.

Add a Copy Activity:
- Source: Azure Cosmos DB (configure Linked Service with CosmosDB account keys)
    - Dataset: select database + container (orders_db.orders_container)
- Target: Snowflake (Linked Service with Snowflake)
    - Dataset: `tmp_orders

The goal is to load data into Snowflake from CosmosDB table using same approach with `watermark` table.


#### 4. Use Synapse Analytics to query Cosmosdb container and load data into Snowflake

Use this guide [Configure and use Azure Synapse Link for Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/cosmos-db/configure-synapse-link) to switch your pipeline to Synapse Analytics.

Read about Synapse Link - [What is Azure Synapse Link for Azure Cosmos DB?](https://learn.microsoft.com/en-us/azure/cosmos-db/synapse-link)

#### Deliverables for Week 4
✅ Cosmos DB account with orders_container created and populated
✅ ADF pipeline that stages data and loads it into Snowflake
✅ Stored Procedure in Snowflake that handles ingestion logic
✅ Synapse query that connects to CosmosDB and extracts live data

