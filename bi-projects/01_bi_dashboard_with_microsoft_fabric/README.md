---
title: "End-to-End Power BI Dashboard with Microsoft Fabric"
track: "BI / Data Analyst"
level: "Base"
roles: ["BI Developer", "Data Analyst"]
duration: "4 assignments, ~1-3 hours each"
cost: "Free trial"
tools: ["Microsoft Fabric", "Lakehouse", "Dataflow Gen2", "Pipeline", "Power BI"]
status: "Ready"
---

# End-to-End Power BI Dashboard with Microsoft Fabric

![Architecture](images/architecture.png)

## Project card

| Level | Roles | Duration | Cost | Status |
|---|---|---|---|---|
| Base | BI Developer, Data Analyst | 4 assignments, ~1-3 h each | Free trial | Ready |

## Goal

You build a sales report for the Contoso sample company in Microsoft Fabric. Dataflow Gen2 loads the data into a Lakehouse. A pipeline refreshes the data every day and sends an email if it fails. A Direct Lake semantic model with a star schema feeds a Power BI report.

## What you will learn

- Set up a Fabric trial, a workspace and a Lakehouse.
- Ingest and transform data with Dataflow Gen2 (Power Query Online).
- Use the **Replace** and **Append** update methods for Lakehouse tables.
- Orchestrate a refresh with a pipeline: schedule and email on failure.
- Build a Direct Lake semantic model: star schema relationships and a DAX measure.
- Build a Power BI report on top of the semantic model.

## Who it is for

- **BI Developer**: build the full path from raw data to a Power BI report in one tool.
- **Data Analyst**: learn how data gets into Power BI, not only how to chart it.

## Tools and services

| Tool | Used for | Free option |
|---|---|---|
| Microsoft Fabric | All-in-one analytics platform | trial (60 days) |
| Lakehouse | Store tables (Delta format in OneLake) | trial |
| Dataflow Gen2 | Low-code ingest and transform (Power Query) | trial |
| Pipeline | Run the dataflow on a schedule, send an email on failure | trial |
| Office 365 Outlook activity | Send the failure email from the pipeline | trial (needs a Microsoft 365 mailbox) |
| Semantic model (Direct Lake) | Star schema and measures for Power BI | trial |
| Power BI | Report | trial |

Key terms:

