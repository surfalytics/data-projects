# Run simple Spark program on Localhost on MacOS

## Check Java

```bash
java -version
java version "1.8.0_121"
Java(TM) SE Runtime Environment (build 1.8.0_121-b13)
Java HotSpot(TM) 64-Bit Server VM (build 25.121-b13, mixed mode)
```
## Install Python

```
brew install python   

python3 --version
Python 3.11.7
```

## Install PySpark

```bash
pip3 install pyspark
```

## Launch PySpark

```bash
pyspark
Python 3.11.7 (main, Dec  4 2023, 18:10:11) [Clang 15.0.0 (clang-1500.1.0.2.5)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
24/01/20 12:09:55 WARN Utils: Your hostname, MacBook-Pro.local resolves to a loopback address: 127.0.0.1; using 10.17.201.250 instead (on interface en0)
24/01/20 12:09:55 WARN Utils: Set SPARK_LOCAL_IP if you need to bind to another address
Setting default log level to "WARN".
To adjust logging level use sc.setLogLevel(newLevel). For SparkR, use setLogLevel(newLevel).
24/01/20 12:09:56 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
Welcome to
      ____              __
     / __/__  ___ _____/ /__
    _\ \/ _ \/ _ `/ __/  '_/
   /__ / .__/\_,_/_/ /_/\_\   version 3.5.0
      /_/

Using Python version 3.11.7 (main, Dec  4 2023 18:10:11)
Spark context Web UI available at http://10.17.201.250:4040
Spark context available as 'sc' (master = local[*], app id = local-1705781397673).
SparkSession available as 'spark'.
```


## Create DataFrame

```python
>>> mnm_file = '/Users/dmitryanoshin/github/data-projects/de-projects/06_spark_projects/01_spark_localhost/data/mnm_dataset.csv'
>>> mnm_df = (spark.read.format("csv")
...         .option("header", "true")
...         .option("inferSchema", "true")
...         .load(mnm_file))
```

## Show Schema

```python
>>> mnm_df.printSchema()
root
 |-- State: string (nullable = true)
 |-- Color: string (nullable = true)
 |-- Count: integer (nullable = true)
```

## Show Sample of Data

```python
>>> mnm_df.show(n=5, truncate=False)
+-----+------+-----+
|State|Color |Count|
+-----+------+-----+
|TX   |Red   |20   |
|NV   |Blue  |66   |
|CO   |Blue  |79   |
|OR   |Blue  |71   |
|WA   |Yellow|93   |
+-----+------+-----+
only showing top 5 rows
```

## Aggreagte data

```python
>>> count_mnm_df = (mnm_df.select("State", "Color", "Count")
...                     .groupBy("State", "Color")
...                     .sum("Count")
...                     .orderBy("sum(Count)", ascending=False))
>>> count_mnm_df.show(n=3, truncate=False)
+-----+------+----------+                                                       
|State|Color |sum(Count)|
+-----+------+----------+
|CA   |Yellow|100956    |
|WA   |Green |96486     |
|CA   |Brown |95762     |
+-----+------+----------+

>>> print("Total Rows = %d" % (count_mnm_df.count()))
Total Rows = 60
```


```python
>>> ca_count_mnm_df = (mnm_df.select("*")
...                        .where(mnm_df.State == 'CA')
...                        .groupBy("State", "Color")
...                        .sum("Count")
...                        .orderBy("sum(Count)", ascending=False))
>>> ca_count_mnm_df.show(n=10, truncate=False)
+-----+------+----------+
|State|Color |sum(Count)|
+-----+------+----------+
|CA   |Yellow|100956    |
|CA   |Brown |95762     |
|CA   |Green |93505     |
|CA   |Red   |91527     |
|CA   |Orange|90311     |
|CA   |Blue  |89123     |
+-----+------+----------+
```

## Run Spark Program

```bash
python3 mnmcount.py /Users/dmitryanoshin/github/data-projects/de-projects/06_spark_projects/01_spark_localhost/data/mnm_dataset.csv
```


# Run simple Spark program on Localhost on Windows