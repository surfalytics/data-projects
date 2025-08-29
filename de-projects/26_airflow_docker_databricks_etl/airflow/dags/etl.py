from etl_config import config
from airflow.decorators import task
from airflow.models import DAG, Variable
from scripts.src import fetch_adzuna_to_spark_df, merge_to_delta_table, get_spark, get_table_records_cnt
import logging


with DAG(
    "adzuna_etl_dag",
    max_active_runs = config.max_active_runs,
    schedule = config.schedule,
    start_date = config.start_date,
    end_date = config.end_date,
    catchup = config.catchup,
    tags = ["adzuna"]
) as dag:

    @task
    def load_adzuna_jobs():
        spark = get_spark()
        df = fetch_adzuna_to_spark_df(
            spark, 
            adzuna_app_id=Variable.get("ADZUNA_APP_ID"),
            adzuna_app_key=Variable.get("ADZUNA_APP_KEY"),
            max_days_old=3
        )
        logging.info(f"number of fetched records from Adzuna = {df.count()}")

        # Building adzuna table fully qualified name
        table_fqn = f"{config.target_catalog}.{config.target_schema}.{config.adzuna_table_name}"
        logging.info(f"Adzuna table fully qualified name: '{table_fqn}'")

        logging.info("Merging fetched data into databricks delta table")
        merge_to_delta_table(spark, df, table_fqn)

        table_records_cnt = get_table_records_cnt(spark, table_fqn)
        logging.info(f"Number of records after merge: {table_records_cnt}")

        logging.info("Closing spark session")
        if spark:
            spark.stop()
        
        logging.info("Done")

    load_task = load_adzuna_jobs()
