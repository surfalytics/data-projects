#!/bin/bash

# Exit on any error
set -e

# Create output directory if it doesn't exist
mkdir -p output

# Define data source (replace with your preferred open data source)
DATA_URL="https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"
DATA_FILE="/app/covid_data.csv"

# Download data
echo "Downloading data from ${DATA_URL}..."
wget -O "${DATA_FILE}" "${DATA_URL}"

# Create a DuckDB databasev
DB_FILE="/app/analysis.db"

# SQL file
SQL_FILE="/app/queries/analysis.sql"

# Perform analysis using DuckDB CLI and the SQL file
echo "Analyzing data with DuckDB..."
duckdb "${DB_FILE}" -c ".read ${SQL_FILE}"

# Display results
echo "\nAnalysis complete. Results saved in /app/output/top_20_locations.csv."
echo "\nTop 5 locations by total cases:"
head -n 6 /app/top_20_locations.csv