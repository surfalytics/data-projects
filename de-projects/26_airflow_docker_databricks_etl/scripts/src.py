from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, to_timestamp, current_timestamp
from airflow.providers.databricks.hooks.databricks import DatabricksHook
from databricks.connect import DatabricksSession
import math
import requests
import logging


def get_spark():
    """ Get remote Spark session """
    conn = DatabricksHook().get_conn()

    logging.info("Using serverless compute")
    return DatabricksSession.builder.remote(
        host=conn.host,
        token=conn.password,
        serverless=True
    ).getOrCreate()


def fetch_adzuna_to_spark_df(
    spark: SparkSession,
    adzuna_app_id: str,
    adzuna_app_key: str,
    *,
    what_phrase: str = "data engineer",
    country: str = "ca",
    max_days_old: int = 1,
    sort_by: str = "date",
    results_per_page: int = 50,
    request_timeout: int = 30,
):
    """ Fetch Adzuna job postings directly into a Spark DataFrame """

    # Base URL and params
    base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/"
    base_params = {
        "app_id": adzuna_app_id,
        "app_key": adzuna_app_key,
        "results_per_page": results_per_page,
        "what_phrase": what_phrase,
        "max_days_old": max_days_old,
        "sort_by": sort_by,
    }

    session = requests.Session()

    # Page 1 to get count / first results
    logging.info("Fetching number of available jobs")
    r = session.get(f"{base_url}1", params=base_params, timeout=request_timeout)
    if r.status_code != 200:
        raise RuntimeError(f"Error fetching page 1: {r.status_code}, {r.text}")

    payload = r.json()
    total_results = int(payload.get("count", 0))
    logging.info(f"Number of available records = {total_results}")
    first_results = payload.get("results", [])

    # Compute total pages and cap with max_pages if provided
    total_pages = math.ceil(total_results / results_per_page) if results_per_page > 0 else 0
    logging.info(f"Number of total pages = {total_pages}")

    all_results = list(first_results)

    # Remaining pages (if any)
    for page in range(2, max(2, total_pages + 1)):
        logging.info(f"Processing page = {page} ...")
        rp = session.get(f"{base_url}{page}", params=base_params, timeout=request_timeout)
        if rp.status_code != 200:
            logging.error(f"Warning: error fetching page {page}: {rp.status_code}, {rp.text}")
            continue
        page_payload = rp.json()
        all_results.extend(page_payload.get("results", []))

    # Flatten into list of dicts
    def _flat(job: dict):
        loc = (job.get("location") or {})
        comp = (job.get("company") or {})
        cat = (job.get("category") or {})
        return {
            "id": str(job.get("id") or ""),
            "title": job.get("title"),
            "location": loc.get("display_name"),
            "company": comp.get("display_name"),
            "category": cat.get("label"),
            "description": job.get("description"),
            "url": job.get("redirect_url"),
            "created": job.get("created"),
        }

    parsed = [_flat(j) for j in all_results]
    logging.info(f"Number of parsed records = {len(parsed)}")

    # Handle empty result
    if not parsed:
        return None

    df = spark.createDataFrame(parsed)

    # Dedupe, cast created -> timestamp, add elt_updated
    df = (
        df.dropDuplicates(["id"])
          .withColumn("id", col("id").cast("bigint"))
          .withColumn("created", to_timestamp(col("created")))
          .withColumn("elt_updated", current_timestamp())
    )
    logging.info("Finished fetching Adzuna jobs")
    return df


def merge_to_delta_table(spark: SparkSession, df: DataFrame, table_fqn: str):
    df.createOrReplaceTempView("temp_view_adzuna_jobs")
    spark.sql(f"""
        MERGE INTO {table_fqn} AS t
        USING (
        SELECT
            id,
            title,
            location,
            company,
            category,
            description,
            url,
            created
        FROM temp_view_adzuna_jobs
        ) AS s
        ON t.id = s.id

        -- Update only if something actually changed
        WHEN MATCHED AND (
            t.title       <=> s.title OR
            t.location    <=> s.location OR
            t.company     <=> s.company OR
            t.category    <=> s.category OR
            t.description <=> s.description OR
            t.url         <=> s.url OR
            t.created     <=> s.created
        )
        THEN UPDATE SET
            t.title       = s.title,
            t.location    = s.location,
            t.company     = s.company,
            t.category    = s.category,
            t.description = s.description,
            t.url         = s.url,
            t.created     = s.created,
            t.etl_at      = current_timestamp()

        -- Insert if not matched
        WHEN NOT MATCHED THEN INSERT (
            id,
            title,
            location,
            company,
            category,
            description,
            url,
            created,
            etl_at
        ) VALUES (
            s.id,
            s.title,
            s.location,
            s.company,
            s.category,
            s.description,
            s.url,
            s.created,
            current_timestamp()
        )
    """)


def get_table_records_cnt(spark: SparkSession, table_fqn: str):
    """ Returns number of records in Databricks delta table """
    return spark.sql(f"select count(*) from {table_fqn}").collect()[0][0]
