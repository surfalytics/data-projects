# DBT Fundamentals

## Prerequisites

1. GitHub
  1.1 Account
  1.2 New Repo
  1.3 Codespace
2. CLI
3. Docker Desktop

## Prepare data in Redshift

Create schemas:

```sql
create schema if not exists jaffle_shop;
create schema if not exists stripe;
```

Create tables:

```sql
create table jaffle_shop.customers(
    id integer,
    first_name varchar(50),
    last_name varchar(50)
);

create table jaffle_shop.orders(
    id integer,
    user_id integer,
    order_date date,
    status varchar(50)
);

create table stripe.payment(
    id integer,
    orderid integer,
    paymentmethod varchar(50),
    status varchar(50),
    amount integer,
    created date
);
```

Ingest data:

```sql
copy jaffle_shop.customers( id, first_name, last_name)
from 's3://dbt-data-lake-xxxx/jaffle_shop_customers.csv'
iam_role 'arn:aws:iam::XXXXXXXXXX:role/RoleName'
region 'us-east-1'
delimiter ','
ignoreheader 1
acceptinvchars;

copy jaffle_shop.orders(id, user_id, order_date, status)
from 's3://dbt-data-lake-xxxx/jaffle_shop_orders.csv'
iam_role 'arn:aws:iam::XXXXXXXXXX:role/RoleName'
region 'us-east-1'
delimiter ','
ignoreheader 1
acceptinvchars;

copy stripe.payment(id, orderid, paymentmethod, status, amount, created)
from 's3://dbt-data-lake-xxxx/stripe_payments.csv'
iam_role 'arn:aws:iam::XXXXXXXXXX:role/RoleName'
region 'us-east-1'
delimiter ','
ignoreheader 1
Acceptinvchars;
```

```sql
select * from jaffle_shop.customers;
select * from jaffle_shop.orders;
select * from stripe.payment;
```

## Create new dbt project

Let's create a new reposity in GitHub in your account.


### Create profile for connection



### Build dbt model

```sql
with customers as (

    select
        id as customer_id,
        first_name,
        last_name

    from jaffle_shop.customers

),

orders as (

    select
        id as order_id,
        user_id as customer_id,
        order_date,
        status

    from jaffle_shop.orders

),

customer_orders as (

    select
        customer_id,

        min(order_date) as first_order_date,
        max(order_date) as most_recent_order_date,
        count(order_id) as number_of_orders

    from orders

    group by 1

),

final as (

    select
        customers.customer_id,
        customers.first_name,
        customers.last_name,
        customer_orders.first_order_date,
        customer_orders.most_recent_order_date,
        coalesce(customer_orders.number_of_orders, 0) as number_of_orders

    from customers

    left join customer_orders using (customer_id)

)

select * from final
```

## Change the way your model is materialized

```yaml
models:
  jaffle_shop:
    +materialized: table
    example:
      +materialized: view
```

or

```sql
{{
  config(
    materialized='view'
  )
}}

with customers as (

    select
        id as customer_id
        ...

)
```

`models/stg_customers.sql`

```sql
select
    id as customer_id,
    first_name,
    last_name

from jaffle_shop.customers
```

`models/stg_orders.sql`

```sql
select
    id as order_id,
    user_id as customer_id,
    order_date,
    status

from jaffle_shop.orders
```

`models/customers.sql`

```sql
with customers as (

    select * from {{ ref('stg_customers') }}

),

orders as (

    select * from {{ ref('stg_orders') }}

),

customer_orders as (

    select
        customer_id,

        min(order_date) as first_order_date,
        max(order_date) as most_recent_order_date,
        count(order_id) as number_of_orders

    from orders

    group by 1

),

final as (

    select
        customers.customer_id,
        customers.first_name,
        customers.last_name,
        customer_orders.first_order_date,
        customer_orders.most_recent_order_date,
        coalesce(customer_orders.number_of_orders, 0) as number_of_orders

    from customers

    left join customer_orders using (customer_id)

)

select * from final

```

## Adding Tests

