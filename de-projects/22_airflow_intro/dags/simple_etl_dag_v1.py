from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import logging


def extract():
    logging.info("Extracting data...")
    return "raw_data"


def transform(ti):
    raw_data = ti.xcom_pull(task_ids='extract_task')
    transformed_data = raw_data.upper()
    logging.info(f"Transforming data: {transformed_data}")
    return transformed_data


def load(ti):
    transformed_data = ti.xcom_pull(task_ids='transform_task')
    logging.info(f"Loading data: {transformed_data}")


# Define the DAG
with DAG(
    dag_id='simple_etl_dag_v1',
    description='A simple ETL DAG',
    start_date=datetime(2025, 1, 1),
    schedule_interval='@daily',
) as dag:

    # Define tasks
    extract_task = PythonOperator(
        task_id='extract_task',
        python_callable=extract
    )

    transform_task = PythonOperator(
        task_id='transform_task',
        python_callable=transform
    )

    load_task = PythonOperator(
        task_id='load_task',
        python_callable=load
    )

    monitoring_task = BashOperator(
        task_id='monitoring_task',
        bash_command="echo $AIRFLOW__CORE__EXECUTOR"
    )

    # Set task dependencies
    extract_task >> transform_task >> load_task >> monitoring_task
