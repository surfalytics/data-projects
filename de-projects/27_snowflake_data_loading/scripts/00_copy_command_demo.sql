-- ============================================================
-- STEP 1. SET CONTEXT
-- ============================================================

USE ROLE      ACCOUNTADMIN;
USE WAREHOUSE COMPUTE_DEV;
USE DATABASE  analytics_dev;
--USE SCHEMA    BRONZE;


-- ============================================================
-- STEP 2. CREATE TARGET TABLE
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

-- Verify structure
DESCRIBE TABLE ANALYTICS_DEV.BRONZE.USERS_DEMO;


-- Verify stage was created
SHOW STAGES IN SCHEMA ANALYTICS_DEV.RAW;


-- ============================================================
-- STEP 3. UPLOAD FILES TO AZURE BLOB (run in terminal / CLI)
-- ============================================================

-- ============================================================
-- STEP 4. LIST STAGE — CONFIRM SNOWFLAKE CAN SEE THE FILES
-- ============================================================

LIST @analytics_dev.raw.azuredata_stage/users_demo/;

-- Expected output:
-- name                                           | size   | last_modified
-- ../users_demo/users_demo.csv                   | 2180   | 2026-xx-xx ...
-- ../users_demo/users_demo_bad.csv               | 1640   | 2026-xx-xx ...


-- ============================================================
-- STEP 5. VALIDATION MODE — DRY RUN (no rows inserted)
-- ============================================================
-- Run this BEFORE the real load — scans the file for errors
-- without inserting a single row into the table

COPY INTO ANALYTICS_DEV.BRONZE.USERS_DEMO
FROM @analytics_dev.raw.azuredata_stage/users_demo/users_demo.csv
FILE_FORMAT = ANALYTICS_DEV.RAW.FF_USERS_CSV
VALIDATION_MODE = RETURN_ERRORS;

-- Expected output when file is clean:
-- (empty result set — no rows returned = no errors found)

-- Optional: preview the first 5 rows without loading
COPY INTO ANALYTICS_DEV.BRONZE.USERS_DEMO
FROM  @analytics_dev.raw.azuredata_stage/users_demo/users_demo.csv
FILE_FORMAT = ANALYTICS_DEV.RAW.FF_USERS_CSV
VALIDATION_MODE = RETURN_5_ROWS;

-- Expected output: 5 rows showing parsed column values
-- UserId | FirstName | LastName | Email           | ... | IsActive | CreatedAt | UpdatedAt
-- U-1001 | James     | Harri.. | james...@...com  | ... | true     | 2023...   | 2024-03-10 14:22:05
-- U-1002 | Sofia     | Mendes | sofia...@...com   | ... | true     | 2023...   | 2024-03-10 14:22:05
-- ...


-- ============================================================
-- STEP 6. COPY INTO — LOAD THE CLEAN FILE
-- ============================================================

COPY INTO ANALYTICS_DEV.BRONZE.USERS_DEMO
FROM  @analytics_dev.raw.azuredata_stage/users_demo/users_demo.csv
FILE_FORMAT = ANALYTICS_DEV.RAW.FF_USERS_CSV
ON_ERROR    = 'ABORT_STATEMENT';

-- Expected output:
-- file               | status | rows_parsed | rows_loaded | error_limit | errors_seen | first_error
-- ..../users_demo... | LOADED | 20          | 20          | 1           | 0           | NULL


-- Verify rows are in the table
SELECT COUNT(*)    AS total_rows    FROM ANALYTICS_DEV.BRONZE.USERS_DEMO;
-- Expected: 20

SELECT *           FROM ANALYTICS_DEV.BRONZE.USERS_DEMO LIMIT 5;
-- Expected: 5 rows with all columns populated


-- ============================================================
-- STEP 7. RUN COPY AGAIN — DEMONSTRATE DEDUPLICATION
-- ============================================================
-- Snowflake tracks every loaded file for 64 days.
-- Running the exact same COPY again will SKIP the file.

