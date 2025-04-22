# Typical Data Warehouse on Azure

This project simulates a typical data warehouse architecture using Azure services as the source systems and Snowflake as the target cloud data warehouse. The goal is to build a modern data platform incrementally by following weekly tasks.

## Week 1: Initial Setup and Data Ingestion from Azure SQL to Snowflake

### 🎯 Objectives

- Set up the foundational infrastructure on Azure and Snowflake.
- Create and populate source tables in **Azure SQL Database**.
- Configure **Azure Data Factory (ADF)** to perform a **COPY** activity from Azure SQL to Snowflake.
- Perform an initial data load into `raw.azure_sql.orders`.

---

### 🧰 Tools & Services

- [Azure Free Trial Subscription](https://azure.microsoft.com/en-ca/pricing/purchase-options/azure-account/)
- Azure Resource Group
- Azure SQL Database
- Azure Key Vault
- Azure Blob Storage
- Azure Data Factory
- Snowflake Trial Account

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
(1, 'Alice Johnson', 'alice.j@example.com', '2023-01-10'),
(2, 'Bob Smith', 'bob.smith@example.com', '2023-01-12'),
(3, 'Charlie Davis', 'charlie.d@example.com', '2023-01-15'),
(4, 'Diana Cruz', 'diana.c@example.com', '2023-02-01'),
(5, 'Ethan Lee', 'ethan.l@example.com', '2023-02-10');

INSERT INTO products (product_id, name, category, price, created_at) VALUES
(101, 'Laptop Pro 15"', 'Electronics', 1499.99, '2023-01-01'),
(102, 'Wireless Mouse', 'Accessories', 29.99, '2023-01-03'),
(103, 'Noise Cancelling Headphones', 'Electronics', 199.95, '2023-01-05'),
(104, 'Office Desk', 'Furniture', 299.99, '2023-01-08'),
(105, 'LED Monitor 24"', 'Electronics', 159.99, '2023-01-09');

INSERT INTO orders (order_id, customer_id, product_id, quantity, total_price, created_at, updated_at) VALUES
(1001, 1, 101, 1, 1499.99, '2023-01-11', '2023-01-11'),
(1002, 2, 102, 2, 59.98, '2023-01-13', '2023-01-15'),
(1003, 3, 103, 1, 199.95, '2023-01-16', '2023-01-18'),
(1004, 4, 104, 1, 299.99, '2023-02-02', '2023-02-02'),
(1005, 5, 105, 2, 319.98, '2023-02-12', '2023-02-14'),
(1006, 1, 102, 3, 89.97, '2023-03-01', '2023-03-04');
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

Use Blob Storage as intermediate staging in Copy Activity. 
