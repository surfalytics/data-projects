view: orders {
  sql_table_name: "RAW"."ORDERS" ;;
  drill_fields: [order_id]

  parameter: profit_or_sales {
    type: unquoted
    allowed_value: { value: "Profit" }
    allowed_value: { value: "Sales" }
  }

  dimension: order_id {
    primary_key: yes
    type: string
    sql: ${TABLE}."ORDER_ID" ;;
  }
  dimension: category {
    type: string
    sql: ${TABLE}."CATEGORY" ;;
  }
  dimension: city {
    type: string
    sql: ${TABLE}."CITY" ;;
  }
  dimension: country {
    type: string
    map_layer_name: countries
    sql: ${TABLE}."COUNTRY" ;;
  }
  dimension: customer_id {
    type: string
    sql: ${TABLE}."CUSTOMER_ID" ;;
  }
  dimension: customer_name {
    type: string
    sql: ${TABLE}."CUSTOMER_NAME" ;;
  }
  dimension_group: order {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    convert_tz: no
    datatype: date
    sql: ${TABLE}."ORDER_DATE" ;;
  }
  dimension: postal_code {
    type: string
    sql: ${TABLE}."POSTAL_CODE" ;;
  }
  dimension: product_id {
    type: string
    sql: ${TABLE}."PRODUCT_ID" ;;
  }
  dimension: product_name {
    type: string
    sql: ${TABLE}."PRODUCT_NAME" ;;
  }
  dimension: quantity {
    type: number
    sql: ${TABLE}."QUANTITY" ;;
  }
  dimension: region {
    type: string
    sql: ${TABLE}."REGION" ;;
  }
  dimension: row_id {
    type: number
    sql: ${TABLE}."ROW_ID" ;;
  }
  dimension: segment {
    type: string
    sql: ${TABLE}."SEGMENT" ;;
  }
  dimension_group: ship {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    convert_tz: no
    datatype: date
    sql: ${TABLE}."SHIP_DATE" ;;
  }
  dimension: ship_mode {
    type: string
    sql: ${TABLE}."SHIP_MODE" ;;
  }
  dimension: state {
    type: string
    sql: ${TABLE}."STATE" ;;
    map_layer_name: us_states
  }
  dimension: subcategory {
    type: string
    sql: ${TABLE}."SUBCATEGORY" ;;
  }
  measure: sales {
    type: number
    sql: ${TABLE}."SALES" ;;
  }
  measure: total_sales {
    type: sum
    sql: ${TABLE}."SALES" ;;
    value_format: "$#,##0"  # Formats as currency with commas
  }
  measure: profit {
    type: number
    sql: ${TABLE}."PROFIT" ;;
  }
  measure: total_profit {
    type: sum
    sql: ${TABLE}."PROFIT" ;;
    value_format: "$#,##0"  # Formats as currency with commas
  }
  measure: dynamic_profit_or_sales {
    type: number
    sql: SUM(CASE
            WHEN {% condition profit_or_sales %} 'Profit' {% endcondition %} THEN ${profit}
            ELSE ${sales}
          END) ;;
    value_format: "$#,##0"
    html: "{% if profit_or_sales._parameter_value == 'Profit' %}
    Profit: {{ rendered_value }}
    {% else %}
    Sales: {{ rendered_value }}
    {% endif %}" ;;
  }
  measure: total_customers {
    type: count_distinct
    sql: ${customer_id} ;;  # Reference the customer_id field
    label: "Total Customers"
  }
  measure: total_orders {
    type: count_distinct
    sql: ${order_id} ;;  # Reference the customer_id field
    label: "Total Orders"
  }
  measure: discount {
    type: number
    sql: ${TABLE}."DISCOUNT" ;;
  }
  measure: count {
    type: count
    drill_fields: [order_id, product_name, customer_name, returned_orders.count]
  }
}