COPY INTO ANALYTICS_DEV.BRONZE.USERS_DEMO
FROM  @analytics_dev.raw.azuredata_stage/users_demo/users_demo.csv
FILE_FORMAT = ANALYTICS_DEV.RAW.FF_USERS_CSV
ON_ERROR    = 'ABORT_STATEMENT';

-- Expected output:
-- file                           | status       | rows_parsed | rows_loaded | errors_seen
-- demo_users_stage/users_demo... | LOAD_SKIPPED | 0           | 0           | 0

-- Confirm row count is still 20 — NOT 40
SELECT COUNT(*) AS total_rows FROM ANALYTICS_DEV.BRONZE.USERS_DEMO;
-- Expected: 20  (dedup prevented duplicate load)


-- ============================================================
-- STEP 8. FORCE RELOAD — OVERRIDE DEDUPLICATION
-- ============================================================
-- WARNING: FORCE = TRUE bypasses the 64-day dedup window.
-- Use only when an intentional reload is required.
-- Rows WILL duplicate if the table has no UNIQUE constraint.

--NOTE!!! duplicated rows can still be loaded to bronze and deduplicated when upsertign to silver

COPY INTO ANALYTICS_DEV.BRONZE.USERS_DEMO
FROM  @analytics_dev.raw.azuredata_stage/users_demo/users_demo.csv
FILE_FORMAT = ANALYTICS_DEV.RAW.FF_USERS_CSV
ON_ERROR    = 'ABORT_STATEMENT'
FORCE       = TRUE;

-- Expected output:
-- file                           | status | rows_parsed | rows_loaded | errors_seen
-- demo_users_stage/users_demo... | LOADED | 20          | 20          | 0

-- Row count is now 40 — duplicates confirmed
SELECT COUNT(*) AS total_rows FROM ANALYTICS_DEV.BRONZE.USERS_DEMO;
-- Expected: 40

-- RESET: clean the table before the next demo step
TRUNCATE TABLE ANALYTICS_DEV.BRONZE.USERS_DEMO;

SELECT COUNT(*) AS total_rows FROM ANALYTICS_DEV.BRONZE.USERS_DEMO;
-- Expected: 0


-- ============================================================
-- STEP 9. LOAD BAD FILE — ON_ERROR = ABORT_STATEMENT (default)
-- ============================================================
-- users_demo_bad.csv contains 3 intentional errors:
--   Row  4 (U-1003): IsActive = 'MAYBE'       → invalid BOOLEAN
--   Row  7 (U-1006): CreatedAt = '15/04/2023' → wrong timestamp format
--   Row 13 (U-1012): CreatedAt = 'NOT-A-DATE' → invalid timestamp

COPY INTO ANALYTICS_DEV.BRONZE.USERS_DEMO
FROM  @analytics_dev.raw.azuredata_stage/users_demo/users_demo_bad.csv
FILE_FORMAT = ANALYTICS_DEV.RAW.FF_USERS_CSV
ON_ERROR    = 'ABORT_STATEMENT'

-- Expected output:
-- file              | status      | rows_parsed | rows_loaded | errors_seen | first_error
-- users_demo_bad... | LOAD_FAILED | 4           | 0           | 1           | Boolean value 'MAYBE' is not recognized, pos 7

-- Row count remains 0 — entire file was rejected
SELECT COUNT(*) AS total_rows FROM ANALYTICS_DEV.BRONZE.USERS_DEMO;
-- Expected: 0


-- ============================================================
-- STEP 10. LOAD BAD FILE — ON_ERROR = CONTINUE
-- ============================================================
-- CONTINUE: skip bad rows, load all good rows

COPY INTO ANALYTICS_DEV.BRONZE.USERS_DEMO
FROM  @analytics_dev.raw.azuredata_stage/users_demo/users_demo_bad.csv
FILE_FORMAT = ANALYTICS_DEV.RAW.FF_USERS_CSV
ON_ERROR    = 'CONTINUE'
FORCE       = TRUE;

-- Expected output:
-- file                               | status           | rows_parsed | rows_loaded | errors_seen | first_error
-- demo_users_stage/users_demo_bad... | PARTIALLY_LOADED | 15          | 12          | 3           | Boolean value 'MAYBE' is not recognized...