- **Microsoft Fabric:** an all-in-one analytics platform. It covers data movement, data engineering, data science, real-time analytics and BI in one interface. [Overview](https://learn.microsoft.com/en-us/fabric/fundamentals/microsoft-fabric-overview).
- **Lakehouse:** one place to store and analyze structured and unstructured data. It mixes a data warehouse and a data lake.
- **Dataflow Gen2:** a visual tool (Power Query Online) to get data, transform it and write it to a destination.
- **Pipeline:** a set of activities that run in order, for example "run the dataflow, then send an email". The Fabric item is called **Pipeline**. Some older docs call it **Data pipeline**.
- **Semantic model:** a layer on top of tables with relationships and measures. Power BI reports read from it. In **Direct Lake** mode it reads the Lakehouse tables directly, with no import.
- **Dimensional model:** "fact" tables hold the measures of a business process. "Dimension" tables hold the context (who, what, where, when). A star schema has one fact table in the middle and dimensions around it.
- **Power BI:** the BI tool from Microsoft. [Overview](https://learn.microsoft.com/en-us/power-bi/fundamentals/power-bi-overview).

## Architecture

The diagram is at the top of this page. Source file: [`images/architecture.excalidraw`](images/architecture.excalidraw). Open it at [excalidraw.com](https://excalidraw.com) to copy or edit it.

Data flow:

1. Contoso sample files (CSV and Parquet) are on GitHub. A Power Query template (`ContosoSales.pqt`) has the queries.
2. Dataflow Gen2 `OnlineSalesDataflow` reads the files and writes 6 tables to the Lakehouse `SalesLakehouse`.
3. Pipeline `SalesPipeline` runs the dataflow every day. If the dataflow fails, it sends an Outlook email.
4. Semantic model `SalesModel` reads the Lakehouse tables in Direct Lake mode. It has a star schema and a DAX measure.
5. A Power BI report reads the semantic model.

## Dataset

- **Source:** Contoso sample data from the Microsoft [pbiworkshops](https://github.com/microsoft/pbiworkshops) GitHub repo. You load it with the Power Query template [`ContosoSales.pqt`](https://github.com/microsoft/pbiworkshops/raw/main/_Asset%20Library/Source_Files/ContosoSales.pqt).
- **Tables / entities:**

| Table | Type | Key columns |
|---|---|---|
| `FactOnlineSales` | Fact | `DateKey`, `CustomerKey`, `ProductKey`, `StoreKey`, `SalesAmount`, `SalesQuantity` |
| `DimDate` | Dimension | `DateKey` |
| `DimCustomer` | Dimension | `CustomerKey` |
| `DimProduct` | Dimension | `ProductKey` |
| `DimStore` | Dimension | `StoreKey` |
| `DimEmployee` | Dimension | `EmployeeKey`, `StoreKey` |

- **Size:** dimensions are small CSV files (up to 3 MB each). `FactOnlineSales` comes from several Parquet files, about 7.5 MB each.

## Prerequisites

- A Microsoft Fabric trial. It is free for 60 days. Start it from [app.fabric.microsoft.com](https://app.fabric.microsoft.com) (Account manager → **Start trial**). See [Fabric trial](https://learn.microsoft.com/en-us/fabric/fundamentals/fabric-trial).
- A work or school email account. Gmail, Hotmail and other personal emails do not work. No work email? A Microsoft 365 trial creates one (`onmicrosoft.com`). It needs a credit card, so cancel it before 30 days. See [Sign up for Power BI as an individual](https://learn.microsoft.com/en-us/power-bi/fundamentals/service-self-service-signup-purchase-for-power-bi).
- Your tenant admin must allow Fabric and trials. If you do not see **Start trial**, ask your admin.
- For the failure email: a Microsoft 365 mailbox for your account (the Office 365 Outlook activity uses it).
- [Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-getting-started) (Windows only). Optional, the web editor is enough for this project.
- Basic SQL and Power BI.
- Basic cloud and Azure knowledge helps. These courses help:
  - [Microsoft Azure: Explore Core Cloud Services](https://www.coursera.org/learn/microsoft-azure-cloud-services) (Coursera)
  - [Course AZ-900T00: Introduction to Cloud Infrastructure](https://learn.microsoft.com/en-us/training/courses/az-900t00) (Microsoft Learn)
- Basic Azure Data Factory is useful. Fabric pipelines work in a similar way.
- New to Git, CLI or Docker? Start with [Surfalytics Module 0](https://www.youtube.com/watch?v=LJIiCLu2gr8&list=PLNCDg7zJiXhP5Z_-TXUdorz2n7sjYHHKE&index=1).

Not everything is clear yet? That is fine. We cover these topics in the project.

## Assignments

Work at your own pace. Each assignment shows the expected time. Assignments 1-4 follow the official tutorial [Build Power BI reports in Microsoft Fabric](https://learn.microsoft.com/en-us/power-bi/fundamentals/fabric-get-started). Open it next to this page. It has screenshots for every step.

### Assignment 1: Set up Fabric and the Lakehouse (~1 h)

**Goal:** Get a trial workspace with an empty Lakehouse.

**Steps:**

1. Sign in to [app.fabric.microsoft.com](https://app.fabric.microsoft.com) with your work or school account.
2. Open the Account manager (your photo, top right). Select **Start trial**. Pick a region and select **Activate**.
3. Create a new workspace, for example `fabric-bi-project`. In **Workspace settings → Workspace type**, select **Fabric Trial**.
4. In the workspace, select **New item → Lakehouse**. Name it `SalesLakehouse` (letters, numbers and underscores only). Select **Create**.
5. Download the Power Query template [`ContosoSales.pqt`](https://github.com/microsoft/pbiworkshops/raw/main/_Asset%20Library/Source_Files/ContosoSales.pqt) to your computer.

**Deliverable:** Screenshot of the workspace with `SalesLakehouse`.

**Done when:**

- [ ] The workspace type is **Fabric Trial**.
- [ ] `SalesLakehouse` exists in the workspace.
- [ ] `ContosoSales.pqt` is on your computer.

**Hints:** To check days left in the trial, open the Account manager and look at **Trial status**.

### Assignment 2: Load data with Dataflow Gen2 (~2 h)

**Goal:** Load 6 Contoso tables into the Lakehouse.

**Steps:**

1. Open `SalesLakehouse`. On the ribbon, select **New Dataflow Gen2** (or **Get data → New Dataflow Gen2**). Name it `OnlineSalesDataflow`.
2. In Power Query Online, select **Import from a Power Query template**. Choose `ContosoSales.pqt`.
3. Select the `DimDate` query (group **Data load**). If asked, select **Configure connection**, set authentication to **Anonymous** and select **Connect**.
4. In `DimDate`, change the `DateKey` column type to **Date/Time**. In the **Change column type** window, select **Replace current**.
5. Check the data destination of `DimDate` (bottom right). It is `SalesLakehouse` with update method **Replace**.
6. Select `FactOnlineSales`. Remove its data destination (the **X** icon). Do not remove destinations of other tables.
7. With `FactOnlineSales` selected, select **+ → Lakehouse**. If asked, use **Organizational account**. Pick `SalesLakehouse`, keep **New table**, select **Next**.
8. Clear **Use automatic settings**. Set **Update method** to **Append**. Select **Save settings**.
9. On the **Home** tab, select **Save & run**. Close the editor with the **X** next to `OnlineSalesDataflow` on the left rail.

**Deliverable:** Screenshot of the 6 tables in `SalesLakehouse` and a short note: what is the difference between **Replace** and **Append**?

**Done when:**

- [ ] The dataflow run succeeded.
- [ ] `SalesLakehouse` has 6 tables: `DimCustomer`, `DimDate`, `DimEmployee`, `DimProduct`, `DimStore`, `FactOnlineSales`.
- [ ] `FactOnlineSales` uses **Append**. The other tables use **Replace**.

**Hints:**

- **Replace** overwrites the table on every refresh. **Append** adds new rows and keeps old rows.
- The sample files do not change. So every run appends the same fact rows again. Check the `FactOnlineSales` row count after each run (SQL analytics endpoint: `SELECT COUNT(*) FROM FactOnlineSales`). In a real project, append only new rows.
- [Dataflow Gen2 quickstart](https://learn.microsoft.com/en-us/fabric/data-factory/create-first-dataflow-gen2).

### Assignment 3: Orchestrate with a pipeline (~1-2 h)

**Goal:** Run the dataflow every day and send an email if it fails.

**Steps:**

1. In the workspace, select **New item → Pipeline** (older docs call it **Data pipeline**). Name it `SalesPipeline`.
2. Select **Pipeline activity → Dataflow**. In **General**, name it `OnlineSalesActivity`. In **Settings**, pick `OnlineSalesDataflow`.
3. On the **Activities** tab, add an **Office365 Outlook** activity. If asked to grant consent, select **OK** and sign in. Name it `Mail on failure`.
4. In its **Settings**, set **To** to your email and **Subject** to `Pipeline failure`. For **Body**, select **View in expression builder** and paste:

   ```text
   @concat(
       'Pipeline: '
       , pipeline().PipelineId
       , '<br>'
       , 'Workspace: '
       , pipeline().WorkspaceId
       , '<br>'
       , 'Time: '
       , utcnow()
   )
   ```

5. Drag the **On fail** handle ("X") of `OnlineSalesActivity` to `Mail on failure`.
6. On the **Home** tab, select **Schedule**. Set **Scheduled run** = On, **Repeat** = Daily, **Time** = 12:00:00 AM. Select **Apply**.
7. Select **Run** (then **Save and run**). Watch the **Output** tab until the status is **Succeeded**.

**Deliverable:** Screenshot of the pipeline canvas and a successful run in the **Output** tab.

**Done when:**

- [ ] The pipeline run status is **Succeeded**.
- [ ] `Mail on failure` runs only on failure of `OnlineSalesActivity`.
- [ ] A daily schedule is on.

**Hints:** Turn off the schedule when you finish the project. Each run appends the fact rows again, so the table grows every day.

### Assignment 4: Semantic model and Power BI report (~3 h)

**Goal:** Build a star schema semantic model and a report on it.

**Steps:**

1. Open `SalesLakehouse`. On the **Home** tab, select **New semantic model**. Name it `SalesModel`.
2. Expand **dbo → Tables**. Select `DimCustomer`, `DimDate`, `DimEmployee`, `DimProduct`, `DimStore`, `FactOnlineSales`. Select **Confirm**.
3. Create relationships (drag a column onto the other column):

   | From | To | Cross filter |
   |---|---|---|
   | `FactOnlineSales[CustomerKey]` | `DimCustomer[CustomerKey]` | Single |
   | `FactOnlineSales[ProductKey]` | `DimProduct[ProductKey]` | Single |
   | `FactOnlineSales[StoreKey]` | `DimStore[StoreKey]` | Single |
   | `FactOnlineSales[DateKey]` | `DimDate[DateKey]` | Single |
   | `DimStore[StoreKey]` | `DimEmployee[StoreKey]` | Both |

   All relationships are active and `Many to one (*:1)`, as in the tutorial. For the last row, think: one store has many employees. Which table is the "many" side? Write your answer in the deliverable.

4. Select `FactOnlineSales` → **New measure**. Enter `Total Sales Amount = SUM(FactOnlineSales[SalesAmount])` and commit with the check mark.
5. Go back to the workspace. On `SalesModel`, select **... → Auto-create report**. Select **Save**.
6. Select **Edit** and build your own page. Answer 3 business questions, for example:
   - Total sales amount (card).
   - Sales by month (line chart, `DimDate`).
   - Sales by product category or store (bar chart).
7. Add a slicer (for example, year). Save the report.

**Deliverable:** Screenshot of the model view (star schema) and of the report.

**Done when:**

- [ ] The model has 5 active relationships, with `FactOnlineSales` in the middle.
- [ ] The measure `Total Sales Amount` works.
- [ ] The report answers at least 3 business questions.
- [ ] The slicer filters all visuals.

**Hints:** [Direct Lake overview](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview), [Star schema guidance](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema), [Get started creating in the Power BI service](https://learn.microsoft.com/en-us/power-bi/fundamentals/service-get-started).

## Final result

- A Fabric workspace with a Lakehouse, a Dataflow Gen2, a pipeline, a semantic model and a report.
- Put screenshots and a short write-up in a GitHub repo. Post the report screenshot on LinkedIn.
- Interview pitch: "I built an end-to-end BI solution in Microsoft Fabric. Dataflow Gen2 loads Contoso data into a Lakehouse, and a pipeline refreshes it daily and emails me on failure. A Direct Lake semantic model with a star schema feeds a Power BI report."

## Clean up

- Turn off the pipeline schedule first.
- Delete the workspace: **Workspace settings → Other → Remove this workspace**. This deletes all items in it.
- The Fabric trial ends after 60 days. You do not pay for it. You can also cancel it early: Account manager → **Cancel trial**.
- After the trial ends, Fabric items (Lakehouse, dataflow, pipeline) stop working. They can be deleted after 7 days.
- If you started a Microsoft 365 trial for a work email, cancel it before 30 days. It has your credit card.

## Resources

- [Tutorial: Build Power BI reports in Microsoft Fabric](https://learn.microsoft.com/en-us/power-bi/fundamentals/fabric-get-started): the main tutorial for this project (updated June 2026).
- [Fabric trial capacity](https://learn.microsoft.com/en-us/fabric/fundamentals/fabric-trial): trial length (60 days), what is included, how to cancel.
- [Sign up for Power BI as an individual](https://learn.microsoft.com/en-us/power-bi/fundamentals/service-self-service-signup-purchase-for-power-bi): work or school email rule, Microsoft 365 trial option.
- [Create your first pipeline](https://learn.microsoft.com/en-us/fabric/data-factory/create-first-pipeline-with-sample-data): the current **Pipeline** item name and run history.
- [Workspaces in Fabric](https://learn.microsoft.com/en-us/fabric/fundamentals/workspaces): workspace settings and how to remove a workspace.
- [Get started with Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-getting-started): build reports on your computer.
- [Azure Data Factory tutorials](https://learn.microsoft.com/en-us/azure/data-factory/data-factory-tutorials#copy-and-ingest-data): pipelines in the classic Azure service.

## Community solutions

Share your repo in Discord. We add the best ones here.
