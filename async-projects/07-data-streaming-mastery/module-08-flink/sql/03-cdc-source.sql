-- =============================================================================
-- 03-cdc-source.sql
-- =============================================================================
-- Demonstrates Flink SQL CDC (Change Data Capture) connector for MySQL.
-- Flink CDC reads the MySQL binlog directly, capturing INSERTs, UPDATEs,
-- and DELETEs in real time -- no Kafka Connect or separate Debezium needed.
--
-- Prerequisites:
--   - MySQL container is running with binlog enabled (debezium/example-mysql).
--   - The flink-sql-connector-mysql-cdc JAR is in Flink's classpath.
--   - The 'inventory' database has been seeded with tables.
--
-- How It Works:
--   1. Flink CDC takes an initial snapshot of the existing MySQL table data.
--   2. After the snapshot, it switches to reading the binlog for ongoing changes.
--   3. All changes (INSERT, UPDATE, DELETE) are emitted as a changelog stream.
-- =============================================================================


-- =============================================================================
-- Table: mysql_orders (CDC Source)
-- =============================================================================
-- This table reads directly from MySQL's binlog using the mysql-cdc connector.
-- The PRIMARY KEY tells Flink which column(s) uniquely identify a row,
-- enabling correct handling of UPDATE and DELETE operations.
--
-- 'NOT ENFORCED' means Flink trusts the source to maintain the PK constraint
-- rather than enforcing it itself (standard for CDC sources).
-- =============================================================================

CREATE TABLE mysql_orders (
    order_id        INT,                -- Primary key from MySQL
    customer_id     INT,                -- FK to customers
    product_id      INT,                -- FK to products
    quantity        INT,                -- Number of items
    amount          DECIMAL(10, 2),     -- Order total
    status          VARCHAR(50),        -- Order status
    created_at      TIMESTAMP(3),       -- Creation timestamp
    updated_at      TIMESTAMP(3),       -- Last update timestamp
    PRIMARY KEY (order_id) NOT ENFORCED -- PK for changelog semantics
) WITH (
    'connector' = 'mysql-cdc',          -- Use Flink CDC MySQL connector
    'hostname' = 'mysql',               -- MySQL hostname
    'port' = '3306',                    -- MySQL port
    'username' = 'root',                -- MySQL username
    'password' = 'debezium',            -- MySQL password
    'database-name' = 'inventory',      -- Database to monitor
    'table-name' = 'orders',            -- Table to capture changes from
    'server-time-zone' = 'UTC'          -- Timezone for timestamp conversion
);


-- =============================================================================
-- Table: mysql_customers (CDC Source)
-- =============================================================================
-- Captures real-time changes to the customers table.
-- Useful as a dimension table for enriching order streams.
-- =============================================================================

CREATE TABLE mysql_customers (
    customer_id     INT,
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    email           VARCHAR(255),
    city            VARCHAR(100),
    state           VARCHAR(50),
    country         VARCHAR(10),
    created_at      TIMESTAMP(3),
    PRIMARY KEY (customer_id) NOT ENFORCED
) WITH (
    'connector' = 'mysql-cdc',
    'hostname' = 'mysql',
    'port' = '3306',
    'username' = 'root',
    'password' = 'debezium',
    'database-name' = 'inventory',
    'table-name' = 'customers',
    'server-time-zone' = 'UTC'
);


-- =============================================================================
-- Table: mysql_products (CDC Source)
-- =============================================================================
-- Captures real-time changes to the products table.
-- Useful as a dimension table for product catalog enrichment.
-- =============================================================================

CREATE TABLE mysql_products (
    product_id      INT,
    product_name    VARCHAR(255),
    category        VARCHAR(100),
    price           DECIMAL(10, 2),
    brand           VARCHAR(100),
    updated_at      TIMESTAMP(3),
    PRIMARY KEY (product_id) NOT ENFORCED
) WITH (
    'connector' = 'mysql-cdc',
    'hostname' = 'mysql',
    'port' = '3306',
    'username' = 'root',
    'password' = 'debezium',
    'database-name' = 'inventory',
    'table-name' = 'products',
    'server-time-zone' = 'UTC'
);


-- =============================================================================
-- Query: Monitor CDC changes in real time
-- =============================================================================
-- Once the tables are created, you can query them like any Flink table.
-- The results continuously update as MySQL data changes.
-- =============================================================================

-- View all current orders from MySQL (initial snapshot + ongoing changes)
-- SELECT * FROM mysql_orders;

-- Real-time order count by status
-- SELECT status, COUNT(*) AS cnt, SUM(amount) AS total
-- FROM mysql_orders
-- GROUP BY status;

-- Latest customer data
-- SELECT * FROM mysql_customers;

-- Products by category
-- SELECT category, COUNT(*) AS product_count, AVG(price) AS avg_price
-- FROM mysql_products
-- GROUP BY category;
