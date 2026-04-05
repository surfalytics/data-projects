-- ============================================================
-- 1. SET CONTEXT
-- ============================================================
---> set Role Context
USE ROLE ACCOUNTADMIN;
---> set Warehouse Context
USE WAREHOUSE COMPUTE_DEV;
---> set the Database
USE DATABASE ANALYTICS_DEV;
USE SCHEMA SILVER;

-- ============================================================
-- 2. CREATE PIPE
-- ============================================================
CREATE OR REPLACE PIPE ANALYTICS_DEV.BRONZE.SV_USERS_PIPE
  AUTO_INGEST = true
  INTEGRATION = 'SV_AZURE_NOTIFICATION_INTEGRATION'  -- must be UPPERCASE
  AS
    COPY INTO ANALYTICS_DEV.BRONZE.USERS (
        UserId,
        FirstName,
        LastName,
        Email,
        Phone,
        Country,
        IsActive,
        CreatedAt,
        UpdatedAt,
        SourceFilePath,
        SourceFileRowNumber,
        SourceFileLastModified,
        LoadTs,
        LoadId
    )
    FROM (
        SELECT
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            $7,
            $8,
            $9,
            METADATA$FILENAME,
            METADATA$FILE_ROW_NUMBER,
            METADATA$FILE_LAST_MODIFIED,
            METADATA$START_SCAN_TIME,
            'LOAD_' || TO_VARCHAR(CURRENT_TIMESTAMP(), 'YYYYMMDD_HH24MISSFF3')
        FROM @ANALYTICS_DEV.RAW.AZUREDATA_STAGE/users/
            (FILE_FORMAT => 'ANALYTICS_DEV.RAW.FF_USERS_CSV')
    )
    ON_ERROR = 'CONTINUE';

-- ============================================================
-- 3. VERIFY PIPE CREATED CORRECTLY
-- ============================================================
SHOW PIPES;
DESC PIPE ANALYTICS_DEV.BRONZE.SV_USERS_PIPE;

-- ============================================================
-- 4. BACKFILL ANY FILES ALREADY IN STAGE
--     Only needed if files existed in stage before pipe was created
-- ============================================================
ALTER PIPE ANALYTICS_DEV.RAW.SV_USERS_PIPE REFRESH;

-- ============================================================
-- 5. CHECK PIPE STATUS
--     Expected: executionState = "Running"
--     If "Initializing" -> wait a few minutes and re-run
--     If "Failing"      -> recheck Azure consent and IAM role
-- ============================================================
SELECT SYSTEM$PIPE_STATUS('ANALYTICS_DEV.RAW.SV_USERS_PIPE');