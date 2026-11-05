-- =============================================================================
-- Solutions for Exercise 2: Windowed Aggregations
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Exercise 2.1: Tumbling Window -- Orders Per Minute
--
-- TUMBLING windows are fixed-size and non-overlapping.
-- SIZE 1 MINUTE means each window covers exactly 60 seconds.
-- Each order belongs to exactly ONE window.
--
-- WINDOWSTART and WINDOWEND are virtual columns containing the window
-- boundaries as epoch milliseconds.
--
-- When a new minute starts, ksqlDB emits a new row for that window.
-- Within a window, each new order triggers an updated row (same key).
-- ---------------------------------------------------------------------------
SELECT
    customer_id,
    COUNT(*)                    AS order_count,
    SUM(price * quantity)       AS total_revenue,
    WINDOWSTART                 AS window_start,
    WINDOWEND                   AS window_end
FROM orders_stream
WINDOW TUMBLING (SIZE 1 MINUTE)
GROUP BY customer_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- Exercise 2.2: Hopping Window -- Smoothed Revenue
--
-- HOPPING windows overlap. SIZE 10 MINUTES, ADVANCE BY 2 MINUTES means:
--   - Each window covers 10 minutes of data
--   - A new window starts every 2 minutes
--   - A single order appears in size/advance = 10/2 = 5 windows
--
-- Hopping windows are preferred for dashboards because they provide smoother
-- trends. Tumbling windows can show spiky data because a single large order
-- dominates one window then disappears.
-- ---------------------------------------------------------------------------
SELECT
    product_id,
    AVG(price * quantity)       AS avg_order_value,
    COUNT(*)                    AS order_count
FROM orders_stream
WINDOW HOPPING (SIZE 10 MINUTES, ADVANCE BY 2 MINUTES)
GROUP BY product_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- Exercise 2.3: Session Window -- User Engagement
--
-- SESSION windows group events by activity bursts separated by an
-- inactivity gap (here 3 minutes).
--
-- A session closes when no new event arrives for 3+ minutes.
-- If a user views 5 pages quickly, waits 4 min, then views 2 more:
--   -> 2 sessions (the 4-min gap exceeds the 3-min threshold)
--
-- Late-arriving events may merge or extend existing sessions if they
-- fall within the gap of an existing session.
-- ---------------------------------------------------------------------------

-- Push query version:
SELECT
    user_id,
    COUNT(*)                    AS pages_viewed,
    WINDOWSTART                 AS session_start,
    WINDOWEND                   AS session_end
FROM clickstream_stream
WINDOW SESSION (3 MINUTES)
GROUP BY user_id
EMIT CHANGES;

-- Bonus: persistent materialized view version:
CREATE TABLE IF NOT EXISTS user_sessions_3min AS
SELECT
    user_id,
    COUNT(*)                    AS pages_viewed,
    WINDOWSTART                 AS session_start,
    WINDOWEND                   AS session_end
FROM clickstream_stream
WINDOW SESSION (3 MINUTES)
GROUP BY user_id
EMIT CHANGES;

-- Pull query against the materialized view:
-- SELECT * FROM user_sessions_3min WHERE user_id = 'C0001';
