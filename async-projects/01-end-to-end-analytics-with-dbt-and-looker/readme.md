# End to end Analytics solution with dbt and looker

Repos of students with example:
- From Aizhan https://github.com/aizhannna/data-projects/tree/main
- 

## Week 1

 Using our popular stack, dbt, Azure Postgres, Looker. 
 
 The first exercise:

1. Create new GitHub repo for this project and add `readme.md` file with information about project in it from local IDE using VScode or similar. Don’t forget to create a branch before creating Pull Request. You can check [Module 0](https://surfalytics.com/surfalytics/2023-06-04-Module00.html) for reference or ask help in Discord in `#ask-anything`.

## Week 2

We will use Superstore dataset. 


During this week we should:
1. add this into Git, folder `data` and inside put a file or files
2. ingest data into Azure Postgres (our Data Warehouse)

How to connect Database? 
1. Open DBeaver: Launch the DBeaver application on your computer.
2. Create a new connection: Click on the "New Database Connection" button in the toolbar at the top left-side or click on the "Database" menu and select "New Database Connection.
3. Select PostgreSQL: In the "Connect to a database" dialog, choose "PostgreSQL" from the list of available databases and click "Next."
4. Configure the connection:
- Host: Ask in Discord!
- Port: 5432
- Database: Ask in Discord!
- Username: Ask in Discord!
- Password: Ask in Discord!
5. By default Azure postgres using TLS/SSL for encryption, we don't need it and we have to disable in Connection Properties

Next step, you have to create a new `DATABASE SURFALYTICS_DW_<YOUR UNIQUE NAME>`
Inside your database `CREATE SCHEMA STG`
And then you need to figure out how to ingest 3 tables
Superstore data set has 3 tabs in Excel, so we want to have 3 tables in `STG` schema `orders`, `returns`, `people`.

Summary:
- Connect with dbeaver
- Create your database and schema
- Load data into 3 tables into stagin, you would need 1st create table using CREATE TABLE ... (it is DDL)
- Document all in markdown (SQL, steps) and commit into PR


## Week 3

1. Setup `dbt core` and create a new project with `dbt init` in the same repository.|
2. Define `source.yml` or `sources.yml` don't remember and specify the source table
3. Create the 1st staging models in `models/stg` folder using that is reading the source table and make `config` in the top of model where you can specify `alias`, `strategy` and maybe something else. In the model (SQL) you can add 2 extra columnas: `dwh_id` - this is the unique column, you can use dbt_utils.surrogate_key macro and then you need add column `etl_timestamp` using the macro or just SQL Server column that represents time now.
3. Define `dev` and `prod` profiles in `profiles.yml` and you should have dev and prod Schema or Database. When you run a `dbt build --select model_name --profile . --target dev` it will create  in your dev schema, and them eith `--prod` it will create in prod schema or database.

As a result you will have dbt project with three model in staging that are represents the tables that you've loaded in Week2. We can actually renames schema in week two in `raw` and week 3 is `stg` and week 4 will be `business` or `dw` or anything. In this case it is true layers of data warehouse also known as medalian architecture - bronze/silver/gold. You can read about it.

## Week 4

You need to add `.pre-commit` to your repo, to check YAML files, trailing whitespace and SQL.

Read about  Medallion Architecture https://i-spark.nl/en/blog/dbt-naming-conventions-and-medallion-architecture/ in context of dbt it is just a folders:
- dbt/models/
  - bronze
  - silver
  - gold

```
Bronze Tier Models: These could include models that extract raw data from source systems, clean it, and prepare it for basic reporting or dashboarding.

Silver Tier Models: Silver tier models might perform more complex aggregations across different datasets, handle historical data transformations, or implement standardized calculations.

Gold Tier Models: Gold tier models could involve building advanced analytics models, predictive models, or generating complex business metrics ready for executive reporting.
```

Currently our model with initial load should be in `dbt/models/bronze/`

Let's try to compare `dbt strategy` and `dbt config` https://docs.getdbt.com/docs/build/incremental-strategy
a) creating view
b) full table reload
c) incremental 

