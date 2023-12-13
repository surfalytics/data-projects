# Trino 101

## Objective

Try Trino and deploy it using Docker and Standalone isntallation and then query the data an duse `trino-dbt` connector
Key Terms
Snowflake Data Warehouse: Snowflake Data Warehouse is a cloud-based platform that offers a comprehensive suite of features for data warehousing, data lakes, data engineering, data science, and data application development. It is designed for secure sharing and consumption of shared data. Its unique architecture supports various data workloads and enables scalable, flexible, and efficient data storage and analysis.

SnowCLI: SnowCLI is a Command Line Interface tool specifically designed for managing Snowflake. It provides a convenient way for users to interact with Snowflake, perform administrative tasks, manage data, execute queries, and automate workflows directly from the command line.

SnowSQL: SnowSQL is a specialized SQL client for Snowflake. It allows users to execute SQL queries against Snowflake data warehouses, manage database objects, and perform various database operations. SnowSQL is designed to leverage Snowflake's capabilities, providing a seamless and optimized experience for running SQL commands.

Snowpipe: Snowpipe is a tool for continuous, automated data ingestion into Snowflake. It enables real-time data loading, allowing users to automatically import data into Snowflake as soon as it becomes available. Snowpipe is essential for scenarios requiring up-to-date data, such as real-time analytics and data streaming.

Time Travel: Time Travel is a unique feature of Snowflake that allows users to access historical data within a defined period. This feature enables users to query past states of data or restore data from a specific point in time, providing significant benefits for data recovery, auditing, and analysis.

Snowflake Architecture: The Snowflake Architecture is characterized by its multi-cluster, shared data architecture. This innovative design separates compute and storage resources, allowing Snowflake to offer high performance, scalability, and concurrency. It enables users to run multiple workloads without performance degradation and manage data efficiently across the organization.

Hex Notebook (www.hex.tech): Hex Notebook is a modern data workspace that integrates notebooks, Python, SQL, and visualizations. It is designed for collaborative data analysis and project development, offering a user-friendly interface for writing code, executing SQL queries, and creating interactive data visualizations. Hex Notebook facilitates teamwork and streamlines the data analysis process, making it ideal for data scientists, analysts, and engineers.

## Prerequisites

- Install Docker App
- Make sure you installed Java and Python

```
java --version
python --version
```

## Implementation

### Trino on Docker
Download Trino image

```
docker pull trinodb/trino
```

Run trino:

```
docker run -d -p 8080:8080 --name trino-trial trinodb/trino
```

Open trino:

```
 docker exec -it trino-trial trino
```

The default Trino Server is http://localhost:8080

Query the data:

```
trino> select count(*) from tpch.sf1.nation;
 _col0 
-------
    25 
(1 row)

Query 20231213_012611_00000_cp5e6, FINISHED, 1 node
Splits: 21 total, 21 done (100.00%)
1.31 [25 rows, 0B] [19 rows/s, 0B/s]
```

We can mount directory as a volume in the path
etc/trino when starting the container, your configuration is used instead of the default
in the image:

```
docker run -d -p 8080:8080 --volume $PWD/etc:/etc/trino trinodb/trino
```

Stop container:

```
docker stop trino-trial
```

Start container:

```
docker start trino-trial
```

Delete container and image:

```
docker rm trino-trial
trino-trial

docker rmi trinodb/trino
Untagged: trinodb/trino:latest
```

### Trino on Archive File

Confirm that java and python is installed and available on the PATH:

```
java --version
python --version
```

Install Java on Mac:

```
brew install openjdk@17

sudo ln -sfn /opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk \
     /Library/Java/JavaVirtualMachines/openjdk-17.jdk

java -version
openjdk version "11.0.21" 2023-10-17
OpenJDK Runtime Environment Homebrew (build 11.0.21+0)
OpenJDK 64-Bit Server VM Homebrew (build 11.0.21+0, mixed mode)
```

We can download Trino from https://repo.maven.apache.org/maven2/io/trino/trino-server

```
wget https://repo.maven.apache.org/maven2/io/trino/trino-server/392/trino-server-392.tar.gz

tar xvzf trino-server-*.tar.gz
```

Also, I've added the `single-installation/etc` to the Trino Server

#### Configuration

Before you can start Trino, you need to provide a set of configuration files:
• Trino logging configuration
• Trino node configuration
• JVM configuration

etc/config.properties:

```
coordinator=true
node-scheduler.include-coordinator=true
http-server.http.port=8080
discovery.uri=http://localhost:8080
```

etc/node.properties:

```
node.environment=demo
```

etc/jvm.config:

```
-server
-Xmx4G
-XX:InitialRAMPercentage=80
-XX:MaxRAMPercentage=80
-XX:G1HeapRegionSize=32M
-XX:+ExplicitGCInvokesConcurrent
-XX:+ExitOnOutOfMemoryError
-XX:+HeapDumpOnOutOfMemoryError
-XX:-OmitStackTraceInFastThrow
-XX:ReservedCodeCacheSize=512M
-XX:PerMethodRecompilationCutoff=10000
-XX:PerBytecodeRecompilationCutoff=10000
-Djdk.attach.allowAttachSelf=true
-Djdk.nio.maxCachedBufferSize=2000000
-XX:+UnlockDiagnosticVMOptions
-XX:+UseAESCTRIntrinsics
```

#### Ading Data Store

Trino catalogs define the data sources available to users. The data access is performed
by a Trino connector configured in the catalog with the connector.name property.
Catalogs expose all the schemas and tables inside the data source to Trino.

etc/cata‐log/tpch.properties with the tpch connector configured:

```
connector.name=tpch
```

#### Running Trino

```
bin/launcher run
```

In my case I've updated shebang `#!/usr/bin/env python3` for `launcher.py`.

This will start the local Trino Cluster. 

## Materials:

- O'Reilly Book [Trino The Definative Guide](https://www.starburst.io/wp-content/uploads/2021/04/Trino-Oreilly-Guide.pdf)
- [Book Repo](https://github.com/trinodb/trino-the-definitive-guide)
- [Trino Repo](https://github.com/trinodb/trino)
