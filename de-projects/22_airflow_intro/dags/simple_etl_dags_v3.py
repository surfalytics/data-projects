from airflow.decorators import task, dag
from datetime import datetime
import logging


def make_etl_dag(table_name: str):
    @dag(
        dag_id=f'simple_etl_dag_{table_name}',
        description='A simple ETL DAG V2',
        start_date=datetime(2025, 1, 1),
        schedule_interval='@daily',
        catchup=False
    )
    def etl():
        @task(task_id=f"extract_{table_name}")
        def extract():
            logging.info("Extracting data...")
            return table_name

        @task(task_id=f"transform_{table_name}")
        def transform(raw_data: str):
            transformed_data = raw_data.upper()
            logging.info(f"Transforming data: {transformed_data}")
            return transformed_data

        @task(task_id=f"load_{table_name}")
        def load(transformed_data: str):
            logging.info(f"Loading data: {transformed_data}")

        raw = extract()
        transformed = transform(raw)
        load(transformed)

    return etl()


TABLES = ['accounts', 'contacts', 'sales']

for table in TABLES:
    make_etl_dag(table)
