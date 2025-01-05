create schema if not exists jaffle_shop;
create schema if not exists stripe;

create schema if not exists dev;

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
