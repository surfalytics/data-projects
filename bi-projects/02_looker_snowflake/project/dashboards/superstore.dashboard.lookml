---
- dashboard: superstore_kpi_dashboard
  title: Superstore KPI Dashboard
  layout: newspaper
  preferred_viewer: dashboards-next
  crossfilter_enabled: true
  description: ''
  refresh: 1 hour
  preferred_slug: FC5nzJ38VdhL9zvl6vCMG6
  elements:
  - title: "% of returned orders"
    name: "% of returned orders"
    model: superstore_model
    explore: orders
    type: single_value
    fields: [returned_orders.total_returned_orders, orders.total_orders]
    limit: 5000
    column_limit: 50
    dynamic_fields:
    - category: table_calculation
      expression: "${returned_orders.total_returned_orders}/${orders.total_orders}"
      label: returned_orders_ratio
      value_format:
      value_format_name: percent_2
      _kind_hint: measure
      table_calculation: returned_orders_ratio
      _type_hint: number
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    show_sql_query_menu_options: false
    show_totals: true
    show_row_totals: true
    show_view_names: false
    show_row_numbers: true
    transpose: false
    truncate_text: true
    truncate_header: false
    size_to_fit: true
    minimum_column_width: 75
    series_labels: {}
    series_cell_visualizations:
      returned_orders.count:
        is_active: true
    table_theme: white
    limit_displayed_rows: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    hidden_pivots: {}
    hide_totals: false
    hide_row_totals: false
    defaults_version: 1
    value_labels: legend
    label_type: labPer
    hidden_fields: [returned_orders.total_returned_orders, orders.total_orders]
    hidden_points_if_no: []
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    legend_position: center
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: true
    interpolation: linear
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    ordering: none
    show_null_labels: false
    listen:
      Period: orders.order_month
      Segment: orders.segment
      Category: orders.category
      Subcategory: orders.subcategory
    row: 0
    col: 20
    width: 4
    height: 2
  - title: Total sales
    name: Total sales
    model: superstore_model
    explore: orders
    type: single_value
    fields: [orders.sales]
    limit: 5000
    column_limit: 50
    dynamic_fields:
    - category: table_calculation
      expression: sum(${orders.sales})
      label: Total sales
      value_format:
      value_format_name: usd_0
      _kind_hint: measure
      table_calculation: total_sales
      _type_hint: number
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    value_labels: legend
    label_type: labPer
    hidden_fields: [orders.sales]
    listen:
      Period: orders.order_month
      Segment: orders.segment
      Category: orders.category
      Subcategory: orders.subcategory
    row: 0
    col: 0
    width: 4
    height: 2
  - title: Total profit
    name: Total profit
    model: superstore_model
    explore: orders
    type: single_value
    fields: [orders.profit]
    limit: 5000
    column_limit: 50
    dynamic_fields:
    - category: table_calculation
      expression: sum(${orders.profit})
      label: Total profit
      value_format:
      value_format_name: usd_0
      _kind_hint: measure
      table_calculation: total_profit
      _type_hint: number
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    hidden_fields: [orders.profit]
    listen:
      Period: orders.order_month
      Segment: orders.segment
      Category: orders.category
      Subcategory: orders.subcategory
    row: 0
    col: 4
    width: 4
    height: 2
  - title: Customers
    name: Customers
    model: superstore_model
    explore: orders
    type: single_value
    fields: [orders.customer_id]
    sorts: [orders.customer_id]
    limit: 5000
    column_limit: 50
    total: true
    dynamic_fields:
    - category: measure
      expression:
      label: count orders
      value_format:
      value_format_name:
      based_on: orders.order_id
      _kind_hint: measure
      measure: count_orders
      type: count_distinct
      _type_hint: number
    - category: measure
      expression:
      label: count returned orders
      value_format:
      value_format_name:
      based_on: returned_orders.order_id
      _kind_hint: measure
      measure: count_returned_orders
      type: count_distinct
      _type_hint: number
    - category: dimension
      expression: '"returned orders ratio"'
      label: returned orders ratio
      value_format:
      value_format_name: ''
      dimension: returned_orders_ratio
      _kind_hint: dimension
      _type_hint: string
    - category: table_calculation
      expression: count_distinct(${orders.customer_id})
      label: Customers
      value_format:
      value_format_name:
      _kind_hint: dimension
      table_calculation: customers
      _type_hint: number
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    show_sql_query_menu_options: false
    show_totals: true
    show_row_totals: true
    show_view_names: false
    show_row_numbers: true
    transpose: false
    truncate_text: true
    truncate_header: false
    size_to_fit: true
    minimum_column_width: 75
    series_labels: {}
    series_cell_visualizations:
      returned_orders.count:
        is_active: true
    table_theme: white
    limit_displayed_rows: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    hidden_pivots: {}
    hide_totals: false
    hide_row_totals: false
    defaults_version: 1
    value_labels: legend
    label_type: labPer
    hidden_fields: [orders.customer_id]
    hidden_points_if_no: []
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    legend_position: center
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: true
    interpolation: linear
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    ordering: none
    show_null_labels: false
    listen:
      Period: orders.order_month
      Segment: orders.segment
      Category: orders.category
      Subcategory: orders.subcategory
    row: 0
    col: 8
    width: 4
    height: 2
  - title: Profit ratio
    name: Profit ratio
    model: superstore_model
    explore: orders
    type: single_value
    fields: [orders.total_profit, orders.total_sales]
    limit: 5000
    column_limit: 50
    dynamic_fields:
    - category: table_calculation
      expression: "${orders.total_profit}/${orders.total_sales}"
      label: profit_ratio
      value_format:
      value_format_name: percent_1
      _kind_hint: measure
      table_calculation: profit_ratio
      _type_hint: number
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    show_sql_query_menu_options: false
    show_totals: true
    show_row_totals: true
    show_view_names: false
    show_row_numbers: true
    transpose: false
    truncate_text: true
    truncate_header: false
    size_to_fit: true
    minimum_column_width: 75
    series_labels: {}
    series_cell_visualizations:
      returned_orders.count:
        is_active: true
    table_theme: white
    limit_displayed_rows: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    hidden_pivots: {}
    hide_totals: false
    hide_row_totals: false
    defaults_version: 1
    value_labels: legend
    label_type: labPer
    hidden_fields: [orders.total_profit, orders.total_sales]
    hidden_points_if_no: []
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    legend_position: center
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: true
    interpolation: linear
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    ordering: none
    show_null_labels: false
    listen:
      Period: orders.order_month
      Segment: orders.segment
      Category: orders.category
      Subcategory: orders.subcategory
    row: 0
    col: 16
    width: 4
    height: 2
  - title: Orders
    name: Orders
    model: superstore_model
    explore: orders
    type: single_value
    fields: [orders.order_id]
    limit: 5000
    column_limit: 50
    dynamic_fields:
    - category: table_calculation
      expression: count_distinct(${orders.order_id})
      label: Orders
      value_format:
      value_format_name:
      _kind_hint: dimension
      table_calculation: orders
      _type_hint: number
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    hidden_fields: [orders.order_id]
    hidden_pivots: {}
    listen:
      Period: orders.order_month
      Segment: orders.segment
      Category: orders.category
      Subcategory: orders.subcategory
    row: 0
    col: 12
    width: 4
    height: 2
  - title: Sales and Profit by Month
    name: Sales and Profit by Month
    model: superstore_model
    explore: orders
    type: looker_area
    fields: [orders.order_month, orders.total_profit, orders.total_sales]
    fill_fields: [orders.order_month]
    sorts: [orders.order_month desc]
    limit: 500
    column_limit: 50
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: right
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: true
    interpolation: linear
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    x_axis_zoom: true
    y_axis_zoom: true
    label_value_format: ''
    defaults_version: 1
    listen:
      Segment: orders.segment
      Category: orders.category
      Subcategory: orders.subcategory
    row: 2
    col: 0
    width: 24
    height: 5
  - title: Profit / Sales by State
    name: Profit / Sales by State
    model: superstore_model
    explore: orders
    type: looker_geo_choropleth
    fields: [orders.state, orders.dynamic_profit_or_sales]
    sorts: [orders.dynamic_profit_or_sales desc 0]
    limit: 500
    column_limit: 50
    map: auto
    map_projection: ''
    show_view_names: true
    quantize_colors: false
    map_plot_mode: points
    heatmap_gridlines: false
    heatmap_gridlines_empty: false
    heatmap_opacity: 0.5
    show_region_field: true
    draw_map_labels_above_data: true
    map_tile_provider: light
    map_position: fit_data
    map_pannable: true
    map_zoomable: true
    map_marker_type: circle
    map_marker_icon_name: default
    map_marker_radius_mode: proportional_value
    map_marker_units: meters
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: fixed
    show_legend: true
    quantize_map_value_colors: false
    reverse_map_value_colors: false
    hidden_fields: []
    hidden_points_if_no: []
    series_labels: {}
    defaults_version: 1
    map_scale_indicator: 'off'
    listen:
      Period: orders.order_month
      Profit or Sales: orders.profit_or_sales
      Segment: orders.segment
      Category: orders.category
      Subcategory: orders.subcategory
    row: 7
    col: 8
    width: 8
    height: 6
  - title: Profit / Sales by Region
    name: Profit / Sales by Region
    model: superstore_model
    explore: orders
    type: looker_column
    fields: [orders.region, orders.dynamic_profit_or_sales]
    filters: {}
    sorts: [orders.region]
    limit: 500
    column_limit: 50
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: false
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    show_value_labels: true
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    y_axes: [{label: '', orientation: left, series: [{axisId: orders.dynamic_profit_or_sales,
            id: orders.dynamic_profit_or_sales, name: Dynamic Profit or Sales}], showLabels: false,
        showValues: true, unpinAxis: false, tickDensity: default, tickDensityCustom: 5,
        type: linear}]
    x_axis_zoom: true
    y_axis_zoom: true
    hide_legend: false
    label_value_format: ''
    defaults_version: 1
    listen:
      Period: orders.order_month
      Profit or Sales: orders.profit_or_sales
      Segment: orders.segment
      Category: orders.category
      Subcategory: orders.subcategory
    row: 7
    col: 0
    width: 8
    height: 6
  - title: Number of Orders by Manager
    name: Number of Orders by Manager
    model: superstore_model
    explore: orders
    type: looker_bar
    fields: [sales_managers.person, orders.total_orders]
    sorts: [orders.total_orders desc 0]
    limit: 500
    column_limit: 50
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: false
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    show_value_labels: true
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    y_axes: [{label: '', orientation: bottom, series: [{axisId: orders.total_orders,
            id: orders.total_orders, name: Total Orders}], showLabels: false, showValues: false,
        unpinAxis: false, tickDensity: default, tickDensityCustom: 5, type: linear}]
    x_axis_zoom: true
    y_axis_zoom: true
    series_labels: {}
    defaults_version: 1
    listen:
      Period: orders.order_month
      Segment: orders.segment
      Category: orders.category
      Subcategory: orders.subcategory
    row: 7
    col: 16
    width: 8
    height: 6
  filters:
  - name: Period
    title: Period
    type: field_filter
    default_value: 2019-01
    allow_multiple_values: false
    required: true
    ui_config:
      type: advanced
      display: popover
      options: []
    model: superstore_model
    explore: orders
    listens_to_filters: []
    field: orders.order_month
  - name: Profit or Sales
    title: Profit or Sales
    type: field_filter
    default_value: Profit
    allow_multiple_values: true
    required: false
    ui_config:
      type: button_toggles
      display: inline
    model: superstore_model
    explore: orders
    listens_to_filters: []
    field: orders.profit_or_sales
  - name: Segment
    title: Segment
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: dropdown_menu
      display: inline
    model: superstore_model
    explore: orders
    listens_to_filters: []
    field: orders.segment
  - name: Category
    title: Category
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: dropdown_menu
      display: inline
    model: superstore_model
    explore: orders
    listens_to_filters: []
    field: orders.category
  - name: Subcategory
    title: Subcategory
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: dropdown_menu
      display: popover
    model: superstore_model
    explore: orders
    listens_to_filters: []
    field: orders.subcategory
