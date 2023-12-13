# Trino 101

## Objective

Try Trino and deploy it using Docker and Standalone isntallation and then query the data an duse `trino-dbt` connector

## Key Terms

Trino is an open source, distributed SQL query engine. It was designed and written
from the ground up to efficiently query data against disparate data sources of all sizes,
ranging from gigabytes to petabytes. Trino breaks the false choice between having fast
analytics using an expensive commercial solution or using a slow “free” solution that
requires excessive hardware.

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
