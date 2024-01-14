view: sales_managers {
  sql_table_name: "RAW"."SALES_MANAGERS" ;;

  dimension: person {
    type: string
    sql: ${TABLE}."PERSON" ;;
  }
  dimension: region {
    type: string
    sql: ${TABLE}."REGION" ;;
  }
  measure: count {
    type: count
  }
}
