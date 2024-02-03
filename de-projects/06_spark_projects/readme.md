# Apache Spark Projects

## Install Spark Locally

We have multiple options to install Sparl Locally. They also might depend on OS you are using.

1. Download Spark Archive
2. Install Pyspark locally
3. Use the Docker file
4. Use Databricks Community Edition

### 1. Download Spark Archive

We can [download Apache Spark](https://spark.apache.org/downloads.html) 

### 2. Install PySpark locally

> If you are using Windows, you should use Ubuntu on Windows WSL. Look next section.

#### Install on MacOS or Linux
We would need to have:

JAVA:

```bash
java -version
java version "1.8.0_121"
Java(TM) SE Runtime Environment (build 1.8.0_121-b13)
Java HotSpot(TM) 64-Bit Server VM (build 25.121-b13, mixed mode)
```

Pythob:

```bash
python3 --version
Python 3.11.7
```

We can use [PySpark library](https://pypi.org/project/pyspark/) and install it as a Python project

```bash
pip install pyspark
```

or

```bash
pip3 install pyspark
```

#### Install on Windows

1. Download [Ubuntu for Windows](https://ubuntu.com/wsl) 
2. Set username and password
3. Run the following commands:

```bash
sudo apt update
sudo apt upgrade

#install python
sudo apt install python3

#install pip
sudo apt install python3-pip

#install java
sudo apt install default-jdk

#install 
pip install pyspark
```

4. Run Spark with command `pyspark`

### 3. Use the Docker file 

There is a Dockerfile `de-projects/06_spark_projects/spark_docker/Dockerfile` that has PySpark and copy all PySpark projects from `de-projects/06_spark_projects`.

You can run these commands:

```bash 
cd ./de-projects/06_spark_projects/spark_docker
```

Build the Spark Image:

```bash
docker build -t spark-local  .
```

Run PySpark and mount folders:

```bash
docker run -it -p 4050:4040 \
  -v ./01_spark_localhost:/opt/spark_projects/01_spark_localhost \
  -v ./02_spark_dataframe_api:/opt/spark_projects/02_spark_dataframe_api \
  spark-local pyspark
```

>Note: just in case we do port forwarding from 4040 to 4050

And we can try to run the little snippet of PySpark:

```python
from pyspark.sql.types import *
import pyspark.sql.functions as F

# Use the DataFrameReader interface to read a CSV file
sf_fire_file = "/opt/spark_projects/02_spark_dataframe_api/data/sf-fire-calls.csv"
fire_df = spark.read.csv(sf_fire_file, header=True)
fire_df.show()
```

We also can open Spark UI at [http://localhost:4050/jobs/](http://localhost:4050/jobs/). 