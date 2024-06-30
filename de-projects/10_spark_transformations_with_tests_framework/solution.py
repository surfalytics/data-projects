# This solution is not ideal. Functionally, it works, but retirns wrong result.

Dmitry
dimoobraznii_91655
Online

Dmitry — Today at 10:13 AM
DE Assignments 1:

Spark ML Logs Transformer
Your first task as a newly hired data engineer is to implement a simple ETL process on a logs stream, produced by data scientists in their machine learning experiments.

Data
Inside  you will find a part of this stream in JSONL format, i.e. a single, valid JSON object per line.

The log object consists of the following fields:

 
a string-based unique indentifier,
an int-based identifier of the experiment, in which this log was produced,
an int-based identifier of the metric, of which this log represents the value,
a deprecated boolean representing whether the log is valid or not (not used),
a date when the log was produced,
a date when the log was written to the stream,
a consecutive identifier inside the experiment representing the order,
a value of the metric.
You can find the corresponding experiments names in  file.

On the other hand, metric names are well-known inside the company, so you have to memorize them on your own:  means  and  is .

Tasks
Your task is to implement an ETL pipeline, which reads an input logs stream, merges additional information, transforms the data and finally, stores it in a new format.

Part 1: Data loaders
In  implement the following functions:

 
it should accept a path to a JSONL file, as defined in the Data section above, and returns a Spark  object containing logs data,
it should accept a path to a CSV file and returns a Spark  object containing  and  columns,
it should returns a Spark  object containing two rows and two columns, as defined in the Data section above.
Part 2: Merge data sources
Having the data loaded, your task is to merge the results into a single . Implement  function which accepts s from the previous task, and returns a new  with all three tables merged, using  and  as foreign keys.

Part 3: Filter invalid logs
Some of the logs were ingested into the stream too late. We don't want that kind of behavior, and your task is to filter out logs, which were injected later than some specified number of hours after the creation date. Implement  method.

Part 4: Calculate experiment's statistics
Once you filtered out invalid logs, your task is to calculate final metrics for each metric in each experiment. The final metric value consists of the  and  values for each metric in each experiment. The expected  should consists of at least following columns:

 
name of the experiment,
name of the metric,
max  of the  in the ,
min  of the  in the .
Part 5: Save transformed data
Finally, the calculated statistics have to be saved in Parquet format. Ideally, the data should be partitioned by  column, so the analysis of the statistics in the future will be more efficient.
Dmitry — Today at 10:14 AM
h
Attachment file type: archive
devskiller-code-FHW4-WWG7-DAHE-S0F.zip
12.31 KB
Dmitry — Today at 10:34 AM
functools.lru_cache is a decorator in Python that allows you to cache the results of function calls. LRU stands for "Least Recently Used," which means that the cache will store a fixed number of results, and if the cache is full, it will remove the least recently used result to make room for a new one.

Using lru_cache can significantly improve the performance of your program, especially if you have functions that are called frequently with the same arguments. By caching the results, you avoid redundant computations and reduce the time complexity of your functions.
Dmitry — Today at 11:29 AM
Style Guide: https://github.com/palantir/pyspark-style-guide
GitHub
GitHub - palantir/pyspark-style-guide: This is a guide to PySpark c...
This is a guide to PySpark code style presenting common situations and the associated best practices based on the most frequent recurring topics across the PySpark repos we&#39;ve encountered. ...
GitHub - palantir/pyspark-style-guide: This is a guide to PySpark c...
Dmitry — Today at 11:41 AM
https://towardsdatascience.com/optimizing-output-file-size-in-apache-spark-5ce28784934c
Medium
Optimizing Output File Size in Apache Spark
A Comprehensive Guide on Managing Partitions, Repartition, and Coealesce Operations
Definitions:
Coalesce: Coalesce reduces the number of partitions in a DataFrame without shuffling the data. It is efficient for reducing the number of partitions when you know that the target number of partitions is lower.
Repartition: Repartition reshuffles the data across the specified number of partitions, evenly distributing the data. This can be useful for increasing or decreasing the number of partitions to improve performance for specific operations.

Application to Your Example:
For your example, if you need to reduce the number of partitions before writing the data to Parquet, coalesce is preferable because it avoids the full shuffle that repartition would incur, making it more efficient.

Here's how you can apply coalesce before saving the DataFrame:

def save_to_parquet(data: DataFrame, output_path: str) -> None:
    """
    Save the DataFrame to Parquet format partitioned by metricId.

    Args:
        data (DataFrame): The DataFrame containing the final scores.
        output_path (str): The output path where the Parquet files will be saved.
    """
    # Reduce the number of partitions to 1 before writing, to avoid small files
    data = data.coalesce(1)
    data.write.partitionBy("metricId").parquet(output_path)

# Example usage:
# logs_df = load_logs(Path("path_to_logs.json"))
# experiments_df = load_experiments(Path("path_to_experiments.csv"))
# metrics_df = load_metrics()
# joined_df = join_tables(logs_df, experiments_df, metrics_df)
# filtered_df = filter_late_logs(joined_df, hours=12)
# final_scores_df = calculate_experiment_final_scores(filtered_df)
# save_to_parquet(final_scores_df, "output_path_to_parquet")


