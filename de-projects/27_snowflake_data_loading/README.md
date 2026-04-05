# Snowflake Data Loading — Azure Blob to Snowflake

End-to-end project for loading CSV data from Azure Blob Storage into Snowflake using both **bulk COPY INTO** and **Snowpipe** (auto-ingest via Azure Event Grid). Follows a medallion architecture (RAW → BRONZE → SILVER) with built-in lineage metadata, error handling, and observability.

## Prerequisites

- Snowflake account with `ACCOUNTADMIN` role
- Azure Storage Account (`adlsanalyticssnowlake`) with a `raw` container
- Azure Event Grid resource provider registered on the subscription (for Snowpipe)
- Azure Storage Queue (`snowpipe-queue`) with an Event Grid subscription filtering on `BlobCreated` events (for Snowpipe)

## Project Structure

```
config/                                    # Infrastructure setup (run once, in order)
  01_create_db_and_schemas.sql             # ANALYTICS_DEV database + RAW/BRONZE/SILVER schemas
  02_create_warehouse.sql                  # COMPUTE_DEV warehouse (XSmall, auto-suspend 60s)
  03_create_file_format.sql                # FF_USERS_CSV — CSV format with header skip
  04_create_tables.sql                     # BRONZE.USERS and SILVER.USERS tables
  05_azure_storage_integration.sql         # Storage integration, stage, and Azure IAM consent
  06_azure_notification_integration.sql    # Notification integration + Azure Queue/Event Grid setup

scripts/                                   # Data loading workflows
  00_copy_command_demo.sql                 # Bulk COPY INTO walkthrough (validation, load, error handling)
  00_snowpipe_demo.sql                     # Snowpipe auto-ingest walkthrough (create pipe, monitor, pause/resume)
  03_raw_to_bronze_pipe.sql                # Production Snowpipe with full lineage metadata columns
  99_bulk_load_data_ingestion_observability.sql  # Monitoring: COPY_HISTORY, VALIDATE(), Tasks, Alerts, quarantine
```

## Setup

Run the config scripts in order using the `ACCOUNTADMIN` role:

| Step | Script                                  | What it does                                                                    |
| ---- | --------------------------------------- | ------------------------------------------------------------------------------- |
| 1    | `01_create_db_and_schemas.sql`          | Creates `ANALYTICS_DEV` database with `RAW`, `BRONZE`, `SILVER` schemas         |
| 2    | `02_create_warehouse.sql`               | Creates `COMPUTE_DEV` warehouse (XSmall, auto-suspend 60s, initially suspended) |
| 3    | `03_create_file_format.sql`             | Creates `FF_USERS_CSV` file format (skip header, handle NULLs)                  |
| 4    | `04_create_tables.sql`                  | Creates `BRONZE.USERS` (with lineage columns) and `SILVER.USERS` tables         |
| 5    | `05_azure_storage_integration.sql`      | Creates Azure storage integration + external stage `azuredata_stage`            |
| 6    | `06_azure_notification_integration.sql` | Creates notification integration for Snowpipe (Azure Queue + Event Grid)        |

Steps 5 and 6 require Azure Portal configuration (IAM consent, Event Grid subscription). Follow the inline comments in each script.

## Data Loading Methods

### Bulk Load — COPY INTO

**Script:** `scripts/00_copy_command_demo.sql`

Demonstrates the full COPY INTO lifecycle:

1. **Validation mode** — dry-run with `RETURN_ERRORS` and `RETURN_5_ROWS` before loading
2. **Standard load** — `ON_ERROR = 'ABORT_STATEMENT'` for clean files
3. **Deduplication** — re-running COPY skips already-loaded files (64-day tracking window)
4. **Force reload** — `FORCE = TRUE` bypasses dedup when intentional reload is needed
5. **Error handling** — `ON_ERROR = 'CONTINUE'` loads good rows, skips bad rows
6. **Error inspection** — `VALIDATE()` to see exact rejected rows and columns
7. **Audit trail** — `COPY_HISTORY` via `INFORMATION_SCHEMA` and `ACCOUNT_USAGE`

### Auto-Ingest — Snowpipe

**Script:** `scripts/00_snowpipe_demo.sql`

Event-driven loading triggered by Azure Blob uploads:

1. File lands in Azure Blob → Event Grid fires `BlobCreated`
2. Event Grid routes to Azure Storage Queue (`snowpipe-queue`)
3. Snowpipe reads the queue and loads the file automatically
4. Typical latency: 30 seconds to 2 minutes

Key operations covered: create pipe, monitor with `SYSTEM$PIPE_STATUS`, pause/resume, cost tracking via `PIPE_USAGE_HISTORY`.

### Production Pipe with Lineage

**Script:** `scripts/03_raw_to_bronze_pipe.sql`

Production-grade Snowpipe that enriches each row with:

- `METADATA$FILENAME` — source file path
- `METADATA$FILE_ROW_NUMBER` — row number within the file
- `METADATA$FILE_LAST_MODIFIED` — file last modified timestamp
- `METADATA$START_SCAN_TIME` — load timestamp
- Generated `LoadId` for batch correlation

## Observability

**Script:** `scripts/99_bulk_load_data_ingestion_observability.sql`

| Technique              | Purpose                                                                                           |
| ---------------------- | ------------------------------------------------------------------------------------------------- |
| `COPY_HISTORY`         | Check status of recent loads (`LOADED`, `PARTIALLY_LOADED`, `LOAD_FAILED`)                        |
| `VALIDATE()`           | Drill into exact rejected rows — line number, column, value                                       |
| Snowflake **Task**     | Hourly cron that inserts failed loads into a `load_alerts` table                                  |
| Snowflake **Alert**    | Triggers email notification when `ERROR_COUNT > 0`                                                |
| **Quarantine pattern** | Load with `ON_ERROR = 'CONTINUE'`, capture rejects into a `_REJECTED` table for manual correction |

## Sample Data

The demo scripts expect two CSV files uploaded to the Azure stage:

- `users_demo.csv` — 20 clean rows
- `users_demo_bad.csv` — 15 rows with 3 intentional errors (invalid boolean, wrong timestamp formats)
