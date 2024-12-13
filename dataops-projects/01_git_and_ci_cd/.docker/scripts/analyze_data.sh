#!/bin/bash

# Exit on any error
set -e

# Create output directory if it doesn't exist
mkdir -p output

# Define data source (replace with your preferred open data source)
DATA_URL="https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"
DATA_FILE="/tmp/covid_data.csv"

# Download data
echo "Downloading data from ${DATA_URL}..."
wget -O "${DATA_FILE}" "${DATA_URL}"

# Create a DuckDB databasev
DB_FILE="/tmp/analysis.db"

# Perform analysis using DuckDB CLI
echo "Analyzing data with DuckDB..."
duckdb "${DB_FILE}" << EOF

-- Basic analysis queries
CREATE TABLE covid_data AS SELECT * FROM read_csv_auto('${DATA_FILE}');

-- Total cases and deaths by location
CREATE VIEW location_summary AS 
SELECT 
    location, 
    MAX(total_cases) as max_total_cases,
    MAX(total_deaths) as max_total_deaths,
    MAX(total_cases_per_million) as max_cases_per_million
FROM covid_data
WHERE continent IS NOT NULL
GROUP BY location
ORDER BY max_total_cases DESC
LIMIT 20;

-- Output results to CSV
COPY (SELECT * FROM location_summary) 
TO '/app/output/top_20_locations.csv' 
WITH (HEADER, DELIMITER ',');

-- Generate some statistics
SELECT 
    COUNT(DISTINCT location) as total_locations,
    MIN(date) as earliest_date,
    MAX(date) as latest_date
FROM covid_data
WHERE continent IS NOT NULL;
EOF

# Display results
echo "\nAnalysis complete. Results saved in /app/output/top_20_locations.csv."
echo "\nTop 5 locations by total cases:"
head -n 6 /app/output/top_20_locations.csv