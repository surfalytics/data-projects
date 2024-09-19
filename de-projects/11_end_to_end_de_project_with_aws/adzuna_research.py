import json
import os
import requests
from datetime import datetime
import math
from loguru import logger
import pandas as pd


ADZUNA_APP_ID = os.getenv('ADZUNA_APP_ID')
ADZUNA_APP_KEY = os.getenv('ADZUNA_APP_KEY')

# Define the API endpoint and base parameters
url = "https://api.adzuna.com/v1/api/jobs/ca/search/"
base_params = {
    'app_id': ADZUNA_APP_ID,
    'app_key': ADZUNA_APP_KEY,
    'results_per_page': 50,  # Maximum allowed results per page
    'what_phrase': "data engineer", # an entire phrase which must be found in the description or title
    'max_days_old': 2,
    'sort_by': "date"
}

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


# Transformation: picking up only necessary fields
parsed_jobs = []
for job in all_job_postings:
      parsed_jobs.append(
        dict(
            job_id = job['id'],
            job_title = job['title'],
            job_location = job['location']['display_name'],
            job_company = job['company']['display_name'],
            job_category = job['category']['label'],
            job_description = job['description'],
            job_url = job['redirect_url'],
            job_created = job['created']
        )
      )

jobs_df = pd.DataFrame.from_dict(parsed_jobs)
jobs_df['job_created'] = pd.to_datetime(jobs_df['job_created'])

logger.info("Done")
