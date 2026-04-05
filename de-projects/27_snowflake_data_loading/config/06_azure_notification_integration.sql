-- ============================================================
-- 1. REGISTER EVENT GRID RESOURCE PROVIDER (Azure Portal)
-- ============================================================
---> portal.azure.com
---> Search "Subscriptions" -> click your subscription
---> Left menu: Settings -> Resource providers
---> Filter by "EventGrid"
---> If Microsoft.EventGrid status = "NotRegistered"
--->   select it -> click "Register" at the top
--->   wait ~1-2 min -> Refresh -> confirm status = "Registered"
---> If Microsoft.EventGrid status = "Registered" -> skip this step

-- ============================================================
-- 2. CREATE STORAGE QUEUE (Azure Portal)
-- ============================================================
---> portal.azure.com
---> Search "Storage accounts" -> click adlsanalyticssnowlake
---> Left menu: Data storage -> Queues
---> Click "+ Queue"
--->   Name: snowpipe-queue
--->   Click OK
---> Click the queue -> copy the URL:
--->   https://adlsanalyticssnowlake.queue.core.windows.net/snowpipe-queue

-- ============================================================
-- 3. CREATE EVENT GRID SUBSCRIPTION (Azure Portal)
-- ============================================================
---> Stay in storage account adlsanalyticssnowlake
---> Left menu: Events
---> Click "+ Event Subscription"
--->   BASICS TAB:
--->     Name:              snowpipe-sub
--->     Event Schema:      Event Grid Schema  !! NOT CloudEvents
--->     System Topic Name: snowpipe-storage-topic  (only if not exists)
--->     Filter Event Types: uncheck all -> check ONLY "Blob Created"
--->     Endpoint Type:     Storage Queue
--->     Endpoint:          click "Select an endpoint"
--->       Subscription:    <your subscription>
--->       Storage Account: adlsanalyticssnowlake
--->       Queue:           snowpipe-queue
--->       Click "Confirm Selection"
--->   FILTERS TAB:
--->     Advanced Filters -> "Add new filter":
--->       Key:      data.api
--->       Operator: String is in
--->       Values:   CopyBlob
--->                 PutBlob
--->                 PutBlockList
--->                 FlushWithClose
--->                 SftpCommit
---> Click "Create"


-- ============================================================
-- 4. SET CONTEXT
-- ============================================================


---> set Role Context
USE ROLE ACCOUNTADMIN;

---> set Warehouse Context
USE WAREHOUSE COMPUTE_DEV;

---> set the Database
USE DATABASE analytics_dev;

--USE SCHEMA my_schema;

-- ============================================================
-- 5. CREATE NOTIFICATION INTEGRATION
-- ============================================================
CREATE NOTIFICATION INTEGRATION sv_azure_notification_integration
  ENABLED = true
  TYPE = QUEUE
  NOTIFICATION_PROVIDER = AZURE_STORAGE_QUEUE
  AZURE_STORAGE_QUEUE_PRIMARY_URI = 'https://adlsanalyticssnowlake.queue.core.windows.net/snowpipe-queue'
  AZURE_TENANT_ID = '12b141e0-ebb1-4e7c-934f-afa1f63e2419';


-- ============================================================
-- 6. RETRIEVE CONSENT URL AND APP NAME
--    - Copy AZURE_CONSENT_URL and open it in browser -> Accept
--    - Copy AZURE_MULTI_TENANT_APP_NAME (use string before underscore)
--      to assign Storage Queue Data Contributor role in Azure Portal
-- ============================================================
  DESC NOTIFICATION INTEGRATION sv_azure_notification_integration;

  --    !! Might need to Wait up to 1 hour after Step 6 consent for app to appear

-- ============================================================
-- 7. GRANT SNOWFLAKE ACCESS TO QUEUE (Azure Portal)

-- ============================================================
---> portal.azure.com
---> Search "Storage accounts" -> click adlsanalyticssnowlake
---> Left menu: Data storage -> Queues -> snowpipe-queue
---> Left menu of queue: Access Control (IAM)
---> Click "+ Add" -> "Add role assignment"
--->   Role:             Storage Queue Data Contributor -> Next
--->   Assign access to: User, group, or service principal
--->   Click "+ Select members"
--->     Search: <string before underscore from AZURE_MULTI_TENANT_APP_NAME>
--->     Select the Snowflake app -> click Select
---> Click "Review + assign" -> "Review + assign"
---> VERIFY:
---> Azure Active Directory -> Enterprise Applications
---> confirm Snowflake app is listed