```sql
version: 2

models:
  - name: customers
    columns:
      - name: customer_id
        tests:
          - unique
          - not_null

  - name: stg_customers
    columns:
      - name: customer_id
        tests:
          - unique
          - not_null

  - name: stg_orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: status
        tests:
          - accepted_values:
              values: ['placed', 'shipped', 'completed', 'return_pending', 'returned']
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('stg_customers')
              field: customer_id
```

## Documentation

`models/schema.yml`

```yaml
version: 2

models:
  - name: customers
    description: One record per customer
    columns:
      - name: customer_id
        description: Primary key
        tests:
          - unique
          - not_null
      - name: first_order_date
        description: NULL when a customer has not yet placed an order.

  - name: stg_customers
    description: This model cleans up customer data
    columns:
      - name: customer_id
        description: Primary key
        tests:
          - unique
          - not_null

  - name: stg_orders
    description: This model cleans up order data
    columns:
      - name: order_id
        description: Primary key
        tests:
          - unique
          - not_null
      - name: status
        tests:
          - accepted_values:
              values: ['placed', 'shipped', 'completed', 'return_pending', 'returned']
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('stg_customers')
              field: customer_id
```

We can generate documentation: `dbt docs generate`

Example:

```yaml
  version: 2

  models:
  - name: customers
    description: >
      Lorem ipsum **dolor** sit amet, consectetur adipisicing elit, sed do eiusmod
      tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
      quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
      consequat.
```

```yaml
  version: 2

  models:
  - name: customers
    description: |
      ### Lorem ipsum

      * dolor sit amet, consectetur adipisicing elit, sed do eiusmod
      * tempor incididunt ut labore et dolore magna aliqua.
```

## Reorganize models

In `staging/jaffle_shop` we create `stg_jaffle_shop__customers.sql`

```sql
select
    id as customer_id,
    first_name,
    last_name

from raw.jaffle_shop.customers
```

Also `stg_jaffle_shop__orders.sql`

```sql
select
    id as order_id,
    user_id as customer_id,
    order_date,
    status

from raw.jaffle_shop.orders
```

In `marts/marketing` we create `dim_customers.sql`

```sql
with customers as (

     select * from {{ ref('stg_jaffle_shop__customers') }}

),

orders as (

    select * from {{ ref('stg_jaffle_shop__orders') }}

),

customer_orders as (

    select
        customer_id,

        min(order_date) as first_order_date,
        max(order_date) as most_recent_order_date,
        count(order_id) as number_of_orders

    from orders

    group by 1

),

final as (

    select
        customers.customer_id,
        customers.first_name,
        customers.last_name,
        customer_orders.first_order_date,
        customer_orders.most_recent_order_date,
        coalesce (customer_orders.number_of_orders, 0)
        as number_of_orders

    from customers

    left join customer_orders using (customer_id)

)

select * from final
```

In `dbt_project.yml`:


```yaml
models:
  jaffle_shop:
    staging:
      +materialized: view

    marts:
      +materialized: table
```

In `staging/stripe/` add `stg_stripe__payments.sql`

```sql
select
    id as payment_id,
    orderid as order_id,
    paymentmethod as payment_method,
    status,

    -- amount is stored in cents, convert it to dollars
    amount / 100 as amount,
    created as created_at

from raw.stripe.payment
```

`marts/finance/fct_orders.sql`

```sql
with orders as  (
    select * from {{ ref ('stg_jaffle_shop__orders' )}}
),

payments as (
    select * from {{ ref ('stg_stripe__payments') }}
),

order_payments as (
    select
        order_id,
        sum (case when status = 'success' then amount end) as amount

    from payments
    group by 1
),

 final as (

    select
        orders.order_id,
        orders.customer_id,
        orders.order_date,
        coalesce (order_payments.amount, 0) as amount

    from orders
    left join order_payments using (order_id)
)

select * from final
```


In `marts/marketing/` add `dim_customers.sql `:

