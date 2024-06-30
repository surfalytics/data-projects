from functools import lru_cache
from pathlib import Path

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
    TODO(Part 1.1): Complete this method
    """
    logs = []
    return get_spark().createDataFrame(
        logs,
        StructType(
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
        ),
    )


def load_experiments(experiments_path: Path) -> DataFrame:
    """
    TODO(Part 1.2): Complete this method
    """
    experiments = []
    return get_spark().createDataFrame(
        experiments,
        StructType(
            [StructField("expId", IntegerType()), StructField("expName", StringType())]
        ),
    )


def load_metrics() -> DataFrame:
    """
    TODO(Part 1.3): Complete this method
    """
    metrics = []
    return get_spark().createDataFrame(
        metrics,
        StructType(
            [
                StructField("metricId", IntegerType()),
                StructField("metricName", StringType()),
            ]
        ),
    )


def join_tables(
    logs: DataFrame, experiments: DataFrame, metrics: DataFrame
) -> DataFrame:
    """
    TODO(Part 2): Complete this method
    """
    joined_tables = []
    return get_spark().createDataFrame(
        joined_tables,
        StructType(
            [
                StructField("logId", StringType()),
                StructField("expId", IntegerType()),
                StructField("expName", StringType()),
                StructField("metricId", IntegerType()),
                StructField("metricName", StringType()),
                StructField("valid", BooleanType()),
                StructField("createdAt", StringType()),
                StructField("ingestedAt", StringType()),
                StructField("step", IntegerType()),
                StructField("value", FloatType()),
            ]
        ),
    )


def filter_late_logs(data: DataFrame, hours: int) -> DataFrame:
    """
    TODO(Part 3): Complete this method
    """
    filtered_logs = []
    return get_spark().createDataFrame(
        filtered_logs,
        StructType(
            [
                StructField("logId", StringType()),
                StructField("expId", IntegerType()),
                StructField("expName", StringType()),
                StructField("metricId", IntegerType()),
                StructField("metricName", StringType()),
                StructField("valid", BooleanType()),
                StructField("createdAt", StringType()),
                StructField("ingestedAt", StringType()),
                StructField("step", IntegerType()),
                StructField("value", FloatType()),
            ]
        ),
    )


def calculate_experiment_final_scores(data: DataFrame) -> DataFrame:
    """
    TODO(Part 4): Complete this method
    """
    scores = []
    return get_spark().createDataFrame(
        scores,
        StructType(
            [
                StructField("expId", IntegerType()),
                StructField("metricId", IntegerType()),
                StructField("expName", StringType()),
                StructField("metricName", StringType()),
                StructField("maxValue", FloatType()),
                StructField("minValue", FloatType()),
            ]
        ),
    )


def save(data: DataFrame, output_path: Path):
    """
    TODO(Part 5): Complete this method
    """
    pass
