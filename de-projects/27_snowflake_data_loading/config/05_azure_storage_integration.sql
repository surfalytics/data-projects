/*--
In this Worksheet we will walk through templated SQL for the end to end process required
to load data from Microsoft Azure into a table.

Snowflake Documentation on bulk loading from Microsoft Azure - https://docs.snowflake.com/en/user-guide/data-load-azure
--*/


-------------------------------------------------------------------------------------------
    -- Step 1: To start, let's set the Role and Warehouse context
        -- USE ROLE: https://docs.snowflake.com/en/sql-reference/sql/use-role
        -- USE WAREHOUSE: https://docs.snowflake.com/en/sql-reference/sql/use-warehouse
-------------------------------------------------------------------------------------------

--> To run a single query, place your cursor in the query editor and select the Run button (⌘-Return).
--> To run the entire worksheet, select 'Run All' from the dropdown next to the Run button (⌘-Shift-Return).

---> set Role Context
USE ROLE ACCOUNTADMIN;

---> set Warehouse Context
USE WAREHOUSE COMPUTE_DEV;

---> set the Database
USE DATABASE analytics_dev;


-------------------------------------------------------------------------------------------
    -- Step 2: Create Storage Integrations
        -- CREATE STORAGE INTEGRATION: https://docs.snowflake.com/en/sql-reference/sql/create-storage-integration
-------------------------------------------------------------------------------------------

    /*--
      A Storage Integration is a Snowflake object that stores a generated identity and access management
      (IAM) entity for your external cloud storage, along with an optional set of allowed or blocked storage locations
      (Amazon S3, Google Cloud Storage, or Microsoft Azure).
    --*/

---> Create the Microsoft Azure Storage Integration
    -- Configuring an Azure Container for Loading Data: https://docs.snowflake.com/en/user-guide/data-load-azure-config

CREATE OR REPLACE STORAGE INTEGRATION sv_azure_data_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'AZURE'
  AZURE_TENANT_ID = '12b141e0-ebb1-4e7c-934f-afa1f63e2419'
  ENABLED = TRUE
  STORAGE_ALLOWED_LOCATIONS = ('azure://adlsanalyticssnowlake.blob.core.windows.net/raw/');

  

    /*--
      Execute the command below to retrieve the AZURE_CONSENT_URL and AZURE_MULTI_TENANT_APP_NAME for the client application created
      automatically for your Snowflake account. You’ll use these values to configure permissions for Snowflake in your Azure Management Console:
          https://docs.snowflake.com/en/user-guide/data-load-azure-config#step-2-grant-snowflake-access-to-the-storage-locations
    --*/

---> Describe our Integration
    -- DESCRIBE INTEGRATIONS: https://docs.snowflake.com/en/sql-reference/sql/desc-integration

DESCRIBE INTEGRATION sv_azure_data_integration;


---> View our Storage Integrations
    -- SHOW INTEGRATIONS: https://docs.snowflake.com/en/sql-reference/sql/show-integrations

SHOW STORAGE INTEGRATIONS;



-------------------------------------------------------------------------------------------
    -- Step 6: Create Stage Objects
-------------------------------------------------------------------------------------------

    /*--
      A stage specifies where data files are stored (i.e. "staged") so that the data in the files
      can be loaded into a table.
    --*/

---> Create the Microsoft Azure Stage
    -- Creating an Azure Stage: https://docs.snowflake.com/en/user-guide/data-load-azure-create-stage

CREATE OR REPLACE STAGE analytics_dev.raw.azuredata_stage
  STORAGE_INTEGRATION = sv_azure_data_integration
  URL = 'azure://adlsanalyticssnowlake.blob.core.windows.net/raw/'
  ;


---> View our Stages
    -- SHOW STAGES: https://docs.snowflake.com/en/sql-reference/sql/show-stages

SHOW STAGES;