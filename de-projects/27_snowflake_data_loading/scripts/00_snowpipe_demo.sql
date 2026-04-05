-- ============================================================
-- SNOWPIPE DEMO — ANALYTICS_DEV.BRONZE.USERS_DEMO
-- Azure Blob Storage → Snowpipe (auto-ingest via Event Grid)
-- Notification Integration: sv_azure_notification_integration
-- Files needed: users_demo.csv  |  users_demo_bad.csv
-- ============================================================


-- ============================================================
-- STEP 1. SET CONTEXT
-- ============================================================

USE ROLE      ACCOUNTADMIN;
USE WAREHOUSE COMPUTE_DEV;
USE DATABASE  analytics_dev;
-- USE SCHEMA BRONZE;


-- ============================================================
-- STEP 2. CONFIRM NOTIFICATION INTEGRATION IS READY
-- ============================================================

-- Verify integration exists and is enabled
SHOW INTEGRATIONS LIKE 'SV_AZURE_NOTIFICATION_INTEGRATION' ;

-- Expected output:
-- name                               | type              | enabled | comment
-- sv_azure_notification_integration  | QUEUE - AZURE_... | true    | ...

-- Inspect details — confirm queue URL and tenant
DESC INTEGRATION SV_AZURE_NOTIFICATION_INTEGRATION;

-- Expected key rows:
-- property                         | value
-- AZURE_STORAGE_QUEUE_PRIMARY_URI  | https://adlsanalyticssnowlake.queue.core.windows.net/snowpipe-queue
-- AZURE_TENANT_ID                  | 12b141e0-ebb1-4e7c-934f-afa1f63e2419


-- ============================================================
-- STEP 3. RECREATE TARGET TABLE (clean slate for demo)
-- ============================================================

CREATE OR REPLACE TABLE ANALYTICS_DEV.BRONZE.USERS_DEMO (
    UserId      STRING,
    FirstName   STRING,
    LastName    STRING,
    Email       STRING,
    Phone       STRING,
    Country     STRING,
    IsActive    BOOLEAN,
    CreatedAt   TIMESTAMP_NTZ,
    UpdatedAt   TIMESTAMP_NTZ
);

-- Verify
DESCRIBE TABLE ANALYTICS_DEV.BRONZE.USERS_DEMO;


-- ============================================================
-- STEP 4. CREATE SNOWPIPE
-- ============================================================
-- AUTO_INGEST = TRUE  → pipe listens to the Azure Queue
-- NOTIFICATION_INTEGRATION links it to sv_azure_notification_integration
-- The COPY INTO inside the pipe defines HOW files are loaded

CREATE OR REPLACE PIPE ANALYTICS_DEV.BRONZE.pipe_users_demo
    AUTO_INGEST            = TRUE
    INTEGRATION            = 'SV_AZURE_NOTIFICATION_INTEGRATION' 
    COMMENT                = 'Auto-ingest pipe for USERS_DEMO from Azure Blob'
AS
COPY INTO ANALYTICS_DEV.BRONZE.USERS_DEMO
FROM  @analytics_dev.raw.azuredata_stage/users_demo_snowpipe/
FILE_FORMAT = ANALYTICS_DEV.RAW.FF_USERS_CSV
ON_ERROR    = 'CONTINUE';

-- Verify pipe was created
SHOW PIPES LIKE 'pipe_users_demo' IN SCHEMA ANALYTICS_DEV.BRONZE;

-- Expected output:
-- name             | definition                          | notification_channel       | owner
-- pipe_users_demo  | COPY INTO ANALYTICS_DEV.BRONZE...   | https://adlsanalyt...      | ACCOUNTADMIN

-- !! IMPORTANT: The notificationChannel column shows the Azure Queue URL
-- This must match the queue wired in your Event Grid subscription
-- If it does not match -> update the Event Grid subscription endpoint in Azure Portal


-- ============================================================
-- STEP 5. CONFIRM PIPE STATUS BEFORE UPLOADING
-- ============================================================

SELECT PARSE_JSON(SYSTEM$PIPE_STATUS('ANALYTICS_DEV.BRONZE.pipe_users_demo'));

-- Expected output (pipe is ready and idle):
-- {
--   "executionState"         : "RUNNING",
--   "pendingFileCount"       : 0,
--   "notificationChannelName": "https://adlsanalyticssnowlake.queue.core.windows.net/snowpipe-queue",
--   "lastIngestedEventTime"  : null,
--   "lastIngestedFilePath"   : null
-- }

-- executionState must be RUNNING before uploading files
-- If PAUSED → run:  ALTER PIPE ANALYTICS_DEV.BRONZE.pipe_users_demo RESUME;


-- ============================================================
-- STEP 6. UPLOAD CLEAN FILE TO AZURE BLOB (terminal / CLI)
-- ============================================================

---> What happens next (automatically, no action needed):
---> 1. Azure Blob fires a BlobCreated event
---> 2. Event Grid catches it → routes to snowpipe-queue
---> 3. Snowpipe reads the queue message
---> 4. Snowpipe loads the file into USERS_DEMO
---> Typical latency: 30 seconds to 2 minutes


-- ============================================================
-- STEP 7. WATCH THE PIPE PICK UP THE FILE
-- ============================================================
-- Run this immediately after upload — watch pendingFileCount

SELECT PARSE_JSON(SYSTEM$PIPE_STATUS('ANALYTICS_DEV.BRONZE.pipe_users_demo'));

-- Expected output WHILE loading:
-- {
--   "executionState"         : "RUNNING",
--   "pendingFileCount"       : 1,         <- file is queued
--   "lastIngestedEventTime"  : null,
--   "lastIngestedFilePath"   : null
-- }

