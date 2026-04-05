 
/*
Query COPY_HISTORY after every load
The first line of defense. After any COPY run, check for PARTIALLY_LOADED or LOAD_FAILED status and non-zero ERROR_COUNT
*/
SELECT FILE_NAME, STATUS, ROW_COUNT, ERROR_COUNT, FIRST_ERROR_MESSAGE
FROM   TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
         TABLE_NAME => 'USERS_DEMO',
         START_TIME => DATEADD(MINUTE, -30, CURRENT_TIMESTAMP())
       ))
WHERE  STATUS != 'LOADED'
ORDER  BY LAST_LOAD_TIME DESC;
/*
VALIDATE() for rejected rows
Once you know a load had errors, drill into the exact rows that failed — which line, which column, what value:
*/
SELECT * FROM TABLE(VALIDATE(ANALYTICS_DEV.BRONZE.USERS_DEMO, JOB_ID => '_last'));
/*
Monitor — Automate the checks
Snowflake Tasks — scheduled SQL, no external scheduler needed:
*/
CREATE OR REPLACE TASK monitor_users_demo_load
    WAREHOUSE = COMPUTE_DEV
    SCHEDULE  = 'USING CRON 0 * * * * UTC'   -- every hour
AS
INSERT INTO ANALYTICS_DEV.BRONZE.load_alerts (file_name, status, error_count, detected_at)
SELECT
    FILE_NAME,
    STATUS,
    ERROR_COUNT,
    CURRENT_TIMESTAMP()
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
    TABLE_NAME => 'USERS_DEMO',
    START_TIME => DATEADD(HOUR, -1, CURRENT_TIMESTAMP())
))
WHERE STATUS != 'LOADED'
  AND STATUS != 'LOAD_SKIPPED';
ALTER TASK monitor_users_demo_load RESUME;
/*
Snowflake Alerts — built-in alerting, triggers when a condition is true:
*/
CREATE OR REPLACE ALERT alert_users_demo_errors
    WAREHOUSE = COMPUTE_DEV
    SCHEDULE  = '60 MINUTE'
    IF (EXISTS (
        SELECT 1
        FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
            TABLE_NAME => 'USERS_DEMO',
            START_TIME => DATEADD(HOUR, -1, CURRENT_TIMESTAMP())
        ))
        WHERE ERROR_COUNT > 0
    ))
    THEN
        CALL SYSTEM$SEND_EMAIL(
            'load_alerts',
            'data-team@yourcompany.com',
            'USERS_DEMO load errors detected',
            'One or more files loaded with errors. Check COPY_HISTORY.'
        );
ALTER ALERT alert_users_demo_errors RESUME;
/*
Fix Rows
*/
/*QUARNTINE PATTERN*/
-- 1. Load what you can
/*
COPY INTO ANALYTICS_DEV.BRONZE.USERS_DEMO
FROM  @analytics_dev.raw.azuredata_stage/users_demo/users_demo_bad.csv
FILE_FORMAT = ANALYTICS_DEV.RAW.FF_USERS_CSV
ON_ERROR    = 'CONTINUE'
FORCE       = TRUE;
*/
-- 2. Capture rejected rows into a quarantine table
CREATE TABLE IF NOT EXISTS ANALYTICS_DEV.BRONZE.USERS_DEMO_REJECTED AS
SELECT CURRENT_TIMESTAMP() AS detected_at, *
FROM   TABLE(VALIDATE(ANALYTICS_DEV.BRONZE.USERS_DEMO, JOB_ID => '_last'));
-- 3. Someone fixes the source data, then re-inserts the corrected rows manually