-- 12 good rows made it in, 3 bad rows were skipped
SELECT COUNT(*) AS total_rows FROM ANALYTICS_DEV.BRONZE.USERS_DEMO;
-- Expected: 12


-- ============================================================
-- STEP 11. INSPECT EXACT ERRORS FROM LAST COPY
-- ============================================================
-- VALIDATE() reads the error details from the most recent COPY run

SELECT *
FROM   TABLE(VALIDATE(ANALYTICS_DEV.BRONZE.USERS_DEMO, JOB_ID => '_last'));

-- Expected output (3 rows):
-- error                                                  | file               | line | character | byte_offset | category | code   | column_name | rejected_record
-- Boolean value 'MAYBE' is not recognized               | users_demo_bad.csv | 4    | 7         | ...         | OTHER    | 100069 | ISACTIVE    | U-1003,Liam,...,MAYBE,...
-- Timestamp '15/04/2023 13:10:07' is not recognized     | users_demo_bad.csv | 7    | 8         | ...         | OTHER    | 100035 | CREATEDAT   | U-1006,Ethan,...,15/04/...
-- Timestamp 'NOT-A-DATE' is not recognized              | users_demo_bad.csv | 13   | 8         | ...         | OTHER    | 100035 | CREATEDAT   | U-1012,Noah,...,NOT-A-DATE,...


-- ============================================================
-- STEP 12. COPY_HISTORY — AUDIT TRAIL
-- ============================================================


  
-- Option A: INFORMATION_SCHEMA (near real-time, 14-day retention)


USE DATABASE analytics_dev;
USE SCHEMA BRONZE;

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
        START_TIME => DATEADD(HOURS, -100, CURRENT_TIMESTAMP())
    )
)
ORDER BY LAST_LOAD_TIME DESC;


-- Expected output (most recent first):
-- file_name            | last_load_time       | row_count | row_parsed | error_count | status           | first_error_message
-- users_demo_bad.csv   | 2024-xx-xx 09:38:.. | 12        | 15         | 3           | PARTIALLY_LOADED | Boolean value 'MAYBE'...
-- users_demo_bad.csv   | 2024-xx-xx 09:35:.. | 0         | 4          | 1           | LOAD_FAILED      | Boolean value 'MAYBE'...
-- users_demo.csv       | 2024-xx-xx 09:28:.. | 20        | 20         | 0           | LOADED           | NULL
-- users_demo.csv       | 2024-xx-xx 09:26:.. | 20        | 20         | 0           | LOADED           | NULL  <- FORCE run
-- users_demo.csv       | 2024-xx-xx 09:24:.. | 0         | 0          | 0           | LOAD_SKIPPED     | NULL
-- users_demo.csv       | 2024-xx-xx 09:22:.. | 20        | 20         | 0           | LOADED           | NULL  <- first load

-- Option B:
USE DATABASE analytics_dev;

SELECT *
  FROM information_schema.load_history
  WHERE table_name='USERS_DEMO'

-- Option C: ACCOUNT_USAGE (365-day retention, ~45 min lag)

SELECT
    FILE_NAME,
    LAST_LOAD_TIME,
    ROW_COUNT,
    ERROR_COUNT,
    STATUS,
    FIRST_ERROR_MESSAGE
FROM  SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY
WHERE TABLE_NAME   = 'USERS_DEMO'
AND   LAST_LOAD_TIME >= DATEADD(DAY, -3, CURRENT_TIMESTAMP())
ORDER BY LAST_LOAD_TIME DESC;

--only specific to bulk load
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.LOAD_HISTORY
WHERE TABLE_NAME = 'USERS_DEMO'
ORDER BY LAST_LOAD_TIME DESC;





-- ============================================================
-- STEP 15. CLEANUP
-- ============================================================

TRUNCATE TABLE ANALYTICS_DEV.BRONZE.USERS_DEMO;

-- DROP TABLE ANALYTICS_DEV.BRONZE.USERS_DEMO; 

