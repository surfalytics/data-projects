# How to add or update a project

1. Copy [TEMPLATE.md](TEMPLATE.md) into a new folder as `README.md`.
2. Fill the front matter with the values below. The roadmap in the root [README](README.md) is built from them.
3. Draw the architecture diagram in the style below. Save it in `images/`.
4. Open a pull request. Use the checklist in the PR template.

## Front matter values

Use only these values, so the roadmap and the website can filter projects.

| Field | Values |
|---|---|
| `track` | Fundamentals, BI / Data Analyst, Analytics Engineer, Data Engineer |
| `focus` | Data Engineer only: End-to-end, Ingestion, Processing, Warehouse and lakehouse, Orchestration, Streaming, Data quality, Infrastructure |
| `level` | Base, Middle, Senior |
| `roles` | Data Analyst, BI Developer, Analytics Engineer, Data Engineer, DataOps Engineer |
| `cost` | Free, Free trial, Paid (~$X) |
| `status` | Ready, In progress, Draft |

## Levels

| Level | Who it is for | What the project asks |
|---|---|---|
| Base | You know the fundamentals (CLI, SQL, Git, Docker, Python) | One tool, step by step, mostly local or free |
| Middle | You did Base projects or work in the role | Several tools together, cloud accounts, design choices |
| Senior | You work in the role and want depth | Production concerns: security, networking, scale, operations |

## Diagram style

- Columns from left to right: Sources → Ingestion → Storage → Transform → Serve/BI.
- One gray row at the bottom for DevOps, security and monitoring.
- Colors: orange = sources, purple = ingestion, cyan = storage, green = transform, blue = serve, gray = DevOps.
- Dashed border = optional component.
- Save the source as `images/architecture.excalidraw` and the export as `images/architecture.png`.

## Writing style

- Short sentences. One idea per sentence. Simple words.
- Bullets and tables instead of long paragraphs.
- Many readers have English as a second language.
