-- =============================================================================
-- Solution: Exercise 3.1 -- Real-Time Order Status Tracker
-- =============================================================================
-- Uses Flink CDC to read MySQL orders and customers, joins them, and publishes
-- an enriched status feed to a Kafka upsert topic.
-- =============================================================================

-- Step 1: Create MySQL CDC source for orders
CREATE TABLE mysql_orders (
    order_id    INT,
    customer_id INT,
    product_id  INT,
    quantity    INT,
    amount      DECIMAL(10, 2),
    status      VARCHAR(50),
    created_at  TIMESTAMP(3),
    updated_at  TIMESTAMP(3),
    PRIMARY KEY (order_id) NOT ENFORCED
) WITH (
    'connector' = 'mysql-cdc',
    'hostname' = 'mysql',
    'port' = '3306',
    'username' = 'root',
    'password' = 'debezium',
    'database-name' = 'inventory',
    'table-name' = 'orders',
    'server-time-zone' = 'UTC'
);

-- Step 2: Create MySQL CDC source for customers
CREATE TABLE mysql_customers (
    customer_id INT,
    first_name  VARCHAR(100),
    last_name   VARCHAR(100),
    email       VARCHAR(255),
    city        VARCHAR(100),
    state       VARCHAR(50),
    country     VARCHAR(10),
    created_at  TIMESTAMP(3),
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

-- Step 3: Create the Kafka upsert sink
CREATE TABLE order_status_tracker_sink (
    order_id       INT,
    customer_name  STRING,
    customer_email STRING,
    amount         DECIMAL(10, 2),
    status         STRING,
    updated_at     TIMESTAMP(3),
    PRIMARY KEY (order_id) NOT ENFORCED
) WITH (
    'connector' = 'upsert-kafka',
    'topic' = 'order-status-tracker',
    'properties.bootstrap.servers' = 'kafka:29092',
    'key.format' = 'json',
    'value.format' = 'json'
);

-- Step 4: Join orders with customers and insert into sink
-- When an order status changes in MySQL, or a customer name changes,
-- the result automatically updates in the Kafka topic.
INSERT INTO order_status_tracker_sink
SELECT
    o.order_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.email                             AS customer_email,
    o.amount,
    o.status,
    o.updated_at
FROM mysql_orders AS o
INNER JOIN mysql_customers AS c
    ON o.customer_id = c.customer_id;
