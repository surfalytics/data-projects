import json
import os
import requests
from datetime import datetime
import math
import boto3
import logging


# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Getting Adzuna API creds
ADZUNA_APP_ID = os.getenv('ADZUNA_APP_ID')
ADZUNA_APP_KEY = os.getenv('ADZUNA_APP_KEY')
BUCKET = "adzuna-etl-project"

# Define the API endpoint and base parameters
url = "https://api.adzuna.com/v1/api/jobs/ca/search/"
base_params = {
    'app_id': ADZUNA_APP_ID,
    'app_key': ADZUNA_APP_KEY,
    'results_per_page': 50,  # Maximum allowed results per page
    'what_phrase': "data engineer",
    'max_days_old': 2,
    'sort_by': "date"
}


def lambda_handler(event, context):

    # Initialize a list to store all job postings
    all_job_postings = []
    
    # Make the first request to determine the total number of pages
    logger.info("Making the first request to determine the total number of pages")
    response = requests.get(f"{url}1", params=base_params)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()  # Parse the JSON response
        total_results = data['count']  # Get the total number of results
        results_per_page = base_params['results_per_page']
        
        # Calculate the total number of pages
        total_pages = math.ceil(total_results / results_per_page)
        logger.info(f"Total number of page = {total_pages}")
        
        # Store the results from the first page
        all_job_postings.extend(data['results'])
    
        # Loop through the remaining pages and request data from each
        logger.info("Looping through the remaining pages and request data from each")
        for page in range(2, total_pages + 1):  # Start from page 2 to total_pages
            response = requests.get(f"{url}{page}", params=base_params)
            
            # Check if the request was successful
            if response.status_code == 200:
                page_data = response.json()
                # Append job postings from this page to the list
                all_job_postings.extend(page_data['results'])
            else:
                logger.error(f"Error fetching page {page}: {response.status_code}, {response.text}")
    else:
        logger.error(f"Error: {response.status_code}, {response.text}")
    
    # Now all_job_postings contains data from all pages
    logger.info(f"Total jobs retrieved: {len(all_job_postings)}")
    
    # Generate a filename with the current timestamp
    current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"adzuna_raw_data_{current_timestamp}.json"
    logger.info(f"File name to store raw data: {file_name}")
    
    # Storing Spotify json raw data to AWS S3
    logger.info("Storing Adzuna json raw data to AWS S3")
    client = boto3.client('s3')
    file_key = f"raw_data/to_process/{file_name}"
    try:
        client.put_object(
            Bucket=BUCKET,
            Key=file_key,
            Body=json.dumps(all_job_postings)
        )
        logger.info(f"File {file_key} successfully created in bucket {BUCKET}.")
        return file_key
    
    except Exception as e:
        logger.error(f"Error occurred while creating file: {str(e)}")
        return None
