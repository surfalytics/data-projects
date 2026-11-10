---
title: "KPI Dashboard with Looker and Snowflake"
category: "BI"
level: "Intermediate"
roles: ["BI Developer", "Analytics Engineer"]
duration: "4 assignments, ~1-4 hours each"
cost: "Free trial"
tools: ["Looker", "LookML", "Snowflake", "Git"]
status: "In progress"
---

# KPI Dashboard with Looker and Snowflake

![Architecture](images/architecture.png)

## Project card

| Level | Roles | Duration | Cost | Status |
|---|---|---|---|---|
| Intermediate | BI Developer, Analytics Engineer | 4 assignments, ~1-4 h each | Free trial | In progress |

## Goal

You build a Superstore KPI dashboard in Looker. The data is in Snowflake. You write the semantic layer in LookML: views, an explore and a model. Then you build the dashboard and keep it in Git as code.

## What you will learn

- Load CSV files into Snowflake.
- Connect Looker to Snowflake.
- Write LookML views, dimensions, measures and parameters.
- Join views in an explore and set join relationships.
- Build a dashboard with filters and save it as LookML.

## Who it is for

- **BI Developer**: learn Looker, a popular enterprise BI tool with a code-based semantic layer.
- **Analytics Engineer**: learn how a semantic layer sits on top of the warehouse.

## Tools and services

| Tool | Used for | Free option |
|---|---|---|
| Snowflake | Data warehouse | trial (30 days) |
| Looker | BI platform from Google Cloud | trial (ask Google Cloud) |
| LookML | Semantic layer as code | yes (part of Looker) |
| Git | Version control for the LookML project | yes |

Key terms:

- **Looker:** an enterprise platform for BI, data apps and embedded analytics. You explore and share data in real time.
- **LookML:** the Looker modeling language. It defines dimensions, measures and joins on top of SQL tables.
- **Snowflake:** a cloud data warehouse. Storage and compute are separate, so you scale them independently.

## Architecture

