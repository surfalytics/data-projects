view: returned_orders {
  sql_table_name: "RAW"."RETURNED_ORDERS" ;;

  dimension: order_id {
    type: string
    # hidden: yes
    sql: ${TABLE}."ORDER_ID" ;;
  }
  dimension: returned {
    type: yesno
    sql: ${TABLE}."RETURNED" ;;
  }
  measure: total_returned_orders {
    type: count_distinct
    sql: ${order_id} ;;
  }
  measure: count {
    type: count
    drill_fields: [orders.product_name, orders.order_id, orders.customer_name]
  }
}
