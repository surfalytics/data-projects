import boto3
import os
import logging
from botocore.exceptions import ClientError


# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Redshift creds
REDSHIFT_REGION = 'us-east-1'  # Change to the region your Redshift Serverless is in
REDSHIFT_WORKGROUP = 'adzuna-etl-project-redshift-wg'  
REDSHIFT_SECRET_ARN = os.getenv('REDSHIFT_SECRET_ARN')
REDSHIFT_IAM_ROLE = os.getenv('REDSHIFT_IAM_ROLE')

# Initialize the Secrets Manager client
session = boto3.session.Session()

# Initialize the Redshift Data API client
client_redshift = session.client('redshift-data', region_name=REDSHIFT_REGION)

# SQL query template to import csv files from s3 and merge data from staging to dw table
QUERY_TEMPLATE = """
BEGIN;

TRUNCATE TABLE adzuna.stg.staging_jobs;

COPY adzuna.stg.staging_jobs 
FROM '{s3_uri}' 
IAM_ROLE '{iam_role}' 
FORMAT AS CSV DELIMITER ',' QUOTE '"' IGNOREHEADER 1 
REGION AS '{region}';

INSERT INTO adzuna.dw.jobs
SELECT stj.*    
FROM adzuna.stg.staging_jobs stj
LEFT JOIN adzuna.dw.jobs dwj ON stj.job_id = dwj.job_id
WHERE dwj.job_id IS NULL;

COMMIT;
"""

# Function to execute query in Redshift
def execute_redshift_query(query_str, database='adzuna'):
    try:
        logger.info(f"Executing SQL query: {query_str}")
        response = client_redshift.execute_statement(
            Database=database,  # Redshift database name
            SecretArn=REDSHIFT_SECRET_ARN,
            Sql=query_str,
            WorkgroupName=REDSHIFT_WORKGROUP  # Redshift Serverless workgroup name
        )
        logger.info("Query executed successfully")
        logger.info(f"Response: {response}")
    
    except ClientError as e:
        logger.error(f"Error executing query: {e}")
        raise e
    
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        raise e

# Function to delete object from s3 bucket
def delete_s3_object(bucket_name, object_key):
    s3_client = boto3.client('s3')
    try:
        # Delete the object
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        logger.info(f"File {object_key} deleted successfully from bucket {bucket_name}.")

    except Exception as e:
        logger.error(f"Error occurred while deleting file: {str(e)}")

# Function to move object to another folder in s3 bucket
def move_s3_object(bucket, source_key, destination_key):
    logger.info(f"Started moving {source_key} to 'migrated' folder in s3 ...")
    s3_client = boto3.client('s3')
    try:
        # Copy the object
        s3_client.copy_object(
            Bucket=bucket,
            CopySource={'Bucket': bucket, 'Key': source_key},
            Key=destination_key
        )
        logger.info(f"File copied from {source_key} to {destination_key} successfully.")
        delete_s3_object(bucket, source_key)

    except Exception as e:
        logger.error(f"Error occurred while copying file: {str(e)}")


def lambda_handler(event, context):
    # Get the S3 object key from the Step Function input
    s3_object = event['s3ObjectKeyTransformed']  # Input from previous function (Step Function)
    
    s3_bucket = "adzuna-etl-project" 
    s3_uri = f's3://{s3_bucket}/{s3_object}'
    
    logger.info(f"S3 URI of transformed file: {s3_uri}")
        
    query = QUERY_TEMPLATE.format(s3_uri=s3_uri, iam_role=REDSHIFT_IAM_ROLE, region=REDSHIFT_REGION)
    logger.info(f"Redshift query to execute: {query}")

    logger.info("Started importing data from csv file in s3 and merging to dw table")
    execute_redshift_query(query_str=query)
    
    # Moving migrated file to another folder in s3
    source_key = s3_object
    source_file_name = source_key.split('/')[2]
    destination_key = "transformed_data/migrated/" + source_file_name
    move_s3_object(s3_bucket, source_key, destination_key)
