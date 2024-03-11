## Project goal

Overview observability tool “Elementary Data” for dbt project.

## Use cases

1. Monitoring dbt project - models and tests running
2. Alerting in case of issues

## Prerequisites

Ensure you have the following software installed on your laptop:

- Git
- Python
- Visual Studio Code

## Useful links

Youtube [video](https://youtu.be/jfg9wBJBtKk?si=4UVZ93u-MdwnJvaF) about observability

The step-by-step guide from the Elementary Data website is [here](https://docs.elementary-data.com/oss/quickstart/quickstart-cli-package)

## Project steps

1. Clone the repo and access it using VS Code
2. Create a trial account or log in to the Snowflake 
3. Create Database
4. Load the data 
5. Change database
6. Edit `profiles.yml` file in your dbt project folder
7. Create Python Virtual environment
8. Add Environment Variables ****to the project
9. dbt package installation and check connection
10. Elementary package installation
11. Import the package and build Elementary models
12. Configuring `profiles.yml` file in your dbt project folder
13. Install Elementary CLI
14. Generate observability report

### Step 1. Clone this repo to your local machine

https://github.com/nordquant/complete-dbt-bootcamp-zero-to-hero

You can use the following command in VS Code terminal:

```bash
git clone https://github.com/nordquant/complete-dbt-bootcamp-zero-to-hero.git
```

### Step 2. Create a trial account or log in to the Snowflake

Go to the Snowflake website, start free trial and choose:
* Standard edition
* AWS
* US East (Ohio)

### Step 3. Create Database

Replace all `<your_name>` on your actual name!

```sql
-- Use an admin role
USE ROLE ACCOUNTADMIN;

-- Create the `transform` role
CREATE ROLE IF NOT EXISTS transform;
GRANT ROLE TRANSFORM TO ROLE ACCOUNTADMIN;

-- Create the default warehouse if necessary
CREATE WAREHOUSE IF NOT EXISTS <your_name>_COMPUTE_WH;
GRANT OPERATE ON WAREHOUSE <your_name>_COMPUTE_WH TO ROLE TRANSFORM;

-- Create the `dbt` user and assign to role
CREATE USER IF NOT EXISTS dbt
  PASSWORD='<your_password>'
  LOGIN_NAME='<your_login>'
  MUST_CHANGE_PASSWORD=FALSE
  DEFAULT_WAREHOUSE='<your_name>_COMPUTE_WH'
  DEFAULT_ROLE='transform'
  DEFAULT_NAMESPACE='<your_name>_AIRBNB.RAW'
  COMMENT='DBT user used for data transformation';
GRANT ROLE transform to USER dbt;

-- Create our database and schemas
CREATE DATABASE IF NOT EXISTS <your_name>_AIRBNB;
CREATE SCHEMA IF NOT EXISTS <your_name>_AIRBNB.RAW;

-- Set up permissions to role `transform`
GRANT ALL ON WAREHOUSE <your_name>_COMPUTE_WH TO ROLE transform; 
GRANT ALL ON DATABASE <your_name>_AIRBNB to ROLE transform;
GRANT ALL ON ALL SCHEMAS IN DATABASE <your_name>_AIRBNB to ROLE transform;
GRANT ALL ON FUTURE SCHEMAS IN DATABASE <your_name>_AIRBNB to ROLE transform;
GRANT ALL ON ALL TABLES IN SCHEMA <your_name>_AIRBNB.RAW to ROLE transform;
GRANT ALL ON FUTURE TABLES IN SCHEMA <your_name>_AIRBNB.RAW to ROLE transform;
```

### Step 4. Load the data

Replace all `<your_name>` on your actual name!

```sql
-- Set up the defaults
USE WAREHOUSE <your_name>_COMPUTE_WH;
USE DATABASE <your_name>_airbnb;
USE SCHEMA RAW;

-- Create our three tables and import the data from S3
CREATE OR REPLACE TABLE raw_listings
                    (id integer,
                     listing_url string,
                     name string,
                     room_type string,
                     minimum_nights integer,
                     host_id integer,
                     price string,
                     created_at datetime,
                     updated_at datetime);
                    
COPY INTO raw_listings (id,
                        listing_url,
                        name,
                        room_type,
                        minimum_nights,
                        host_id,
                        price,
                        created_at,
                        updated_at)
                   from 's3://dbtlearn/listings.csv'
                    FILE_FORMAT = (type = 'CSV' skip_header = 1
                    FIELD_OPTIONALLY_ENCLOSED_BY = '"');
                    

CREATE OR REPLACE TABLE raw_reviews
                    (listing_id integer,
                     date datetime,
                     reviewer_name string,
                     comments string,
                     sentiment string);
                    
COPY INTO raw_reviews (listing_id, date, reviewer_name, comments, sentiment)
                   from 's3://dbtlearn/reviews.csv'
                    FILE_FORMAT = (type = 'CSV' skip_header = 1
                    FIELD_OPTIONALLY_ENCLOSED_BY = '"');
                    

CREATE OR REPLACE TABLE raw_hosts
                    (id integer,
                     name string,
                     is_superhost string,
                     created_at datetime,
                     updated_at datetime);
                    
COPY INTO raw_hosts (id, name, is_superhost, created_at, updated_at)
                   from 's3://dbtlearn/hosts.csv'
                    FILE_FORMAT = (type = 'CSV' skip_header = 1
                    FIELD_OPTIONALLY_ENCLOSED_BY = '"');
```

### Step 5. Change database

In VS Code open folder with dbt project. 

Change the name of the database from `airbnb` to `<your_name>_airbnb` in the following:

- `sources.yml` file
- all models in `src` folder
- in `shapshots` folder

### Step 6. Edit `profiles.yml` file in your dbt project folder

Replace all `<your_name>` on your actual name!

```yaml
dbtlearn: 
  outputs: 
    dev: 
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}" 
      database: <your_name>_AIRBNB 
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}" 
      role: transform 
      schema: DEV 
      threads: 1 
      type: snowflake 
      user: "{{ env_var('SNOWFLAKE_USER') }}" 
      warehouse: <your_name>_COMPUTE_WH 
  target: dev
```

### Step 7. Create Python Virtual environment

Open the folder where you want to locate a Virtual environment and create a new one.

*For MacOS:*

```bash
# create virtual environment
python3 -m venv edenv
```

> Where “edenv” is the name of Virtual environment. You can choose another name.
> 

*For Windows:*

```bash
# create virtual environment
python -m venv edenv
```

Activate the environment.

*For MacOS:*

```bash
# activate virtual environment
source edenv/bin/activate
```

*For Windows:*

```bash
# activate virtual environment
edenv\Scripts\activate
```

### Step 8. Add **Environment Variables** to the project

We can set Environment Variables once for the duration of your CLI session

*For MacOS:*

```bash
# set environment variables once
export SNOWFLAKE_ACCOUNT=<your_account>
export SNOWFLAKE_USER=<your_login>
export SNOWFLAKE_PASSWORD=<your_password>
```

*For Windows cmd:*

```bash
# set environment variables once for cmd
set SNOWFLAKE_ACCOUNT=<your_account>
set SNOWFLAKE_USER=<your_login>
set SNOWFLAKE_PASSWORD=<your_password>
```

*For Windows PowerShell:*

```bash
# set environment variables once for PowerShell
$env:SNOWFLAKE_ACCOUNT=<your_account>
$env:SNOWFLAKE_USER=<your_login>
$env:SNOWFLAKE_PASSWORD=<your_password>
```

Or we can automate Environment Variable setup.

*For MacOS:*

- Navigate to your virtual environment's directory. Inside, you'll find a **`bin`** directory that contains scripts that are run when the virtual environment is activated or deactivated.
- Find the **`activate`** script within the **`bin`** directory. This script is executed whenever you activate your virtual environment.
- Edit the **`activate`** script to include the export commands for your environment variables at the end of the file:

```bash
# add these commands at the end of file
export SNOWFLAKE_ACCOUNT=<your_account>
export SNOWFLAKE_USER=<your_login>
export SNOWFLAKE_PASSWORD=<your_password>
```

Then deactivate Virtual environment and activate again. 

```bash
# deactivate virtual environment
deactivate

# activate virtual environment
source edenv/bin/activate
```

*For Windows* use Environment Variables in parameters of your system.

### Step 9. dbt package installation and check connection

Run the following commands in your dbt project folder:

```bash
#install dbt-snowflake package
pip install dbt-snowflake

#check your connection
dbt debug
```

### Step 10. Elementary package installation

Add elementary to your `packages.yml` in the dbt project folder

```yaml
packages:
package: elementary-data/elementary
version: 0.14.1
```

Add to your `dbt_project.yml` file materialization config

```yaml
models:
  elementary:
  ## elementary models will be created in the schema '<your_schema>_elementary'
    +schema: "elementary"
    ## To disable elementary for dev, uncomment this:
    # enabled: "{{ [target.name](http://target.name/) in ['prod','analytics'] }}"
```

### Step 11. Import the package and build Elementary models

Run the following commands in your dbt project folder:

```bash
#install needed dependencies
dbt deps

#load seed data to snowflake
dbt seed

#run dbt models
dbt run
```

If you get an error, it’s ok. We can fix it in `dbt_project.yml` file. In your `models` section change `REPORTER` to `TRANSFORM` and run dbt models again.

```yaml
models:
  dbtlearn:
    +materialized: view
    +post-hook:
      - "GRANT SELECT ON {{ this }} TO ROLE TRANSFORM"
```

Validate the installation by running some tests

```bash
#install needed dependencies
dbt test
```

After you ran your tests, we can check that the results were loaded to **`elementary_test_results`** table.

### Step 12. Configuring `profiles.yml` file in your dbt project folder

In order to connect, Elementary needs a connection profile. Run the following command within the dbt project.

```bash
dbt run-operation elementary.generate_elementary_cli_profile
```

Copy the output, add the profile to your **`profiles.yml`**, edit, and fill in the missing fields.

```yaml
elementary: 
  outputs: 
    dev: 
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      role: transform
      warehouse: TSEBEK_COMPUTE_WH
      database: TSEBEK_AIRBNB
      schema: dev_elementary
      threads: 1
```

### Step 13. Install Elementary CLI

To install the monitor module run:

```bash
pip install elementary-data
pip install 'elementary-data[snowflake]'
```

If you have another database/DWH, you can use one of the following command based on your platform.

```bash
pip install 'elementary-data[bigquery]'
pip install 'elementary-data[redshift]'
pip install 'elementary-data[databricks]'
pip install 'elementary-data[athena]'
## Postgres doesn't require this step
```

Run command in order to ensure the installation was successful:

```bash
edr --help
```

You should receive this:

![alt text][def]

If you're receiving **`command not found: edr`** please check **[troubleshooting guide](https://docs.elementary-data.com/general/troubleshooting)**. 

### Step 14. Generate observability report

Run command
```bash
edr report
```

[def]: Screenshot.png