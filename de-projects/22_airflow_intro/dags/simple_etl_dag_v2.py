from airflow.decorators import task, dag
from datetime import datetime
import logging

@dag(
    dag_id=f'simple_etl_dag_v2',
    description='A simple ETL DAG V2 with decorators',
    start_date=datetime(2025, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def etl():
    @task
    def extract():
        logging.info("Extracting data...")
        return "dummy data"

    @task
    def transform(raw_data: str):
        transformed_data = raw_data.upper()
        logging.info(f"Transforming data: {transformed_data}")
        return transformed_data

    @task
    def load(transformed_data: str):
        logging.info(f"Loading data: {transformed_data}")

    @task.bash
    def monitor():
        return "echo $AIRFLOW__CORE__EXECUTOR"

    raw = extract()
    transformed = transform(raw)
    load(transformed) >> monitor()


dag = etl()