The diagram is at the top of this page. Source file: [`images/architecture.excalidraw`](images/architecture.excalidraw). Open it at [excalidraw.com](https://excalidraw.com) to copy or edit it.

Data flow:

1. Superstore CSV files (orders, returns, people) are the source.
2. You load the files into the Snowflake `RAW` schema.
3. Looker connects to Snowflake with the connection `superstore_snowflake_connection`.
4. LookML views, an explore and a model define the business logic.
5. The Superstore KPI dashboard reads from the explore. The LookML project lives in Git.

## Dataset

- **Source:** Superstore sample data, in [`project/source_files`](project/source_files). Files use `|` as the delimiter and have a header row.
- **Tables / entities:**

| File | Snowflake table | Content |
|---|---|---|
| [`supestore_orders.csv`](project/source_files/supestore_orders.csv) | `RAW.ORDERS` | Order lines: dates, customer, product, sales, profit |
| [`supestore_returns.csv`](project/source_files/supestore_returns.csv) | `RAW.RETURNED_ORDERS` | Returned order IDs |
| [`supestore_people.csv`](project/source_files/supestore_people.csv) | `RAW.SALES_MANAGERS` | Regional sales manager |

- **Size:** about 10,000 order lines, 800 returns, 4 managers.

## Prerequisites

- A Snowflake account. Start a [30-day free trial](https://signup.snowflake.com/).
- A Looker instance. Looker has no free tier. Ask for a trial through [Google Cloud](https://cloud.google.com/looker). Do not confuse it with Looker Studio, a different free tool.
- Basic SQL.
- Optional: [`de-projects/02_dbt_core_snowflake`](../../de-projects/02_dbt_core_snowflake) to model the data with dbt first.
- New to Git, CLI or Docker? Start with [Surfalytics Module 0](https://www.youtube.com/watch?v=LJIiCLu2gr8&list=PLNCDg7zJiXhP5Z_-TXUdorz2n7sjYHHKE&index=1).

## Assignments

Work at your own pace. Each assignment shows the expected time. The finished LookML project is in [`project/`](project). Try to write it yourself first, then compare.

### Assignment 1: Load data into Snowflake (~1 h)

**Goal:** Load the 3 Superstore files into the Snowflake `RAW` schema.

**Steps:**

1. Create a database and the `RAW` schema.
2. Create a file format for `|` delimited files and the 3 tables:

   ```sql
   CREATE DATABASE IF NOT EXISTS SUPERSTORE;
   CREATE SCHEMA IF NOT EXISTS SUPERSTORE.RAW;
   USE SCHEMA SUPERSTORE.RAW;

   CREATE OR REPLACE FILE FORMAT pipe_csv
     TYPE = CSV
     FIELD_DELIMITER = '|'
     SKIP_HEADER = 1
     FIELD_OPTIONALLY_ENCLOSED_BY = '"';

   CREATE OR REPLACE TABLE ORDERS (
       ROW_ID        NUMBER,
       ORDER_ID      VARCHAR,
       ORDER_DATE    DATE,
       SHIP_DATE     DATE,
       SHIP_MODE     VARCHAR,
       CUSTOMER_ID   VARCHAR,
       CUSTOMER_NAME VARCHAR,
       SEGMENT       VARCHAR,
       COUNTRY       VARCHAR,
       CITY          VARCHAR,
       STATE         VARCHAR,
       POSTAL_CODE   VARCHAR,
       REGION        VARCHAR,
       PRODUCT_ID    VARCHAR,
       CATEGORY      VARCHAR,
       SUBCATEGORY   VARCHAR,
       PRODUCT_NAME  VARCHAR,
       SALES         NUMBER(18,4),
       QUANTITY      NUMBER,
       DISCOUNT      NUMBER(5,2),
       PROFIT        NUMBER(18,4)
   );

   CREATE OR REPLACE TABLE RETURNED_ORDERS (
       RETURNED VARCHAR,
       ORDER_ID VARCHAR
   );

   CREATE OR REPLACE TABLE SALES_MANAGERS (
       PERSON VARCHAR,
       REGION VARCHAR
   );
   ```

3. Upload the files. Use the Snowsight UI (**Data → Add Data → Load data into a Table**) with the `pipe_csv` file format. Or use a stage and `COPY INTO`.
4. Check row counts.

**Deliverable:** SQL script and row counts for the 3 tables.

**Done when:**

- [ ] `RAW.ORDERS` has about 9,994 rows.
- [ ] `RAW.RETURNED_ORDERS` has about 800 rows.
- [ ] `RAW.SALES_MANAGERS` has 4 rows.

**Hints:** [Load data with Snowsight](https://docs.snowflake.com/en/user-guide/data-load-web-ui), [COPY INTO](https://docs.snowflake.com/en/sql-reference/sql/copy-into-table).

### Assignment 2: Connect Looker to Snowflake (~1 h)

**Goal:** Create a Looker connection and a LookML project linked to Git.

**Steps:**

1. In Snowflake, create a user, role and warehouse for Looker. Grant read access to `SUPERSTORE.RAW`.
2. In Looker, go to **Admin → Database → Connections** and add a Snowflake connection. Name it `superstore_snowflake_connection`.
3. Test the connection.
4. Create a new LookML project. Connect it to a GitHub repo.

**Deliverable:** Screenshot of a successful connection test.

**Done when:**

- [ ] The connection test passes.
- [ ] The LookML project is linked to Git.

**Hints:** [Looker Snowflake connection](https://cloud.google.com/looker/docs/db-config-snowflake). Never commit passwords or keys to Git.

### Assignment 3: Build the LookML model (~3 h)

**Goal:** Write views, an explore and a model for the Superstore data.

**Steps:**

1. Create 3 views, one per table:
   - [`orders.view.lkml`](project/views/orders.view.lkml): dimensions, a `order` date group, measures `total_sales`, `total_profit`, `total_customers`, `total_orders`, and the `profit_or_sales` parameter.
   - [`returned_orders.view.lkml`](project/views/returned_orders.view.lkml): `total_returned_orders`.
   - [`sales_managers.view.lkml`](project/views/sales_managers.view.lkml): manager per region.
2. Create the explore [`superstore_explore.explore.lkml`](project/explores/superstore_explore.explore.lkml):
   - `orders` left join `returned_orders` on `order_id`.
   - `orders` join `sales_managers` on `region`.
3. Create the model [`superstore_model.model.lkml`](project/models/superstore_model.model.lkml). It uses the connection and includes all views and explores.
4. Validate the LookML and commit.

**Deliverable:** LookML files in Git.

**Done when:**

- [ ] LookML validation shows no errors.
- [ ] You can query sales by region in the explore.
- [ ] The returned orders share looks correct.

**Hints:**

- Check the primary key. One order has many lines, so `order_id` is not unique in `ORDERS`. `row_id` is.
- Check the join relationship. The returns file has duplicate order IDs.
- [LookML introduction](https://cloud.google.com/looker/docs/what-is-lookml).

### Assignment 4: Build the KPI dashboard (~3 h)

**Goal:** Build the Superstore KPI dashboard and save it as LookML.

**Steps:**

1. Add KPI tiles: % of returned orders, total sales, total profit, customers, profit ratio, orders.
2. Add charts:
   - Sales and profit by month (area).
   - Profit or sales by state (map).
   - Profit or sales by region (column).
   - Number of orders by manager (bar).
3. Add filters: Period, Profit or Sales (toggle), Segment, Category, Subcategory.
4. Save the dashboard as LookML. Compare with [`superstore.dashboard.lookml`](project/dashboards/superstore.dashboard.lookml).

**Deliverable:** Dashboard screenshot and the dashboard LookML file in Git.

**Done when:**

- [ ] All tiles and charts show data.
- [ ] The Profit or Sales toggle changes the charts.
- [ ] Filters apply to all tiles.

**Hints:** [LookML dashboards](https://cloud.google.com/looker/docs/building-lookml-dashboards).

## Final result

- A Snowflake database with Superstore data.
- A LookML project in Git: views, explore, model and dashboard.
- A KPI dashboard with filters. Post a screenshot on LinkedIn.
- Interview pitch: "I built a Superstore KPI dashboard in Looker on Snowflake. I wrote the semantic layer in LookML, with a parameter to switch between profit and sales. The project is in Git, so changes are reviewed like code."

## Clean up

- **Snowflake:** run `DROP DATABASE SUPERSTORE;`. Drop the Looker user, role and warehouse if you created them.
- **Looker:** delete the connection and the project if your trial instance stays open.

## Resources

- [Looker demo video](https://www.youtube.com/watch?v=FBlyD2nCJds): a quick look at the product.
- [Looker learning path from Google](https://www.cloudskillsboost.google/paths/28): official course.
- [Udemy course on Looker](https://www.udemy.com/course/looker-learning-tutorial-for-beginners/): beginner course.
- [Looker documentation](https://cloud.google.com/looker/docs): full reference.

## Community solutions

Share your repo in Discord. We add the best ones here.

- Creating a Superstore KPI dashboard using Looker and Snowflake: [Medium article](https://medium.com/@kazarmax/creating-a-superstore-kpi-dashboard-using-looker-and-snowflake-73fec857132d)
