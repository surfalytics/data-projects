-- Create a new schema in PostgreSQL database
CREATE SCHEMA migration;


-- Create table in PostgreSQL database to host generated sales data
CREATE TABLE migration.sales_data (
    row_id INT PRIMARY KEY,
    order_id VARCHAR(255),
    order_date DATE,
    ship_date DATE,
    ship_mode VARCHAR(50),
    customer_id VARCHAR(50),
    customer_name VARCHAR(255),
    segment VARCHAR(50),
    country VARCHAR(50),
    city VARCHAR(50),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    region VARCHAR(50),
    product_id VARCHAR(255),
    category VARCHAR(50),
    sub_category VARCHAR(50),
    product_name VARCHAR(255),
    sales NUMERIC(10, 2),
    quantity INT,
    discount NUMERIC(5, 2),
    profit NUMERIC(10, 2)
);


-- Load the data into the created table
COPY migration.sales_data
FROM '/docker-entrypoint-initdb.d/data/sales_data.csv' -- specify your path to the file here
DELIMITER ','
CSV HEADER;


-- Check all the data rows were imported. It should be 3,000,000
-- SELECT COUNT(*)
-- FROM migration.sales_data;


-- Check the data
-- SELECT *
-- FROM migration.sales_data
-- LIMIT 10;