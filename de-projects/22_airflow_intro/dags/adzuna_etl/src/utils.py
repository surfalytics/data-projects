from datetime import datetime
import pandas as pd
import requests
import json
import math
import os


def get_adzuna_raw_data(ADZUNA_APP_ID, ADZUNA_APP_KEY, RAW_DATA_UNPROCESSED_FOLDER):

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
    print("Adzuna Function triggered to extract raw json data from Adzuna API.")

    # Initialize a list to store all job postings
    all_job_postings = []
    
    # Make the first request to determine the total number of pages
    print("Making the first request to determine the total number of pages")
    response = requests.get(f"{url}1", params=base_params)
    
    if response.status_code != 200:
        error_message = f"Error fetching page 1: {response.status_code}, {response.text}"
        print(error_message)

    data = response.json()  # Parse the JSON response
    total_results = data.get('count', 0)
    results_per_page = base_params['results_per_page']

    # Calculate the total number of pages
    total_pages = math.ceil(total_results / results_per_page)
    print(f"Total number of pages = {total_pages}")

    # Store the results from the first page
    all_job_postings.extend(data.get('results', []))

    # Loop through the remaining pages and request data from each
    print("Looping through the remaining pages to request data from each")
    for page in range(2, total_pages + 1):  # Start from page 2
        response = requests.get(f"{url}{page}", params=base_params)
        if response.status_code == 200:
            page_data = response.json()
            all_job_postings.extend(page_data.get('results', []))
        else:
            print(f"Error fetching page {page}: {response.status_code}, {response.text}")

    print(f"Total jobs retrieved: {len(all_job_postings)}")

    raw_json_data = json.dumps({"items": all_job_postings})
    raw_json_bytes = raw_json_data.encode('utf-8')

    # Generate a filename with the current timestamp to store raw data
    # Create RAW_DATA_UNPROCESSED_FOLDER if it doesn't exist
    os.makedirs(RAW_DATA_UNPROCESSED_FOLDER, exist_ok=True) 
    current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"adzuna_raw_data_{current_timestamp}.json"
    file_path = RAW_DATA_UNPROCESSED_FOLDER + file_name
    print(f"File name to store raw data: {file_path}")

    with open(file_path, "wb") as file:
        file.write(raw_json_bytes)
    print("Done")

    return file_path
