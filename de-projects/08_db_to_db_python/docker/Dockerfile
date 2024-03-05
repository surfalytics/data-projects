# Use the official PostgreSQL image as a parent image
FROM postgres:latest

# Set environment variables (optional)
ENV POSTGRES_DB=sales
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=1

# Copy the initialization sql script for Postgres
COPY ./init-scripts/ /docker-entrypoint-initdb.d/

# Copy the CSV file to be loaded in Postgres
COPY ./source-data/sales_data.csv /docker-entrypoint-initdb.d/data/