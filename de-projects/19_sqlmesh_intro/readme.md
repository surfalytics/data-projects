# Getting Started with SQL Mesh

SQLMesh is a data transformation framework, just like how dbt is.

## Setup SQLmesh

First, create the virtual environment:

```bash
python3 -m venv .env
```

Then activate it:

```bash
source .env/bin/activate
```

Install

```bash
pip install sqlmesh
```

## Init project

In this example, we specify the duckdb dialect:

```bash
sqlmesh init duckdb
```

SQLMesh project-level configuration parameters are specified in the `config.yaml` file in the project directory.

This example project uses the embedded DuckDB SQL engine, so its configuration specifies duckdb as the local gateway's connection and the local gateway as the default.

The command to run the scaffold generator requires a default SQL dialect for your models, which it places in the config `model_defaults` `dialect` key. In this example, we specified the duckdb SQL dialect as the default:

```yaml
gateways:
  local:
    connection:
      type: duckdb
      database: ./db.db

default_gateway: local

model_defaults:
  dialect: duckdb
```

SQLMesh uses a scaffold generator to initiate a new project. The generator will create multiple sub-directories and files for organizing your SQLMesh project code.

The scaffold generator will create the following configuration file and directories:

- `config.yaml` - The file for project configuration. More info about configuration here.
- `./models` - SQL and Python models. More info about models here.
- `./seeds` - Seed files. More info about seeds here.
- `./audits` - Shared audit files. More info about audits here.
- `./tests` - Unit test files. More info about tests here.
- `./macros` - Macro files. More info about macros here.

It will also create the files needed for this quickstart example:

- `./models`
  - `full_model.sql`
  - `incremental_model.sql`
  - `seed_model.sql`
- `./seeds`
  - `seed_data.csv`
- `./audits`
  - `assert_positive_order_ids.sql`
- `./tests`
  - `test_full_model.yaml`

Finally, the scaffold will include data for the example project to use.

The data used in this example project is contained in the `seed_data.csv` file in the `/seeds` project directory. The data reflects sales of 3 items over 7 days in January 2020.

The file contains three columns, `id`, `item_id`, and `event_date`, which correspond to each row's unique ID, the sold item's ID number, and the date the item was sold, respectively.

| id  | item_id | event_date |
|-----|---------|------------|
| 1   | 2       | 2020-01-01 |
| 2   | 1       | 2020-01-01 |
| 3   | 3       | 2020-01-03 |
| 4   | 1       | 2020-01-04 |
| 5   | 1       | 2020-01-05 |
| 6   | 1       | 2020-01-06 |
| 7   | 1       | 2020-01-07 |

## create prod env

SQLMesh's key actions are creating and applying plans to environments. At this point, the only environment is the empty prod environment.

A **SQLMesh environment** is an isolated namespace containing models and the data they generated. The most important environment is `prod `("production"), which consists of the databases behind the applications your business uses to operate each day. Environments other than prod provide a place where you can test and preview changes to model code before they go live and affect business operations.

A **SQLMesh plan** contains a comparison of one environment to another and the set of changes needed to bring them into alignment. For example, if a new SQL model was added, tested, and run in the dev environment, it would need to be added and run in the prod environment to bring them into alignment. SQLMesh identifies all such changes and classifies them as either breaking or non-breaking.

The first SQLMesh plan must execute every model to populate the production environment. Running `sqlmesh plan` will generate the plan and the following output:

```bash
sqlmesh init duckdb

~/github/data-projects/de-projects/19_sqlmesh_intro main* 20s
.env ❯ sqlmesh plan
======================================================================
Successfully Ran 1 tests against duckdb
----------------------------------------------------------------------
`prod` environment will be initialized

Models:
└── Added:
    ├── sqlmesh_example.full_model
    ├── sqlmesh_example.incremental_model
    └── sqlmesh_example.seed_model
Models needing backfill [missing dates]:
├── sqlmesh_example.full_model: [full refresh]
├── sqlmesh_example.incremental_model: [2020-01-01 - 2025-01-23]
└── sqlmesh_example.seed_model: [full refresh]
Apply - Backfill Tables [y/n]:
```