We are using `dbt-postgres` and it supports: `append`, `merge`, `delete+insert` you need to copy same model and try 3 options and document the SQL difference about these 3 appoaches.

We should add GitHub Actions to be able to run `.pre-commit` in CI i.e. when you create a PR, it will test the files.

## Week 5

Hello, week 5 goals:

You should already has a dbt project and it should have several bronze models. 
You should be aware about dbt incremental strategies and medalien architecture (just folders layers/structure)
You should have the basic pre-commit

In week 5 we will continue our dbt journey. 

DBT Specific:
1. For dbt make sure you have DEV and PROD profile and you can run in Dev and in Prod your model
2. We can add the dbt freshness test, it is not super useful for our data but good to know about it https://docs.getdbt.com/reference/resource-properties/freshness
3. We should add more tests to the models we have, there are multiple types of tests https://docs.getdbt.com/docs/build/data-tests make sure you have one of each, you can add different things
4. You can check the verision of your dbt and ugrade to the last one 1.8.x and it let you add brand new feature: https://docs.getdbt.com/docs/build/unit-tests Unit Test - i.e. example of testing on dummy data, please add this as well.
5. Let's focus do some cool things on dbt_project.yml file where we can define our folders and we will use `meta` tags for extra information: https://docs.getdbt.com/reference/resource-configs/meta#assign-owner-and-favorite_color-in-the-dbt_projectyml-as-a-config-property (it could be defined in the model too), this will help for the documentation
6. Let's also add another cool thing like centralized description for the models, using https://docs.getdbt.com/reference/resource-properties/description#use-a-docs-block-in-a-description, it means we will define all definitions in separate place as a YAML files and then reference them in the model
7. We now can build the docs and see the dbt docs site with model(s) description and column defintions and DAG
8. Please make sure it is super clear what is dbt DAG (i.e. dependencies of the models)
9. Let's split the profiles. Curently we have 2 profiles (prod and dev in the same YAML file), now we will ad folders:
- `conf` - prod profile
- `conf_local` - dev profile
It means when you run model `dbt run --select model --profile ./conf/` basically show the path towards the profile folder
10. Review the folder /logs, delete all from it and run the model, see what is inside. Review the folder `target`, it has compile and run subfolders, check their differences.
11. check the commands `dbt run`, `dbt test`, `dbt build`, `dbt compile`.
12. Add a tag and alias for each model inside the model `config` , (alias = friendly name of the table) https://docs.getdbt.com/docs/build/custom-aliases, tag in dbt_project file https://docs.getdbt.com/reference/resource-configs/tags#use-tags-to-run-parts-of-your-project
13. check what is dbt artifacts: https://substack.com/home/post/p-141116365, they are core thing for dbt docs and model docuemntation (like dbt metadata of all you have), review your own.
14. dbt artifacts will allow us to unock knowledge of `deffer` command https://docs.getdbt.com/reference/node-selection/defer in short, when you run model in dev, dbt will lookup the artifacts if the dev representation of upstream tables exists, if not it will place prod table, it means you don't need to have full copy of DEV! super useful!
15. Finally run `dbt doc` and have docs available

As you can see we basically adding some best practices from real world dbt projects.
For CI/CD, lets do the following:
1. For Github we need to add a PR template (ask ChatGPT)
2. Place the .pre-commit into CI/CD, basically run the same file when we open a PR (it calls Continious Integrations). You need to ask chatgpt how to create YAML for github actions based on your pre-commit file and trigger it on PR creation/update.
3. Let's add something from this example to add more cool checking of our `pre-commit` I am sharing my work example in thread.

Pre-commit example:

