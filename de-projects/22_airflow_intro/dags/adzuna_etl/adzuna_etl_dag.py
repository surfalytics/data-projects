from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.models import Variable
from datetime import datetime
from adzuna_etl.src.utils import get_adzuna_raw_data


"""
Home work

1. Split into modules and import them inside dag

2. Second approach (offload heavy job from airflow to outside)
create a new repo
inside repo, there should be docker container with repo code (ingestion / traformation logic)
save docker image into docker registry
inside dag, need to use docker executor to pull the image and start the container (and tasks are executed inside that container)

"""

# Shared folders mounted to all services to store raw and transformed data files
RAW_DATA_UNPROCESSED_FOLDER = "/opt/airflow/shared-data/raw_data/to_process/"

ADZUNA_APP_ID = Variable.get("ADZUNA_APP_ID")
ADZUNA_APP_KEY = Variable.get("ADZUNA_APP_KEY")


default_args = {
    "owner": "Maksim",
    "depends_on_past": False,
    "start_date": datetime(2025, 3, 30),
}


with DAG(
    dag_id = "adzuna_ingest_raw_data",
    default_args = default_args,
    description="Download data from Adzuna API",
    schedule= None #timedelta(hours=1) to run every hour; timedelta(days=1) to run every 24 hours
) as dag:
    
    extract_raw_data_task = PythonOperator(
        task_id = "extract_raw_data_task",
        python_callable = get_adzuna_raw_data,
        op_args = [ADZUNA_APP_ID, ADZUNA_APP_KEY, RAW_DATA_UNPROCESSED_FOLDER]
    )
    
    extract_raw_data_task
