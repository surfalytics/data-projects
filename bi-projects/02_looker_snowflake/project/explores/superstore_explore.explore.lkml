include: "/views/*"

explore: orders {
  view_name: orders
  join: returned_orders {
    type: left_outer
    relationship: one_to_one
    sql_on: ${returned_orders.order_id} =  ${orders.order_id};;
  }
  join: sales_managers {
    type: inner
    relationship: many_to_one
    sql_on: ${sales_managers.region} = ${orders.region};;
  }
}