In this case, coalesce(1) is used to reduce the number of partitions to 1, ensuring that the Parquet files are written efficiently without creating too many small files. If you have a large dataset, you might want to coalesce to a higher number of partitions, depending on the size and your performance needs.
Dmitry — Today at 11:54 AM
Solution:
from functools import lru_cache
from pathlib import Path
from pyspark.sql import Row
from pyspark.sql.functions import col, unix_timestamp, expr, to_timestamp, min, max

from pyspark import SparkContext
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    BooleanType,
    FloatType,
)


@lru_cache(maxsize=1)
def get_spark():
    sc = SparkContext(master="local[1]", appName="ML Logs Transformer")
    spark = SparkSession(sc)
    return spark


def load_logs(logs_path: Path) -> DataFrame:
    """
    Load logs from a given JSON file path and return a Spark DataFrame.

    This function reads a JSON file containing log data and converts it into a Spark DataFrame with a predefined schema.
    The schema includes the following fields:
        - logId: StringType
        - expId: IntegerType
        - metricId: IntegerType
        - valid: BooleanType
        - createdAt: StringType
        - ingestedAt: StringType
        - step: IntegerType
        - value: FloatType

    Args:
        logs_path (Path): The path to the JSON file containing the logs.

    Returns:
        DataFrame: A Spark DataFrame containing the logs data.
    """
    schema = StructType(
        [
            StructField("logId", StringType()),
            StructField("expId", IntegerType()),
            StructField("metricId", IntegerType()),
            StructField("valid", BooleanType()),
            StructField("createdAt", StringType()),
            StructField("ingestedAt", StringType()),
            StructField("step", IntegerType()),
            StructField("value", FloatType()),
        ]
    )
    logs_df = get_spark().read.json(str(logs_path), schema=schema)

    return logs_df


def load_experiments(experiments_path: Path) -> DataFrame:
    """
    Load experiments from a given CSV file path and return a Spark DataFrame.

    This function reads a CSV file containing experiment data and converts it into a Spark DataFrame with a predefined schema.
    The schema includes the following fields:
        - expId: IntegerType
        - expName: StringType

    Args:
        experiments_path (Path): The path to the CSV file containing the experiments.

    Returns:
        DataFrame: A Spark DataFrame containing the experiments data.
    """
    schema = StructType(
        [
            StructField("expId", IntegerType()),
            StructField("expName", StringType()),
        ]
    )
    
    experiments_df = get_spark().read.csv(str(experiments_path), schema=schema, header=True)

    return experiments_df


