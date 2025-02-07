model(
    name sqlmesh_example.full_model,
    kind full,
    cron '@daily',
    grain item_id,
    audits(assert_positive_order_ids)
)
;

select item_id, count(distinct id) as num_orders, 1 as one
from sqlmesh_example.incremental_model
group by item_id
