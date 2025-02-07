model(
    name sqlmesh_example.incremental_model,
    kind incremental_by_time_range(time_column event_date),
    start '2020-01-01',
    cron '@daily',
    grain(id, event_date)
)
;

select
    id,
    item_id,
    'z' as new_column,  -- Added column
    event_date,
from sqlmesh_example.seed_model
where event_date between @start_date and @end_date
