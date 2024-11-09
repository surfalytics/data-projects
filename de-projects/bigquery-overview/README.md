# Table of Contents

- [Introduction](#introduction)
- [Databases vs. Data Warehouses vs. Data Lakes](#databases-vs-data-warehouses-vs-data-lakes)
  - [Databases](#databases)
  - [Data Warehouses](#data-warehouses)
  - [Data Lakes](#data-lakes)
  - [Summary](#summary)
- [BigQuery Overview](#bigquery-overview)
- [Architecture](#architecture)
- [BigQuery vs Snowflake](#bigquery-vs-snowflake)
  - [Architecture](#architecture-1)
  - [Scalability](#scalability)
  - [Performance](#performance)
  - [Pricing](#pricing)
- [How to get started with BigQuery?](#how-to-get-started-with-bigquery)
  - [BigQuery Sandbox](#bigquery-sandbox)
- [Storage Overview. How to partition and cluster data?](#storage-overview-how-to-partition-and-cluster-data)
  - [Resource Model](#resource-model)
  - [Partitioning](#partitioning)
    - [Partitioning: Hands-on](#partitioning-hands-on)
  - [Clustering](#clustering)
    - [Clustering: Hands-On](#clustering-hands-on)

## **Introduction**

In this lesson, we’ll dive into Google BigQuery’s essentials, exploring how it’s designed for big data analytics and how it compares to other tools like Snowflake. You’ll learn practical techniques to optimize your queries with partitioning and clustering, keeping performance high and costs low. Plus, we’ll guide you on getting started with BigQuery for free, so you can start running queries right away. By the end, you’ll have a solid foundation to use BigQuery effectively in your own data projects.

## **Databases vs. Data Warehouses vs. Data Lakes**

As data volumes grow, choosing the right storage solution is crucial. Databases, data warehouses, and data lakes each offer unique advantages and serve different needs. Let’s explore their key differences, architectures, and strengths.

![image](https://github.com/user-attachments/assets/b00457ad-3807-45c6-ae08-c7d98fb5764b)


### Databases

Databases are designed for quick, transactional operations, making them ideal for real-time business applications. Common examples include MySQL, PostgreSQL, and MongoDB.

- **Architecture**: Row-based, optimized for Online Transaction Processing (OLTP).
- **Pros**: Fast transactions, data integrity, structured accessibility.
- **Cons**: Limited scalability, not ideal for large-scale analytics.

### Data Warehouses

Data warehouses like Google BigQuery, Amazon Redshift, and Snowflake aggregate data from multiple sources for high-performance analytics, making them essential for business intelligence.

- **Architecture**: Columnar, optimized for Online Analytical Processing (OLAP).
- **Pros**: Fast query performance, centralized data, historical data storage.
- **Cons**: High costs, rigid ETL processes, limited support for unstructured data.

### Data Lakes

Data lakes, such as those on Google Cloud Storage, Amazon S3 and Azure Data Lake, provide scalable storage for both structured and unstructured data, supporting diverse use cases like big data and machine learning.

- **Architecture**: Distributed, schema-on-read for flexibility.
- **Pros**: High scalability, flexible data formats, suitable for advanced analytics.
- **Cons**: Risk of “data swamps,” slower retrieval, potential data quality issues.

### Summary

Each solution serves specific purposes: databases for transactions, data warehouses for analytics, and data lakes for scalable storage. In this landscape, Google BigQuery is a data warehouse, combining analytics performance with data lake flexibility, making it a valuable tool for modern data-driven organizations.

## BigQuery Overview

![image](https://github.com/user-attachments/assets/41e9d672-5344-49a1-8fa5-c75e50bd1d1e)


[BigQuery](https://airbyte.com/connectors/bigquery) is a serverless data warehouse that was released in 2011 by Google

- **Enterprise Data Warehouse**: BigQuery serves as a robust data warehouse solution, ideal for large-scale enterprise analytics needs.
- **Serverless**: Fully managed by Google Cloud, BigQuery removes the need for infrastructure management, letting users focus purely on data analytics.
- **Separate Storage and Compute**: BigQuery’s architecture separates storage from compute, enabling flexible scaling and efficient resource allocation based on workload needs.
- **Scalability**: Designed to handle petabytes of data, BigQuery scales seamlessly, making it suitable for datasets of any size.
- **Cost Efficiency**: With a pricing model based on usage, BigQuery only charges for the storage and compute resources actually used, optimizing cost-effectiveness.

## Architecture

BigQuery’s serverless architecture decouples storage and compute and allows them to scale independently on demand. This is very different from traditional node-based cloud data warehouse solutions or on-premise massively parallel processing (MPP) systems.

![image](https://github.com/user-attachments/assets/f625aaee-ca66-4713-8197-3bbd42767bb7)


Under the hood, BigQuery employs a vast set of multi-tenant services driven by low-level Google infrastructure technologies like [Dremel, Colossus, Jupiter and Borg](https://cloud.google.com/blog/big-data/2016/01/bigquery-under-the-hood).

![image](https://github.com/user-attachments/assets/d58052ed-3940-4efd-96f5-fc089714eedf)


**Compute is [Dremel](https://research.google.com/pubs/pub36632.html), a large multi-tenant cluster that executes SQL queries.**

- Dremel turns SQL queries into execution trees. The leaves of the tree are called slots and do the heavy lifting of reading data from storage and any necessary computation. The branches of the tree are ‘mixers’, which perform the aggregation.
- Dremel dynamically apportions slots to queries on an as-needed basis, maintaining fairness for concurrent queries from multiple users. A single user can get thousands of slots to run their queries.

**Storage is [Colossus](https://www.systutorials.com/3202/colossus-successor-to-google-file-system-gfs/), Google’s global storage system.**

- BigQuery leverages the [columnar storage format](https://cloud.google.com/blog/products/gcp/inside-capacitor-bigquerys-next-generation-columnar-storage-format) and compression algorithm to store data in Colossus, optimized for reading large amounts of structured data.
- Colossus also handles replication, recovery (when disks crash) and distributed management (so there is no single point of failure). Colossus allows BigQuery users to scale to dozens of petabytes of data stored seamlessly, without paying the penalty of attaching much more expensive compute resources as in traditional data warehouses.

**Compute and storage talk to each other through the petabit [Jupiter](https://cloudplatform.googleblog.com/2015/06/A-Look-Inside-Googles-Data-Center-Networks.html) network.**

- In between storage and compute is ‘shuffle’, which takes advantage of Google’s Jupiter network to move data extremely rapidly from one place to another.

**BigQuery is orchestrated via [Borg](https://research.google.com/pubs/pub43438.html), Google’s precursor to [Kubernetes](https://kubernetes.io/).**

- The mixers and slots are all run by Borg, which allocates hardware resources.

## BigQuery vs Snowflake

![image](https://github.com/user-attachments/assets/de5a3bfd-91c5-4d42-a992-3e13d652a85d)


### Architecture

Snowflake and BigQuery both offer decoupled storage and compute resources that can elastically scale to meet all your mission-critical workload requirements. But they also have slightly different architectures.

**Snowflake** has a [three-layer architecture](https://docs.snowflake.com/en/user-guide/intro-key-concepts.html#snowflake-architecture).

- Centralized storage layer: Uses cloud storage infrastructure from platforms such as AWS, Microsoft Azure, and GCP to store all your data records persistently, without any losses.
- Multi-cluster compute layer: Contains multiple massively parallel processing (MPP) compute clusters that are capable of quickly processing all your complex queries.
- Cloud services layer: This layer is a collection of different services, such as query management, optimization, transactions, security, metadata, and sharing.

Snowflake’s unique three-layered architecture offers the data management simplicity of a shared-disk architecture along with the scalability of a shared-nothing architecture.

![image](https://github.com/user-attachments/assets/718e274f-8f59-441e-9e0d-fd62dfe10415)


### Scalability

![image](https://github.com/user-attachments/assets/318aa49b-2fff-40f8-afa8-8d1a0c247b19)


### Performance

![image](https://github.com/user-attachments/assets/9a18541b-8c7c-4f32-bda5-15aaff96a968)


![image](https://github.com/user-attachments/assets/68d950ed-f78b-4bbb-a643-cfc483b89587)


### Pricing

![image](https://github.com/user-attachments/assets/b6224531-0fe7-4342-bf9a-5d11e352737b)

## **How to get started with BigQuery?**

- **BigQuery Sandbox** allows you to easily access BigQuery features without providing your credit card information. There are some limitations.
- The **GCP free trial** includes a $300-worth free credit that is applicable across all GCP products.

For both: 10 GB per month storage for free, 1 TB of query data processed per month

- Using official **BigQuery learning** courses from Google. [Example](https://www.cloudskillsboost.google/course_templates/14)

### **BigQuery Sandbox**

- Create google account
- Go to the following link: `https://console.cloud.google.com/bigquery`
- Login to BigQuery console and run the following sql query:

```sql
SELECT 
  EXTRACT(YEAR FROM creation_date) AS year,
  EXTRACT(MONTH FROM creation_date) AS month,
  COUNT(creation_date) AS number_posts
FROM
  `bigquery-public-data.stackoverflow.stackoverflow_posts`
WHERE
  answer_count > 0
GROUP BY year, month
ORDER BY year ASC, month ASC;
```

## Storage Overview. How to partition and cluster data?

### Resource Model

Folder structure: project, dataset, and table - helps you structure your information logically

![image](https://github.com/user-attachments/assets/a47f31d1-83e6-46e3-b144-4200fa55b3eb)


BigQuery uses columnar storage, storing each column in a separate file block, making it ideal for OLAP use cases. Unlike traditional databases like MySQL, which store data row-by-row for OLTP tasks, BigQuery supports efficient data streaming, updates, and deletions. It allows unlimited data mutations (INSERT, UPDATE, MERGE, DELETE).

![image](https://github.com/user-attachments/assets/d6faa897-cc0c-4c8c-915a-204474f558a8)

BigQuery uses variations and advancements on columnar storage. Internally, BigQuery stores data in a proprietary columnar format called [Capacitor](https://cloud.google.com/blog/products/gcp/inside-capacitor-bigquerys-next-generation-columnar-storage-format), which has a number of benefits for data warehouse workloads. 

You can load data into BigQuery at [no cost](https://cloud.google.com/bigquery/pricing#free) (for batch loads) because [BigQuery storage costs](https://cloud.google.com/bigquery/pricing#storage) are based on the amount of data stored (first 10 GB is free each month) and whether storage is considered active or long-term.

- If you have a table or partition modified in the last 90 days, it is considered as active storage and incurs a monthly charge for data stored at BigQuery storage rates.

![image](https://github.com/user-attachments/assets/bda5ede4-b90e-493c-ab15-2cad383b3e29)

### **Partitioning**

A partitioned table is a special table that is divided into segments, called partitions, that make it easier to manage and query your data. You can typically split large tables into many smaller partitions using data ingestion time or `TIMESTAMP/DATE` column or an `INTEGER` column.

![image](https://github.com/user-attachments/assets/423d0f32-d790-4680-9479-ae4d72f3fa00)

BigQuery supports following ways to create partitioned tables:

***Ingestion time partitioned tables*:**

- Automatically partitions data by ingestion date, adding `_PARTITIONTIME` and `_PARTITIONDATE` columns.

***DATE/TIMESTAMP column partitioned tables*:**

- Partitions based on a `TIMESTAMP` or `DATE` column, with special partitions for `NULL` and out-of-range values. Supports hourly granularity.

***INTEGER range partitioned tables*:**

- Partitions based on integer ranges, with special partitions for `NULL` and out-of-range values.

### Partitioning: Hands-on

By running the following SQL query, we will create a non-partitioned table with data loaded from a [public data set](https://console.cloud.google.com/marketplace/browse?filter=solution-type:dataset&_ga=2.99891288.755387171.1599359331-1764086539.1598401521) based on StackOverflow posts by [creating a new table from an existing table](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#creating_a_new_table_from_an_existing_table). This table will contain the StackOverflow posts created in 2018.

```sql
CREATE OR REPLACE TABLE `stackoverflow.questions_2018` AS
SELECT *
FROM `bigquery-public-data.stackoverflow.posts_questions`
WHERE creation_date BETWEEN '2018-01-01' AND '2018-07-01'
```

Let’s **query the non-partitioned table** to fetch all StackOverflow questions tagged with ‘android’ in the month of January 2018.

```sql
SELECT
 id,
 title,
 body,
 accepted_answer_id,
 creation_date,
 answer_count,
 comment_count,
 favorite_count,
 view_count
FROM
 `stackoverflow.questions_2018`
WHERE
 creation_date BETWEEN '2018-01-01' AND '2018-02-01'
 AND tags = 'android';
```

Before the query runs, [caching is disabled](https://cloud.google.com/bigquery/docs/cached-results#console) to be fair when comparing performance with partitioned and clustered tables.

Now let’s see whether partitioned tables can do better. You can create partitioned tables in [multiple ways](https://cloud.google.com/bigquery/docs/creating-partitioned-tables#creating_ingestion-time_partitioned_tables). We will create a `DATE/TIMESTAMP` partitioned table using [BigQuery DDL statements](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language). We chose the partitioning column as `creation_date` based on the query access pattern.

```sql
CREATE OR REPLACE TABLE `stackoverflow.questions_2018_partitioned`
PARTITION BY
 DATE(creation_date) AS
SELECT
 *
FROM
 `bigquery-public-data.stackoverflow.posts_questions`
WHERE
 creation_date BETWEEN '2018-01-01' AND '2018-07-01';
```

Now let’s run the previous **query on the partitioned table**, [with cache disabled](https://cloud.google.com/bigquery/docs/cached-results#console), to fetch all StackOverflow questions tagged with ‘android’ in the month of January 2018.

```sql
SELECT
 id,
 title,
 body,
 accepted_answer_id,
 creation_date,
 answer_count,
 comment_count,
 favorite_count,
 view_count
FROM
 `stackoverflow.questions_2018_partitioned`
WHERE
 creation_date BETWEEN '2018-01-01' AND '2018-02-01'
 AND tags = 'android';
```

**With partitioned table query scanned only the required partitions in <2s processing ~290MB data** compared to query running with non-partitioned table processing 3.2GB.

### **Clustering**

In BigQuery, clustering organizes table data based on specified columns, ideally high-cardinality and non-temporal columns. Data is sorted by clustering column values into storage blocks. BigQuery automatically re-clusters data when new data is added, maintaining order without extra cost or user intervention.

![image](https://github.com/user-attachments/assets/c9ad7d05-521c-42cb-ba7d-79e33f116e65)

Clustering improves query performance, especially for filter and aggregation queries, by allowing BigQuery to skip unnecessary data scans. Clustering can be applied to both partitioned and non-partitioned tables, allowing partitioning by `DATE` or `TIMESTAMP` and clustering on up to four other columns.

### Clustering: Hands-On

You can create clustered tables in [multiple ways](https://cloud.google.com/bigquery/docs/creating-clustered-tables#creating_clustered_tables). We will create a new `DATE/TIMESTAMP` partitioned and clustered table using [BigQuery DDL statements](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#creating_a_clustered_table). We chose the partitioning column as `creation_date` and cluster key as `tag` based on the query access pattern.

```sql
CREATE OR REPLACE TABLE `stackoverflow.questions_2018_clustered`
PARTITION BY
 DATE(creation_date)
CLUSTER BY
 tags AS
SELECT
 *
FROM
 `bigquery-public-data.stackoverflow.posts_questions`
WHERE
 creation_date BETWEEN '2018-01-01' AND '2018-07-01';
```

Now let’s run the **query on the partitioned and clustered table**, [with cache disabled](https://cloud.google.com/bigquery/docs/cached-results#console), to fetch all StackOverflow questions tagged with ‘android’ in the month of January 2018.

```sql
SELECT
 id,
 title,
 body,
 accepted_answer_id,
 creation_date,
 answer_count,
 comment_count,
 favorite_count,
 view_count
FROM
 `stackoverflow.questions_2018_clustered`
WHERE
 creation_date BETWEEN '2018-01-01'
 AND '2018-02-01'
 AND tags = 'android';
```

With a partitioned and clustered table, the query scanned ~275MB of data in less than 1s, which is better than a partitioned table. The way data is organized by partitioning and clustering minimizes the amount of data scanned by slot workers thereby improving query performance and optimizing costs.

Few things to note when using clustering:

- Clustering does not provide strict cost guarantees before running the query. Notice in the results above with clustering, query validation reported processing of 286.1MB but actually query processed only 275.2MB of data.
- Use clustering only when you need more granularity than partitioning alone allows.