```
# Pre-commit that runs locally
fail_fast: false

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: check-yaml

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        files: '\.(yaml|yml)$'
  - repo: https://github.com/tconbeer/sqlfmt
    rev: v0.21.2
    hooks:
      - id: sqlfmt
        name: SQL formatter
        language_version: python
        additional_dependencies: [".[jinjafmt]"]

  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 3.7.9
    hooks:
      - id: flake8

  - repo: https://github.com/dbt-checkpoint/dbt-checkpoint
    rev: v1.2.0
    hooks:
      - id: check-model-has-description
      - id: check-model-has-tests-by-group
        args: ["--tests", "not_null", "--test-cnt", "1", "--"]        
      - id: check-model-has-tests-by-group
        args:
          [
            "--tests",
            "unique",
            "unique_combination_of_columns",
            "--test-cnt",
            "1",
            "--",
          ]
      - id: check-macro-has-description
        files: ^(macros/).*$
  - repo: https://github.com/sqlfluff/sqlfluff
    rev: 2.3.5
    hooks:
      - id: sqlfluff-fix
        args: [--config, "./conf_local/.sqlfluff", --show-lint-violations]
        additional_dependencies:
          ["dbt-core==1.7.4", "dbt-snowflake==1.7.1", "sqlfluff-templater-dbt"]
```

> Note: you need to use your dbt versions in pre-commit config.

## Week 6

This week we will continue to work on dbt and GitHub.

