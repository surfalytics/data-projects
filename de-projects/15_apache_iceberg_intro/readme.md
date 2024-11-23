# Getting Started with Apache Iceberg

## Objective

We want to understand what is Apache Iceberg Format, key advatnages and use cases for Lakehouse. During this exercies we will use "Apache Iceberg: The Definitive Guide" book to complete hands on.

## Key Terms

### 1. Table Format

- **Definition**: A specification that describes how data files are structured and stored in a data lake.
- **Purpose**: Ensures consistent interaction across multiple engines (e.g., Spark, Flink, Trino).

### 2. Manifest Files

- **Definition**: Metadata files that list all the data files in a table or partition.
- **Purpose**: Enable efficient scanning and querying by storing metadata about file paths, record counts, and column statistics.

### 3. Manifest List

- **Definition**: A higher-level metadata file that tracks all the manifest files for a table snapshot.
- **Purpose**: Provides a single entry point for understanding the state of the table.

### 4. Snapshots

- **Definition**: A consistent view of the table at a point in time.
- **Purpose**: Allows time travel queries and ensures readers and writers can operate without conflicts.

### 5. Schema Evolution

- **Definition**: The ability to add, remove, or rename columns in a table schema without disrupting queries or applications.
- **Purpose**: Makes it easier to adapt to changing data requirements over time.

### 6. Partitioning

- **Definition**: Logical division of data in a table based on key columns to improve query performance.
- **Purpose**: Iceberg partitioning is hidden from query engines, allowing for dynamic and efficient scans.

### 7. Data Files

- **Definition**: The actual files that store table data in formats like Parquet, Avro, or ORC.
- **Purpose**: Contain the raw data for a table, managed by Iceberg.

### 8. Metadata

- **Definition**: Information about the structure and state of a table, stored separately from the data files.
- **Key Components**:
  - **Table Metadata File**: Stores table-level information such as schema, partitioning, and pointers to snapshots.
  - **Metadata Versioning**: Enables tracking and recovery of historical table states.

### 9. ACID Transactions

- **Definition**: Atomicity, Consistency, Isolation, and Durability in data operations.
- **Purpose**: Ensures reliable data consistency during reads and writes, even with concurrent users.

### 10. Time Travel

- **Definition**: The ability to query historical snapshots of a table.
- **Purpose**: Facilitates debugging, auditing, and reproducibility of analyses.

### 11. Compaction

- **Definition**: The process of consolidating smaller files into larger ones.
- **Purpose**: Reduces the number of files to optimize query performance.

### 12. Deletes and Updates

- **Definition**: Supports row-level modifications without rewriting entire partitions.
- **Purpose**: Provides fine-grained control over data modifications, which is challenging in traditional formats.

### 13. Hidden Partitioning

- **Definition**: Iceberg handles partitioning internally, abstracting it from query engines.
- **Purpose**: Removes the need for users to specify partitions explicitly in queries.

### 14. Catalogs

- **Definition**: Systems that manage table metadata and provide access to Iceberg tables.
- **Examples**: Hive Metastore, AWS Glue, or custom implementations.
- **Purpose**: Enable easy integration with engines like Spark, Flink, or Trino.

## Benefits of Apache Iceberg

1. **Engine Agnostic**: Compatible with various processing engines (e.g., Spark, Flink, Trino).
2. **Efficient Queries**: Leverages column statistics and hidden partitioning for optimized scanning.
3. **Versioned Data**: Supports time travel and snapshot isolation.
4. **Scalability**: Designed for large-scale datasets in data lakes.
5. **ACID Compliance**: Ensures data consistency and reliability during complex operations.

## Prerequisites

- [Apache Iceberg: The Definitive Guide Book](https://hello.dremio.com/wp-apache-iceberg-the-definitive-guide-reg.html)
- Trial Dremio: https://www.dremio.com/cloud/
- AWS account: https://aws.amazon.com/free/

All discussions and weekly meetings will be in the Discord channel - **data-engineering-projects**.





