"""
PyFlink Word Count Example
==========================

A basic PyFlink streaming application that reads text messages from a Kafka topic,
splits each message into words, counts the occurrences of each word using a tumbling
window, and prints the results.

This demonstrates:
    - Setting up a PyFlink StreamTableEnvironment
    - Creating Kafka source and print sink tables via Flink SQL
    - Running a continuous word count query with tumbling windows
    - Watermark-based event time processing

Prerequisites:
    - Kafka broker running at kafka:29092 (or localhost:9092)
    - A Kafka topic named 'words' with text messages
    - apache-flink Python package installed
    - Flink Kafka connector JAR in the classpath

Usage:
    python pyflink_wordcount.py

    Or submit to a Flink cluster:
    flink run -py pyflink_wordcount.py
"""

import os
import logging

from pyflink.table import EnvironmentSettings, TableEnvironment
from pyflink.table.expressions import col, lit

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
INPUT_TOPIC = os.environ.get("INPUT_TOPIC", "words")
CONSUMER_GROUP = "pyflink-wordcount"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pyflink_wordcount")


def create_kafka_source_ddl(table_name: str, topic: str, bootstrap_servers: str) -> str:
    """
    Generate the DDL statement to create a Kafka source table.

    The table has a single column 'line' containing the raw text from each
    Kafka message, plus a processing-time attribute for windowing.

    Args:
        table_name: Name of the Flink SQL table to create.
        topic: Kafka topic to consume from.
        bootstrap_servers: Kafka broker connection string.

    Returns:
        A CREATE TABLE DDL string.
    """
    return f"""
        CREATE TABLE {table_name} (
            `line` STRING,
            `proctime` AS PROCTIME()
        ) WITH (
            'connector' = 'kafka',
            'topic' = '{topic}',
            'properties.bootstrap.servers' = '{bootstrap_servers}',
            'properties.group.id' = '{CONSUMER_GROUP}',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'raw'
        )
    """


def create_print_sink_ddl(table_name: str) -> str:
    """
    Generate the DDL statement to create a print sink table.

    The print sink outputs results to stdout, which is useful for
    development and debugging.

    Args:
        table_name: Name of the Flink SQL sink table.

    Returns:
        A CREATE TABLE DDL string.
    """
    return f"""
        CREATE TABLE {table_name} (
            `word`         STRING,
            `window_start` TIMESTAMP(3),
            `window_end`   TIMESTAMP(3),
            `word_count`   BIGINT
        ) WITH (
            'connector' = 'print'
        )
    """


def create_kafka_sink_ddl(
    table_name: str, topic: str, bootstrap_servers: str
) -> str:
    """
    Generate the DDL statement to create a Kafka upsert sink table.

    Uses upsert-kafka connector so that updated word counts for the same
    window overwrite previous values.

    Args:
        table_name: Name of the Flink SQL sink table.
        topic: Kafka topic to write results to.
        bootstrap_servers: Kafka broker connection string.

    Returns:
        A CREATE TABLE DDL string.
    """
    return f"""
        CREATE TABLE {table_name} (
            `word`         STRING,
            `window_start` TIMESTAMP(3),
            `window_end`   TIMESTAMP(3),
            `word_count`   BIGINT,
            PRIMARY KEY (`word`, `window_start`) NOT ENFORCED
        ) WITH (
            'connector' = 'upsert-kafka',
            'topic' = '{topic}',
            'properties.bootstrap.servers' = '{bootstrap_servers}',
            'key.format' = 'json',
            'value.format' = 'json'
        )
    """


def run_wordcount() -> None:
    """
    Main entry point for the PyFlink word count pipeline.

    Steps:
        1. Create a streaming TableEnvironment.
        2. Register a Kafka source table (reads raw text lines).
        3. Register a print sink table (outputs word counts).
        4. Run a SQL query that:
           a. Splits each line into individual words using UNNEST.
           b. Groups words into 1-minute tumbling windows.
           c. Counts occurrences of each word per window.
        5. Inserts results into the sink, triggering continuous execution.
    """
    logger.info("Starting PyFlink Word Count pipeline")

    # Step 1: Create the streaming table environment
    env_settings = EnvironmentSettings.in_streaming_mode()
    t_env = TableEnvironment.create(env_settings)

    # Configure checkpointing for fault tolerance
    t_env.get_config().set("execution.checkpointing.interval", "60000")
    t_env.get_config().set("execution.checkpointing.mode", "EXACTLY_ONCE")
    t_env.get_config().set("parallelism.default", "2")

    # Step 2: Create the Kafka source table
    logger.info("Creating Kafka source table for topic '%s'", INPUT_TOPIC)
    t_env.execute_sql(
        create_kafka_source_ddl("words_source", INPUT_TOPIC, KAFKA_BOOTSTRAP_SERVERS)
    )

    # Step 3: Create the print sink table (for development output)
    logger.info("Creating print sink table")
    t_env.execute_sql(create_print_sink_ddl("wordcount_sink"))

    # Optionally create a Kafka sink as well
    t_env.execute_sql(
        create_kafka_sink_ddl(
            "wordcount_kafka_sink", "word-counts", KAFKA_BOOTSTRAP_SERVERS
        )
    )

    # Step 4 & 5: Run the word count query and insert into the sink
    #
    # The query uses:
    # - UNNEST with a CROSS JOIN to split each line into words
    # - TUMBLE window for 1-minute aggregation
    # - Processing time (proctime) since raw Kafka messages don't have
    #   embedded event timestamps
    logger.info("Submitting word count query")

    wordcount_query = """
        INSERT INTO wordcount_sink
        SELECT
            word,
            TUMBLE_START(proctime, INTERVAL '1' MINUTE) AS window_start,
            TUMBLE_END(proctime, INTERVAL '1' MINUTE)   AS window_end,
            COUNT(*)                                     AS word_count
        FROM (
            -- Split each line into individual words
            -- REGEXP_SPLIT_TO_TABLE is not available, so we use a lateral table
            SELECT word, proctime
            FROM words_source,
                 LATERAL TABLE(STRING_SPLIT(LOWER(TRIM(line)), ' ')) AS T(word)
            WHERE TRIM(word) <> ''
        )
        GROUP BY
            TUMBLE(proctime, INTERVAL '1' MINUTE),
            word
    """

    # Execute the query -- this submits the job to the Flink cluster
    result = t_env.execute_sql(wordcount_query)
    logger.info("Word count job submitted. Job ID: %s", result.get_job_client().get_job_id())

    # Wait for the job to finish (in streaming mode, this runs until cancelled)
    logger.info("Waiting for job to complete (Ctrl+C to cancel)...")
    result.wait()


if __name__ == "__main__":
    run_wordcount()
