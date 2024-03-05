# Importing, exporting and transferring data between PostgreSQL and Snowflake using Python and Pandas

## Project goal
Give understanding and practical experience on how to read data from database tables to Pandas dataframe and write it back.

## Use cases
 - Test assignment during job application for DA/DE roles
 - Data transformation where it’s hard or impossible to use SQL
 - Migrating data between different databases


## Prerequisites
Ensure you have the following software installed on your laptop:
 - git
 - Python
 - Docker
 - DBeaver
 - Visual Studio Code (dark theme and extensions: Python, Jupyter, Rainbow CSV)
 - Account in Snowflake

## Project tasks
1. Clone the repo and access it using VS Code
2. Generate data
3. Load data to PostgreSQL
4. Read data from PostgreSQL to Pandas dataframe
5. Modify data in Pandas dataframe and write it back to PostgreSQL
6. Speed up export to PostgreSQL
7. Read data from Snowflake to Pandas dataframe
8. Transfer data from PostgreSQL to Snowflake

### Task 1. Clone the repo and access it using VS Code

#### Expected result / definition of done:
 - Project downloaded from github
 - Project is opened in VS Code

#### Steps:
 - Open the folder where you want to locate the project repo

 - Run the terminal inside the folder and clone the project repo

`git clone https://github.com/surfalytics/data-projects.git`

 - Open VS Code and navigate to the cloned project folder

 - Double-check you installed Python, Jupyter, Rainbow CSV extensions for VS Code


### Task 2. Generate data

#### Expected result / definition of done:
 - Generated `sales_data.csv` file in the `./docker/source-data/` folder

#### Steps:
 - In the `docker` folder, create `source-data` subfolder
 - Run the `generate_data.py` file
 - Ensure the `csv` file is created
 - Open it in VS Code to observe it and see how the Rainbow CSV extension works


### Task 3. Load data to PostgreSQL

#### Expected result / definition of done:
 - Generated csv file is exported to the PostgreSQL database
 - You accessed the database using DBeaver and checked # of rows = 3 mln and data is correct

#### Steps:
 - Launch Docker Desktop application
 - Open terminal in VS Code and navigate to the docker directory
 - Run the following command to build the docker image

`docker build -t postgres-image .`

 - Check the `postgres-image` image is created

`docker image list`

 - Run the following command to run a container

`docker run --name postgres-cont -d -p 5433:5432 postgres-image`

 - Check the `postgres-cont` is created

`docker ps`

 - Open DBeaver application

 - Create new connection (to the newly created PostgreSQL database in Docker)
 - Click New Connection > Select PostgreSQL and fill in the settings:
```
Host: localhost
Port: 5433
Database: sales
Username: postgres
Password: 1
```

 - Click `Test Connection`. In case of success, you should see `Connected`. If so, click `Finish`

 - In DBeaver, in the newly created connection, ensure you see the `sales` database, the `migration` schema, the `sales_data` table inside it.

 - Open SQL Editor and run the following queries:

`SELECT COUNT(*) FROM migration.sales_data;`

You should see 3,000,000 as a result

 - Run the following query to observe the imported data:

`SELECT * FROM migration.sales_data LIMIT 100;`

It’s just to ensure the data is imported and looks as expected


### Task 4. Read data from PostgreSQL to Pandas dataframe

#### Expected result / definition of done:
 - Data from PostgreSQL is imported to Pandas dataframe and printed to the screen.


#### Steps:

 - In VS Code, open terminal

 - Create virtual environment for the project:

`python -m venv project_venv`

 - Activate the environment:

`.\project_venv\Scripts\activate`

 - Install requires python packages:

`pip install pandas sqlalchemy psycopg2-binary "snowflake-connector-python[pandas]"`


 - Navigate to the `migration.ipynb` file. Ensure it’s properly displayed.

 - Set the kernel to use the newly created `project_venv` environment

 - Run the first cell

 - Ensure you can see the displayed Pandas dataframe with the data from PostgreSQL


### Task 5. Modify data in Pandas dataframe and write it back to PostgreSQL

### Expected result / definition of done:
 - The new Pandas dataframe created and it contains the new `shipping_duration` calculated column 
 - You printed the new dataframe
 - You wrote the data from the new dataframe back to PostgreSQL

#### Steps:

 - Run the second cell

 - Ensure you see printed dataframe and it contains the new `shipping_duration` column

 - Uncomment the last line in the cell and run the cell again

 - Track the time how long it took to execute the code in the cell. Later, we will try to speed it up. 

 - In DBeaver, refresh the tables and check if the new `updated_sales_data` table appeared.

 - Check the number of rows and print the first 100 rows to check if the new `shipping_duration` column is there


### Task 6. Speed up export to PostgreSQL

#### Expected result / definition of done:
 - It take noticeably less time to upload data from Pandas dataframe to Pandas dataframe

#### Steps:
In DBeaver, create schema for the updated table by running the following SQL:

``` sql
CREATE TABLE migration.fast_updated_sales_data (
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
   profit NUMERIC(10, 2),
   shipping_duration INT
);
```

 - Run the third cell in the `migration.ipynb` file

 - Track the execution time and compare it to the time in the previous step. 

 - In DBeaver, check if the `fast_updated_sales_data` table was populated.


### Task 7. Read data from Snowflake to Pandas dataframe

#### Expected result / definition of done:
 - Data from Snowflake is imported to Pandas dataframe and printed to the screen


#### Steps:

 - Log in to your Snowflake account

 - In VS Code, open the `migration.ipynb` file and go the the fourth cell

- Update the connection credentials using your account data

 - Run the fourth cell. If everything was done correctly, you should see the table data from Snowflake


### Task 8. Transfer data from PostgreSQL to Snowflake

#### Expected result / definition of done:
- Data from PostgreSQL is uploaded to Snowflake


#### Steps:

 - In Snowflake, create your personal database and schema
 ``` sql
CREATE DATABASE IF NOT EXISTS <your_name>_MIGRATION;
CREATE SCHEMA IF NOT EXISTS <your_name>_MIGRATION.RAW;
```

 - In VS Code, go to the last, fifth, cell and update the snowflake connection credentials with your account details

```
snowflake_conn = snowflake.connector.connect(
    user='snowflake_user',
    password='snowflake_password',
    account='snowflake_account',
    warehouse='snowflake_warehouse',
    database='<your_name>_MIGRATION', #Put your db name here
    schema='RAW')
```

 - Run the fifth cell

 - In Snowflake, check that your database was added the new table with the data.


## Other materials

 - See more detailed instructions with screenshots in this article - https://python.plainenglish.io/bridging-databases-with-python-from-database-tables-to-pandas-and-back-again-1ae5ad4e2e1f