```sql
with customers as (
    select * from {{ ref ('stg_jaffle_shop__customers')}}
),
orders as (
    select * from {{ ref ('fct_orders')}}
),
customer_orders as (
    select
        customer_id,
        min (order_date) as first_order_date,
        max (order_date) as most_recent_order_date,
        count(order_id) as number_of_orders,
        sum(amount) as lifetime_value
    from orders
    group by 1
),
 final as (
    select
        customers.customer_id,
        customers.first_name,
        customers.last_name,
        customer_orders.first_order_date,
        customer_orders.most_recent_order_date,
        coalesce (customer_orders.number_of_orders, 0) as number_of_orders,
        customer_orders.lifetime_value
    from customers
    left join customer_orders using (customer_id)
)
select * from final
```

### Change materisalisation

```sql
{{ config(
materialized='table'
) }}
 ```

 ```sql
{{ config(
materialized='view'
) }}
 ```

### REF macro

The `ref` function allows us to build dependencies between models in a flexible way that can be shared in a common code base. The `ref` function compiles to the name of the database object as it has been created on the most recent execution of `dbt run` in the particular development environment. This is determined by the environment configuration that was set up when the project was created.

### Naming Conventions

- Sources (src) refer to the raw table data that have been built in the warehouse through a loading process. (We will cover configuring Sources in the Sources module)
- Staging (stg) refers to models that are built directly on top of sources. These have a one-to-one relationship with sources tables. These are used for very light transformations that shape the data into what you want it to be. These models are used to clean and standardize the data before transforming data downstream. Note: These are typically materialized as views.
- Intermediate (int) refers to any models that exist between final fact and dimension tables. These should be built on staging models rather than directly on sources to leverage the data cleaning that was done in staging.
- Fact (fct) refers to any data that represents something that occurred or is occurring. Examples include sessions, transactions, orders, stories, votes. These are typically skinny, long tables.
- Dimension (dim) refers to data that represents a person, place or thing. Examples include customers, products, candidates, buildings, employees.


## Sources

In `models/staging/jaffle_shop/` create `src_jaffle_shop.yml`

```yaml
version: 2

sources:
  - name: jaffle_shop
    database: raw
    schema: jaffle_shop
    tables:
      - name: customers
      - name: orders
```

In `models/staging/jaffle_shop/` update `stg_customers.sql`

```sql
select
    id as customer_id,
    first_name,
    last_name
from {{ source('jaffle_shop', 'customers') }}
```

In `stg_orders.sql`

```sql
select
    id as order_id,
    user_id as customer_id,
    order_date,
    status
from {{ source('jaffle_shop', 'orders') }}
```

### Freshness test

In `models/staging/jaffle_shop/src_jaffle_shop.yml`

```yaml
version: 2

sources:
  - name: jaffle_shop
    database: raw
    schema: jaffle_shop
    tables:
      - name: customers
      - name: orders
        loaded_at_field: _etl_loaded_at
        freshness:
          warn_after: {count: 12, period: hour}
          error_after: {count: 24, period: hour}
```

Also add `src_stripe.yml`:

```yaml
version: 2

sources:
  - name: stripe
    database: raw
    schema: stripe
    tables:
      - name: payment
        loaded_at_field: _batched_at
        freshness:
          warn_after: {count: 12, period: hour}
          error_after: {count: 24, period: hour}
```

Update model in `models/staging/stripe/stg_payments.sql`:

```sql
select
    id as payment_id,
    orderid as order_id,
    paymentmethod as payment_method,
    status,
    -- amount is stored in cents, convert it to dollars
    amount / 100 as amount,
    created as created_at
from {{ source('stripe', 'payment') }}
```

Run `dbt source freshness`.

## Tests

Generic and Singular.

In `models/staging/jaffle_shop/stg_jaffle_shop.yml`

```yaml
version: 2

models:
  - name: stg_jaffle_shop__customers
    columns:
      - name: customer_id
        data_tests:
          - unique
          - not_null

  - name: stg_jaffle_shop__orders
    columns:
      - name: order_id
        data_tests:
          - unique
          - not_null
      - name: status
        data_tests:
          - accepted_values:
              values:
                - completed
                - shipped
                - returned
                - return_pending
                - placed
```

