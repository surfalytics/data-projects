import os
from munch import Munch
from airflow.models import Variable
from datetime import datetime, timezone


airflow_env = os.getenv("AIRFLOW_ENV", "local")
config = {}

# local / sandbox
if airflow_env in ("local"):
    config.update({
        # airflow params
        "schedule": "@hourly",
        "start_date": datetime(2025, 8, 24, 0, 0, 0, tzinfo=timezone.utc),  # timezone-aware
        "end_date": None,
        "catchup": False,
        "max_active_runs": 1,

        # adzuna api params
        "adzuna_app_id": Variable.get("ADZUNA_APP_ID"),
        "adzuna_app_key": Variable.get("ADZUNA_APP_KEY"),

        # databricks params
        "databricks_conn_id": "databricks_default",
        "target_catalog": "adzuna",
        "target_schema": "prj",
        "adzuna_table_name": "jobs"
    })


# clean up local variables
del airflow_env

# export as munch
config = Munch(config)
