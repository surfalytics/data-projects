model(
    name sqlmesh_example.seed_model,
    kind seed(path '../seeds/seed_data.csv'),
    columns(id integer, item_id integer, event_date date),
    grain(id, event_date)
)
;
