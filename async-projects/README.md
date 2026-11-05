# Surfalytics Async Projects

Self-paced, hands-on data projects. Every project uses the same structure:

- Project card: level, roles, duration, cost, status.
- Goal and what you will learn.
- Tools table and architecture diagram (Excalidraw).
- Assignments with Goal, Steps, Deliverable and "Done when" checklist.
- Final result, clean up and community solutions.

Want to add a project? Copy [TEMPLATE.md](TEMPLATE.md).

## Catalog

| # | Project | Category | Level | Roles | Duration | Cost | Status |
|---|---|---|---|---|---|---|---|
| 01 | [End-to-end Analytics with dbt and Looker](01-end-to-end-analytics-with-dbt-and-looker/) | Analytics Engineering | Intermediate | Analytics Engineer, Data Engineer, BI Developer | 8 assignments | Free | Ready |
| 02 | [BI Admin with Tableau Server](02-BI-admin-with-Tableau/) | BI | Intermediate | Data Analyst, BI Developer | 4 assignments | Free trial | Ready |
| 03 | [Open Source BI with Metabase](03-Open-Source-BI-with-Metabase/) | BI | Beginner | Data Analyst, BI Developer | 4 assignments | Free | In progress |
| 04 | [Typical Data Warehouse on Azure](04-azure-data-warehouse/) | Data Engineering | Intermediate | Data Engineer, Analytics Engineer | 4 assignments | Free trial | Ready |
| 05 | [Getting Started with Databricks](05-getting-started-with-databricks/) | Data Engineering | Beginner | Data Engineer, Analytics Engineer | 4 assignments | Free | In progress |
| 06 | [Data Ingestion Patterns: From API to Snowflake](06-data-ingestion-patterns/) | Data Engineering | Intermediate | Data Engineer, Analytics Engineer | 6 assignments | Free trial | Ready |
| 07 | [Data Streaming Mastery](07-data-streaming-mastery/) | Streaming | Intermediate | Data Engineer, DataOps Engineer | 10 assignments | Free | Ready |

## Fixed values

Use only these values in the front matter, so the website can filter projects.

| Field | Values |
|---|---|
| `category` | BI, Analytics Engineering, Data Engineering, Streaming, DataOps |
| `level` | Beginner, Intermediate, Advanced |
| `roles` | Data Analyst, BI Developer, Analytics Engineer, Data Engineer, DataOps Engineer |
| `cost` | Free, Free trial, Paid (~$X) |
| `status` | Ready, In progress, Draft |

## Diagram style

- Columns from left to right: Sources → Ingestion → Storage → Transform → Serve/BI.
- One gray row at the bottom for DevOps, security and monitoring.
- Colors: orange = sources, purple = ingestion, cyan = storage, green = transform, blue = serve, gray = DevOps.
- Dashed border = optional component.
- Save the source as `images/architecture.excalidraw` and the export as `images/architecture.png`.
