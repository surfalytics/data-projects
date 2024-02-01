# Getting Started with Soda for Data Warehouse 

## About Soda
Soda (https://www.soda.io/) is a tool used for data quality checking and monitoring. To automate the search for bad-quality data.

Its strengths lie in the automation, scalability, and integration of data quality checks into broader data workflows. It is particularly effective in larger or more dynamic data environments where ongoing monitoring and alerting are crucial.


## History
Soda appeared in 2018. The company behind Soda, also named Soda, was founded in Brussels, Belgium.

Company mission: help data teams catch, prevent, and resolve data issues before they wreak havoc downstream.

The tool was designed to provide users with the ability to write checks and validations for their data, set up alerts, and generate reports on data quality. 

Companies using SODA: HelloFresh, Group 1001, Lululemon, Panasonic, Zefr, and Zendesk


## Soda Distribution
* **Soda Core**: is a free, open-source Python library and CLI tool with documentation.
    * Available for free
    * Compatible with basic SodaCL checks and configurations
    * Supports connections to 18+ data sources
        * Links:
            * Github - https://github.com/sodadata/soda-core 
            * Docs - https://github.com/sodadata/soda-core/blob/main/docs/overview-main.md 
* **Soda Cloud**: a more comprehensive, cloud-based solution that provides a UI for monitoring data quality, setting up alerts, and visualizing issues.
* **Soda Library**, an extension of Soda Core, enables users to connect to Soda Cloud and is compatible with complex SodaCL checks, and offers other features and functionality not available with the open-source tool.

## Key Concepts

**SodaCL**  - Soda Checks Language is a YAML-based language used to write checks for data quality. 

**Soda Check** is a test that Soda performs when it scans a dataset in your data source.
(doc: https://docs.soda.io/soda-cl/soda-cl-overview.html)

**Soda Scan** executes the checks you write and returns a result for each check:
* *pass*: the values in the dataset match or fall within the thresholds you specified
* *fail*: the values in the dataset do not match or fall within the thresholds you specified
* *error*: the syntax of the check is invalid
* *warn*: something you can explicitly configure for individual checks.

**Metric** is a property of the data in your dataset. They can be *built-in* or *custom*.

SodaCL includes over 25 built-in metrics that you can use to write checks, but you also have the option of writing your own SQL queries or expressions using SodaCL.

(doc) SodaCL metrics and checks - https://docs.soda.io/soda-cl/metrics-and-checks.html 


A *threshold* is the value for a metric that Soda checks against during a scan. Usually, you use both a metric and a threshold to define a SodaCL check in a checks YAML file, like the following example that checks that the dim_customer dataset is not empty.

TO DO - Insert image with metric here


## Project

We will use Soda Core (both CLI and Python package) to check data quality of Superstore dataset in Snowflake.


### Scenario 1: Soda Core CLI + Snowflake

Use Soda Core CLI on local machine to check the data in Snowflake.


#### Prerequisites
* *Python* installed
* *pip* installed
* *venv* installed
* *Snowflake* account


#### Step 1 - Install Soda Core

> Docs - https://github.com/sodadata/soda-core/blob/main/docs/installation.md 

Create a virtual environment

``python -m venv soda_venv``

Activate the virtual environment

``.\soda_venv\Scripts\activate``

Upgrade pip inside your new virtual environment

``python.exe -m pip install --upgrade pip``

Install the soda-core-snowflake package

``pip install soda-core-snowflake``


#### Step 2 - Prepare a "configuration.yml" file

In the project directory, create the `configuration.yml` file. It will store connection details for Snowflake.

> Use this instruction - https://docs.soda.io/soda/connect-snowflake.html -  as a reference
to copy+paste the connection syntax into your file, then adjust the values to correspond with your data source’s details.

Create and use system variables for *username*, *password*, *account* attributes for security.

```
data_source snowflake:
  type: snowflake
  username:  ${SNOWFLAKE_USER}
  password:  ${SNOWFLAKE_PASSWORD}
  account:   ${SNOWFLAKE_ACCOUNT}
  database:  SUPERSTORE
  schema:    RAW
  warehouse: WH_SUPERSTORE
```

Run the following command in prompt to test the configured connection to Snowflake:

```
soda test-connection -d snowflake -c ./soda/configuration.yml -V
```

In case of successful configuration, you should see the *Connection 'snowflake' is valid* message in output.


#### Step 3 - Write checks in a checks.yml file

Let’s create checks YAML file for our superstore dataset.
Since we are going to test the *Orders* table in Snowflake, I created a separate folder called *checks* and the *orders.yml* in it.

> Your checks define a passing state, what you expect to see in your dataset. Do not define a failed state

> Useful links:
> * SodaCL tutorial - https://docs.soda.io/soda/quick-start-sodacl.html
> * SodaCL metrics and checks - https://docs.soda.io/soda-cl/metrics-and-checks.html 

`orders.yml`

```
# Checks for ORDERS table in Snowflake

checks for ORDERS:
# Built-in metrics:
  - row_count > 10000
  - missing_count(row_id) = 0
  - duplicate_count(row_id) = 0
  - missing_count(order_id) = 0
  - missing_count(order_date) = 0

# Custom metric
  - count_order_date_after_ship_date = 0:
      count_order_date_after_ship_date query: |
        SELECT COUNT(*) 
        FROM ORDERS 
        WHERE order_date > ship_date

# Schema validation
  - schema:
      fail:
        when required column missing:
          - ORDER_ID
          - ROW_ID
        when wrong column type:
          ORDER_ID: TEXT
```

`returned_orders.yml`

```
checks for RETURNED_ORDERS:
# Built-in metrics:
  - row_count > 0

# Referential integrity
  - values in (order_id) must exist in orders (order_id)
```


#### Step 4 - Run a scan

To run a scan of the data in your data source, execute the following command:

```
soda scan -d snowflake  -c ./soda/configuration.yml ./soda/checks/
```

The output:
```
The output:
[22:51:18] Soda Core 3.1.4
[22:51:19] Scan summary:
[22:51:19] 5/5 checks PASSED:
[22:51:19]     ORDERS in snowflake
[22:51:19]       row_count > 0 [PASSED]
[22:51:19]       missing_count(row_id) = 0 [PASSED]
[22:51:19]       duplicate_count(row_id) = 0 [PASSED]
[22:51:19]       missing_count(order_id) = 0 [PASSED]
[22:51:19]       missing_count(order_date) = 0 [PASSED]
[22:51:19] All is good. No failures. No warnings. No errors.

```

### Scenario 2: Soda Core Python library + Snowflake

Use Soda Core Python library on local machine to check the data in Snowflake.

Steps 1, 2, 3 in this scenario are identical to the previous one. So, refer to the prevous section to complete them unless you did already. 

The only difference will be in step 4, we will be running a scan using Soda Core Python library instead of Soda Core CLI.

We will be using the following `soda_scan.py` script to run a scan programmatically

```
from soda.scan import Scan

scan = Scan()
scan.set_data_source_name("snowflake")

# Add configuration YAML files
scan.add_configuration_yaml_file(file_path="./soda/configuration.yml")

# Add variables
scan.add_variables({"date": "2024-01-28"})

# Add check YAML files 
scan.add_sodacl_yaml_file("./soda/checks/orders.yml")
scan.add_sodacl_yaml_file("./soda/checks/returned_orders.yml")

# Execute the scan
#scan.execute()
exit_code = scan.execute()
print(exit_code)

# Set logs to verbose mode, equivalent to CLI -V option
scan.set_verbose(True)

# Print results of scan
print(scan.get_logs_text())

# Set scan definition name, equivalent to CLI -s option;
#scan.set_scan_definition_name("YOUR_SCHEDULE_NAME")

# Inspect the scan result
#print(scan.get_scan_results()) #returns result as json

# Inspect the scan logs
#scan.get_logs_text() # returns result as text log as you see in CLI

# Typical log inspection # Important feature - used to build automated pipelines
#print(scan.assert_no_error_logs())
#print(scan.assert_no_checks_fail())

# Advanced methods to inspect scan execution logs
#print(scan.has_error_logs())
#print(scan.get_error_logs_text())

# Advanced methods to review check results details
#print(scan.get_checks_fail())
#print(scan.has_check_fails())
#print(scan.get_checks_fail_text())
#print(scan.assert_no_checks_warn_or_fail())
#print(scan.get_checks_warn_or_fail())
#scan.has_checks_warn_or_fail()
#scan.get_checks_warn_or_fail_text()
#print(scan.get_all_checks_text())
```

Run the following command to execute a scan using the python script:

`python .\python\soda_pandas_scan.py`