-- Run again after 1-2 minutes
SELECT PARSE_JSON(SYSTEM$PIPE_STATUS('ANALYTICS_DEV.BRONZE.pipe_users_demo'));

-- Expected output AFTER loading:
-- {
--   "executionState"         : "RUNNING",
--   "pendingFileCount"       : 0,                            <- cleared
--   "lastIngestedEventTime"  : "2026-xx-xxT09:22:10.000Z",  <- timestamp of last event
--   "lastIngestedFilePath"   : "users_demo/users_demo.csv"  <- last file picked up
-- }


-- ============================================================
-- STEP 8. VERIFY ROWS LANDED IN THE TABLE
-- ============================================================

SELECT COUNT(*) AS total_rows FROM ANALYTICS_DEV.BRONZE.USERS_DEMO;
-- Expected: 20


SELECT * FROM ANALYTICS_DEV.BRONZE.USERS_DEMO LIMIT 5;
-- Expected: 5 rows with all columns populated


-- ============================================================
-- STEP 9. UPLOAD BAD FILE — SHOW ERROR HANDLING
-- ============================================================
-- users_demo_bad.csv contains 3 intentional errors:
--   Row  4 (U-1003): IsActive = 'MAYBE'       → invalid BOOLEAN
--   Row  7 (U-1006): CreatedAt = '15/04/2023' → wrong timestamp format
--   Row 13 (U-1012): CreatedAt = 'NOT-A-DATE' → invalid timestamp
-- Pipe is configured ON_ERROR = CONTINUE → good rows load, bad rows skipped


-- Wait 1-2 minutes then check pipe status
SELECT PARSE_JSON(SYSTEM$PIPE_STATUS('ANALYTICS_DEV.BRONZE.pipe_users_demo'));

-- Check row count — 20 + 12 good rows from bad file = 32
SELECT COUNT(*) AS total_rows FROM ANALYTICS_DEV.BRONZE.USERS_DEMO;
-- Expected: 32


-- ============================================================
-- STEP 10. COPY_HISTORY — AUDIT TRAIL FOR SNOWPIPE LOADS
-- ============================================================

-- Option A: INFORMATION_SCHEMA (near real-time, 14-day retention)
-- NOTE: does not have PIPE_NAME column — filter by TABLE_NAME only

USE DATABASE analytics_dev;
USE SCHEMA   BRONZE;

SELECT
    FILE_NAME,
    LAST_LOAD_TIME,
    ROW_COUNT,
    ROW_PARSED,
    ERROR_COUNT,
    STATUS,
    FIRST_ERROR_MESSAGE
FROM TABLE(
    INFORMATION_SCHEMA.COPY_HISTORY(
        TABLE_NAME => 'USERS_DEMO',
        START_TIME => DATEADD(HOURS, -2, CURRENT_TIMESTAMP())
    )
)
ORDER BY LAST_LOAD_TIME DESC;

-- Expected output:
-- file_name            | last_load_time       | row_count | row_parsed | error_count | status           | first_error_message
-- users_demo_bad.csv   | 2026-xx-xx 09:28:.. | 12        | 15         | 3           | PARTIALLY_LOADED | Boolean value 'MAYBE'...
-- users_demo.csv       | 2026-xx-xx 09:22:.. | 20        | 20         | 0           | LOADED           | NULL






-- ============================================================
-- STEP 11. PIPE USAGE HISTORY — COST AND THROUGHPUT
-- ============================================================
-- How many files processed, bytes ingested, credits consumed

SELECT
    PIPE_NAME,
    START_TIME,
    END_TIME,
    CREDITS_USED,
    FILES_INSERTED,
    BYTES_INSERTED
FROM  SNOWFLAKE.ACCOUNT_USAGE.PIPE_USAGE_HISTORY
WHERE PIPE_NAME   = 'PIPE_USERS_DEMO'
AND   START_TIME >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
ORDER BY START_TIME DESC;

-- Expected output:
-- pipe_name                              | start_time    | credits_used | files_inserted | bytes_inserted
-- ANALYTICS_DEV.BRONZE.PIPE_USERS_DEMO  | 2026-xx-xx.. | 0.000842     | 2              | 3820


-- ============================================================
-- STEP 12. PAUSE AND RESUME THE PIPE
-- ============================================================
-- Useful for maintenance windows, schema changes, or cost control
-- Files uploaded while paused queue in the Azure Queue
-- and will load automatically when pipe is resumed

-- Pause
ALTER PIPE ANALYTICS_DEV.BRONZE.pipe_users_demo SUSPEND;

SELECT PARSE_JSON(SYSTEM$PIPE_STATUS('ANALYTICS_DEV.BRONZE.pipe_users_demo'));
-- Expected: "executionState": "PAUSED"

-- Resume — queued files start loading immediately
ALTER PIPE ANALYTICS_DEV.BRONZE.pipe_users_demo RESUME;

SELECT PARSE_JSON(SYSTEM$PIPE_STATUS('ANALYTICS_DEV.BRONZE.pipe_users_demo'));
-- Expected: "executionState": "RUNNING"

-- !! NOTE: Files uploaded while PAUSED remain in the queue
-- and WILL be loaded once the pipe resumes — no files are lost



-- ============================================================
-- CLEANUP
-- ============================================================

TRUNCATE TABLE ANALYTICS_DEV.BRONZE.USERS_DEMO;

ALTER PIPE ANALYTICS_DEV.BRONZE.pipe_users_demo SUSPEND;

-- DROP PIPE  ANALYTICS_DEV.BRONZE.pipe_users_demo;   -- optional full reset
-- DROP TABLE ANALYTICS_DEV.BRONZE.USERS_DEMO;        -- optional