1. We would like to add a dbt seed (CSV file) that will create for us a `calendar` table. You can check any kind of CSV file that has calendar. Idea is to learn about [what is seed](https://docs.getdbt.com/docs/build/seeds).
2. We want to add packages to dbt and run `dbt deps` to install them. You have to use https://hub.getdbt.com/ to pick up 1-2 you like and try to reproduct them.
3. For the bronze models we have, we would need to add technical columns such as `unique_key` and `etl_timestamp`. For Unique Key Column you can use `dbt.utils` macro for [Surrogate Key](https://github.com/dbt-labs/dbt-utils?tab=readme-ov-file#generate_surrogate_key-source) and for ETL timestamp you would need something like `current_timestamp()`. This is what we have to add for all models in dbt.
4. For `_unique_key` add at `unique` test in YAML file for models.
5. Let's create a model for our Silver layer (sivler folder), it is basically all the same columns excep we will join calendar table and you can add new tables in the model, for example using `CASE` statement. Also, you can try to `LEFT JOIN` (I hope you understand why it is LEFT join) our tables `people` and `return` if this possible. In other words, we are doing simple joins but not yet any metrics or aggregation. Don't forget `etl_timestamp` and `unique_key` and add tests.
6. We can do the gold layer. You have to create the DIM tables:
- `dim_product` - product information and `product_id` (you may generate `product_id` as a sequence)
- `dim_customer` - customer information and `customer_id` (you may generate ID as a sequence)
- `dim_shipping` - shipping information and `shipping_id` (you may generate ID as a sequence)
- `dim_geo` - geo information and `geo_id` (you may generate ID as a sequence)
7. Finally, we can add a fact table, `fct_sales`. The table will have IDs (as a surrogate keys) and metrics. For example, the column list could be:
  - `product_id`
  - `customer_id`
  - `shipping_id`
  - `geo_id`
  - `date_id` to join calendar
  - `sales_amt`
  - `orders_number`
  - `items_number`
  - and etc. (You can try to use WINDOW functions to calculate more complicated metrics, also you can calcualte `profit`, shipping cost and so on)
 
In other, words in gold layer, we aggregated data down to our dimensions and we keep only IDs and metrics and actual dimension values are in Dimension Tables. 

We just created a Star Schema with 1 fact table and multiple dimension tables around.

8. Let's add more tests for metrics and dimensions and run them:
- sales amount is positive
- product category are in ACCEPTED VALUES list
- and etc, think in "business terms" what tests can gurantee we are providing quality data.

9. Build new `dbt docs` and check the dbt DAG.

Optionally, you can add more than one fact table.

10. Create a data model (Physical and Logics) (star schema) with Dbeaver or Lucid or anything you like. Check the definitions and examples.

11. Make sure you have a great CI with `pre-commit` that checks files and dbt and sql linting. Share PR with the discord and ask for a real Code Review.

## Week 7

By week 7, we should have dbt project in our local IDE and also published in GitHub. The `pre-commit` will make sure code is accurate and running everytime we are creating a commit locally and insied GitHub Actions (Continious Integration). Inside data warehouse we should have DEV and PROD copy of data and models. It means we can do changes safely and test without breaking our production. 

For our local dbt setup, I want to add couple more useful things:
1. Adding nice dbt feature [deffer](https://docs.getdbt.com/reference/node-selection/defer). Example of command run:

```bash
dbt run --target dev --defer --state ./prod_artifacts/ --select fact_mrr_time_series   
```
This command has `--target dev` i.e. will run against DEV, and I want to run fact table. If I have dependenices for this model dbt will look up them and failed, if I don't have table in DEV scehma. `--defer` will help dbt to lookup the PROD tables instead and we don't need to build the whole DEV jsut for us. Save money, storage and time! 

How dbt will know about proper tables names and schemas? Using this part `--state ./prod_artifacts/`. I've created the folder `prod_artifacts` and drop the dbt artfifacts into the folder. I am using these commands:

```bash
dbt docs generate --target prod
rm ./prod_artifacts/catalog.json
rm ./prod_artifacts/manifest.json
mv ./target/catalog.json ./target/manifest.json ./prod_artifacts/
```

You need to understand this powerfull concept.

2. `makefile` to have shortcuts for CLI commands. You can read what is it [here](https://blog.det.life/what-is-a-makefile-and-how-i-use-it-in-a-dbt-project-703b922be2ef).

Example for command above:

```bash
prod-artifacts:
 dbt docs generate --target prod
	rm ./prod_artifacts/catalog.json
	rm ./prod_artifacts/manifest.json
	mv ./target/catalog.json ./target/manifest.json ./prod_artifacts/
```

3. We have to leverage concept of Slowly Change Dimensions. Check this [blog post](https://sarathd.medium.com/slowly-changing-dimensions-using-dbt-snapshots-2a46727f0d39#:~:text=Understanding%20the%20SCD%20Type%202,the%20same%20record%20over%20time.) or similar. Let's focus on Product Dimension. Assume, we want to change the Product name to something else. This is a good question for data professional, how do we want to handle changes?

We can insert new order into source table, something like:

> Please update table, columns and values for the insert, I am using real example. The key change here is product name changes from `Xerox 1999` to `Xerox v2`

```sql
INSERT INTO <YOUR TABLE> (
  Row_ID, Order_ID, Order_Date, Ship_Date, Ship_Mode, Customer_ID, Customer_Name, Segment, Country_Region, City, State, Postal_Code, Region, Product_ID, Category, Sub_Category, Product_Name, Sales, Quantity, Discount, Profit
) VALUES (
  93, 'CA-2019-149587', '2019-01-31', '2019-02-05', 'Second Class', 'KB-16315', 'Karl Braun', 'Consumer', 'United States', 'Minneapolis', 'Minnesota', 55407, 'Central', 'OFF-PA-10003177', 'Office Supplies', 'Paper', 'Xerox 1999', 12.96, 2, 0, 6.2208
);
```

It means, that both `Xerox 1999` and `Xerox v2`. For SCD 1, we would overwrite just in DIM PRODUCTS, but we want SCD 2, you and you need kep both versions with couple extra columns. Depens on sales date, it will be one of them in reporting. 

Update the PRODUCT DIM to make sure it is SCD 2. (PS remember this is one of the most popular interview question!)

Let's think what else missing to make this a production solution?

1. Create a Physical Data model our our Fact and Dim tables. You can use free trial of SQLDBM or you can use Dbeaver to create the [Physical Data model](https://dbeaver.com/docs/dbeaver/Custom-Diagrams/).
2. We should create a BI Dashboard for end users. We can use Power BI, Tableau, Looker. Let's focus on Looker and we will use my [Rock Your Data](https://rockyourdata.looker.com/login) instance. I will share creds in discord. You should leverage this project [Looker Project](https://github.com/surfalytics/data-projects/blob/main/bi-projects/02_looker_snowflake/readme.md). You can check [example of implementation from Maksim](https://medium.com/@kazarmax/creating-a-superstore-kpi-dashboard-using-looker-and-snowflake-73fec857132d).

> Looker can be integrated with your own repo for a project. Everyone should create their own connection to data warehouse (postgres) and then create a new project.

This is the focus for this week.

Next week, we should start think, how to put dbt into container and host somewhere as well as schedule with the GitHub Actons.


