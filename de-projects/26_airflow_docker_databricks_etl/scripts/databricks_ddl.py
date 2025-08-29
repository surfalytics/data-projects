# Init scripts to create catalog, schema and table in databricks

from scripts.src import get_spark
import logging


try:
    logging.info("Getting spark session")
    spark = get_spark()

    logging.info("Creating catalog")
    spark.sql("CREATE CATALOG adzuna")

    logging.info("Creating schema")
    spark.sql("CREATE SCHEMA adzuna.prj")

    logging.info("Creating table")
    spark.sql("""
        CREATE TABLE adzuna.prj.jobs (
            id BIGINT,
            title STRING,
            location STRING,
            company STRING,
            category STRING,
            description STRING,
            url STRING,
            created TIMESTAMP,
            etl_at TIMESTAMP
        )
        USING DELTA
    """)

    logging.info("Closing spark session")
    try:
        if spark:
            spark.stop()
    except Exception as e:
        logging.warning(f"Error while stopping Spark session: {e}")

    logging.info("Done")

except Exception as e:
    logging.error(f"Error when executing databricks ddl: {e}")

# docker compose exec -T airflow-scheduler python /opt/python/scripts/databricks_ddl.py