Create `tests/assert_positive_total_for_payments.sql`

```sql
-- Refunds have a negative amount, so the total amount should always be >= 0.
-- Therefore return records where this isn't true to make the test fail.
select
    order_id,
    sum(amount) as total_amount
from {{ ref('stg_stripe__payments') }}
group by 1
having total_amount > 0
```

Execute tests:

- Execute `dbt test` to run all generic and singular tests in your project.
- Execute `dbt test --select test_type:generic` to run only generic tests in your project.
- Execute `dbt test --select test_type:singular` to run only singular tests in your project.

In `models/staging/jaffle_shop/src_jaffle_shop.yml`:

```yaml
version: 2

sources:
  - name: jaffle_shop
    database: raw
    schema: jaffle_shop
    tables:
      - name: customers
        columns:
          - name: id
            tests:
              - unique
              - not_null

      - name: orders
        columns:
          - name: id
            tests:
              - unique
              - not_null
        loaded_at_field: _etl_loaded_at
        freshness:
          warn_after: {count: 12, period: hour}
          error_after: {count: 24, period: hour}
```

## Documentation

In `models/staging/jaffle_shop/stg_jaffle_shop.yml`:

```yaml
version: 2

models:
  - name: stg_customers
    description: Staged customer data from our jaffle shop app.
    columns:
      - name: customer_id
        description: The primary key for customers.
        tests:
          - unique
          - not_null

  - name: stg_orders
    description: Staged order data from our jaffle shop app.
    columns:
      - name: order_id
        description: Primary key for orders.
        tests:
          - unique
          - not_null
      - name: status
        description: '{{ doc("order_status") }}'
        tests:
          - accepted_values:
              values:
                - completed
                - shipped
                - returned
                - placed
                - return_pending
      - name: customer_id
        description: Foreign key to stg_customers.customer_id.
        tests:
          - relationships:
              to: ref('stg_customers')
              field: customer_id
```

We can describe individual object:

In `models/staging/jaffle_shop/jaffle_shop.md`:

```yaml
{% docs order_status %}

One of the following values:

| status         | definition                                       |
|----------------|--------------------------------------------------|
| placed         | Order placed, not yet shipped                    |
| shipped        | Order has been shipped, not yet been delivered   |
| completed      | Order has been received by customers             |
| return pending | Customer indicated they want to return this item |
| returned       | Item has been returned                           |

{% enddocs %}
```

In `models/staging/jaffle_shop/src_jaffle_shop.yml`:

```yaml
version: 2

sources:
  - name: jaffle_shop
    description: A clone of a Postgres application database.
    database: raw
    schema: jaffle_shop
    tables:
      - name: customers
        description: Raw customers data.
        columns:
          - name: id
            description: Primary key for customers.
            tests:
              - unique
              - not_null

      - name: orders
        description: Raw orders data.
        columns:
          - name: id
            description: Primary key for orders.
            tests:
              - unique
              - not_null
        loaded_at_field: _etl_loaded_at
        freshness:
          warn_after: {count: 12, period: hour}
          error_after: {count: 24, period: hour}
```

In `models/staging/jaffle_shop/stg_jaffle_shop.yml`:

```yaml
version: 2

models:
  - name: stg_jaffle_shop__customers
    description: Staged customer data from our jaffle shop app.
    columns:
      - name: customer_id
        description: The primary key for customers.
        tests:
          - unique
          - not_null

  - name: stg_jaffle_shop__orders
    description: Staged order data from our jaffle shop app.
    columns:
      - name: order_id
        description: Primary key for orders.
        tests:
          - unique
          - not_null
      - name: status
        description: "{{ doc('order_status') }}"
        tests:
          - accepted_values:
              values:
                - completed
                - shipped
                - returned
                - placed
                - return_pending
      - name: customer_id
        description: Foreign key to stg_customers.customer_id.
        tests:
          - relationships:
              to: ref('stg_jaffle_shop__customers')
              field: customer_id
```

Generate: `dbt docs generate`

## dbt packages


## dbt seeds


## dbt macros