def load_metrics() -> DataFrame:
    """
    Load a dummy dataset of metrics and return a Spark DataFrame.

    This function creates a dummy dataset with predefined metric IDs and names, 
    then converts it into a Spark DataFrame with a predefined schema.
    The schema includes the following fields:
        - metricId: IntegerType
        - metricName: StringType

    Returns:
... (120 lines left)
Collapse
message.txt
8 KB
Dmitry — Today at 12:20 PM
@Max  @Aizhan  you can try to reproduce it
I see this example of value:
{"logId":"5f2d8f15ea79f5621549e397","expId":0,"metricId":0,"valid":false,"createdAt":"2020-07-19T12:35:38","ingestedAt":"2020-07-19T16:08:11","step":4,"value":0.1}

but there are more values that are smaller, and only difference is time difference, maybe the problem, that we need to do the time difference vice versa:) any way highly recommend to do this on your own
﻿
from functools import lru_cache
from pathlib import Path
from pyspark.sql import Row
from pyspark.sql.functions import col, unix_timestamp, expr, to_timestamp, min, max

from pyspark import SparkContext
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    BooleanType,
    FloatType,
)


@lru_cache(maxsize=1)
def get_spark():
    sc = SparkContext(master="local[1]", appName="ML Logs Transformer")
    spark = SparkSession(sc)
    return spark


def load_logs(logs_path: Path) -> DataFrame:
    """
    Load logs from a given JSON file path and return a Spark DataFrame.

    This function reads a JSON file containing log data and converts it into a Spark DataFrame with a predefined schema.
    The schema includes the following fields:
        - logId: StringType
        - expId: IntegerType
        - metricId: IntegerType
        - valid: BooleanType
        - createdAt: StringType
        - ingestedAt: StringType
        - step: IntegerType
        - value: FloatType

    Args:
        logs_path (Path): The path to the JSON file containing the logs.

    Returns:
        DataFrame: A Spark DataFrame containing the logs data.
    """
    schema = StructType(
        [
            StructField("logId", StringType()),
            StructField("expId", IntegerType()),
            StructField("metricId", IntegerType()),
            StructField("valid", BooleanType()),
            StructField("createdAt", StringType()),
            StructField("ingestedAt", StringType()),
            StructField("step", IntegerType()),
            StructField("value", FloatType()),
        ]
    )
    logs_df = get_spark().read.json(str(logs_path), schema=schema)

    return logs_df


def load_experiments(experiments_path: Path) -> DataFrame:
    """
    Load experiments from a given CSV file path and return a Spark DataFrame.

    This function reads a CSV file containing experiment data and converts it into a Spark DataFrame with a predefined schema.
    The schema includes the following fields:
        - expId: IntegerType
        - expName: StringType

    Args:
        experiments_path (Path): The path to the CSV file containing the experiments.

    Returns:
        DataFrame: A Spark DataFrame containing the experiments data.
    """
    schema = StructType(
        [
            StructField("expId", IntegerType()),
            StructField("expName", StringType()),
        ]
    )
    
    experiments_df = get_spark().read.csv(str(experiments_path), schema=schema, header=True)

    return experiments_df


def load_metrics() -> DataFrame:
    """
    Load a dummy dataset of metrics and return a Spark DataFrame.

    This function creates a dummy dataset with predefined metric IDs and names, 
    then converts it into a Spark DataFrame with a predefined schema.
    The schema includes the following fields:
        - metricId: IntegerType
        - metricName: StringType

    Returns:
        DataFrame: A Spark DataFrame containing the dummy metrics data.
    """
    schema = StructType(
        [
            StructField("metricId", IntegerType()),
            StructField("metricName", StringType()),
        ]
    )
    
    # Create a dummy dataset
    metrics = [
        Row(metricId=0, metricName="Loss"),
        Row(metricId=1, metricName="Accuracy")
    ]
    
    metrics_df = get_spark().createDataFrame(metrics, schema=schema)

    return metrics_df


def join_tables(
    logs: DataFrame, experiments: DataFrame, metrics: DataFrame
) -> DataFrame:
    """
    Join logs, experiments, and metrics DataFrames into a single DataFrame.

    This function performs the following joins:
        1. Join logs with experiments on expId.
        2. Join the result with metrics on metricId.

    Args:
        logs (DataFrame): The logs DataFrame.
        experiments (DataFrame): The experiments DataFrame.
        metrics (DataFrame): The metrics DataFrame.
    """
     # Join logs with experiments on expId
    logs_experiments = logs.join(experiments, on="expId", how="inner")

    # Join the result with metrics on metricId
    joined_tables = logs_experiments.join(metrics, on="metricId", how="inner")

    joined_tables = joined_tables.select(
                "logId",
                "expId",
                "expName",
                "metricId",
                "metricName",
                "valid",
                "createdAt",
                "ingestedAt",
                "step",
                "value"
                )

    return joined_tables


def filter_late_logs(data: DataFrame, hours: int) -> DataFrame:
    """
    Filter logs where the difference between 'createdAt' and 'ingestedAt' is greater than a specified number of hours.

    Args:
        data (DataFrame): The DataFrame containing the joined logs, experiments, and metrics.
        hours (int): The threshold in hours to filter late logs.

    Returns:
        DataFrame: A DataFrame containing only the logs where the time difference is greater than the specified hours.
    """
    # Convert the timestamp strings to timestamp type
    data = data.withColumn("createdAt_ts", to_timestamp(col("createdAt"), "yyyy-MM-dd'T'HH:mm:ss"))
    data = data.withColumn("ingestedAt_ts", to_timestamp(col("ingestedAt"), "yyyy-MM-dd'T'HH:mm:ss"))

    # Calculate the time difference in hours
    time_diff_col = (unix_timestamp(col("ingestedAt_ts")) - unix_timestamp(col("createdAt_ts"))) / 3600

    # Add the time difference column to the DataFrame
    data_with_time_diff = data.withColumn("time_diff_hours", time_diff_col)

    # Filter the DataFrame
    filtered_logs = data_with_time_diff.filter(col("time_diff_hours") > hours)

    return filtered_logs


def calculate_experiment_final_scores(data: DataFrame) -> DataFrame:
    """
    Calculate the final scores for each experiment and metric.

    This function calculates the minimum and maximum values for each metric in each experiment.
    The resulting DataFrame includes the following columns:
        - expName: name of the experiment,
        - metricName: name of the metric,
        - maxValue: maximum value of the metric in the experiment,
        - minValue: minimum value of the metric in the experiment.

    Args:
        data (DataFrame): The DataFrame containing the filtered logs with experiment and metric information.

    Returns:
        DataFrame: A DataFrame containing the final scores for each experiment and metric.
    """
    scores = data.groupBy("expId", "expName", "metricId", "metricName").agg(
        max("value").alias("maxValue"),
        min("value").alias("minValue")
    )

    return scores


def save(data: DataFrame, output_path: Path) -> None:
    """
    Save the DataFrame to Parquet format partitioned by metricId.

    Args:
        data (DataFrame): The DataFrame containing the final scores.
        output_path (str): The output path where the Parquet files will be saved.

    """
    data.write.partitionBy("metricId").parquet(str(output_path))
message.txt
8 KB

