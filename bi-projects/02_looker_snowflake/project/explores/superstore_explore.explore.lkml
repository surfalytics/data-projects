include: "/views/*"

explore: orders {
  view_name: orders
  join: returned_orders {
    type: left_outer
    relationship: many_to_many  # order_id repeats in both tables
    sql_on: ${returned_orders.order_id} =  ${orders.order_id};;
  }
  join: sales_managers {
    type: inner
    relationship: many_to_one
    sql_on: ${sales_managers.region} = ${orders.region};;
  }
}
