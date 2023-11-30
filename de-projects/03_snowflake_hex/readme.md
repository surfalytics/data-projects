# Mastering modern data tools: Snowflake DW and Hex Notebook

## Objective

Introduce to the modern data stack, focusing on Snowflake and Hex, by detailing their key features and elements, and to provide practical skills through hands-on experience with a real-world project, enabling to effectively utilize these technologies in data warehousing, analysis, and visualization.

## Key Terms

**Snowflake Data Warehouse**: Snowflake Data Warehouse is a cloud-based platform that offers a comprehensive suite of features for data warehousing, data lakes, data engineering, data science, and data application development. It is designed for secure sharing and consumption of shared data. Its unique architecture supports various data workloads and enables scalable, flexible, and efficient data storage and analysis.

**SnowCLI**: SnowCLI is a Command Line Interface tool specifically designed for managing Snowflake. It provides a convenient way for users to interact with Snowflake, perform administrative tasks, manage data, execute queries, and automate workflows directly from the command line.

**SnowSQL**: SnowSQL is a specialized SQL client for Snowflake. It allows users to execute SQL queries against Snowflake data warehouses, manage database objects, and perform various database operations. SnowSQL is designed to leverage Snowflake's capabilities, providing a seamless and optimized experience for running SQL commands.

**Snowpipe**: Snowpipe is a tool for continuous, automated data ingestion into Snowflake. It enables real-time data loading, allowing users to automatically import data into Snowflake as soon as it becomes available. Snowpipe is essential for scenarios requiring up-to-date data, such as real-time analytics and data streaming.

**Time Travel**: Time Travel is a unique feature of Snowflake that allows users to access historical data within a defined period. This feature enables users to query past states of data or restore data from a specific point in time, providing significant benefits for data recovery, auditing, and analysis.

**Snowflake Architecture**: The Snowflake Architecture is characterized by its multi-cluster, shared data architecture. This innovative design separates compute and storage resources, allowing Snowflake to offer high performance, scalability, and concurrency. It enables users to run multiple workloads without performance degradation and manage data efficiently across the organization.

**Hex Notebook (www.hex.tech)**: Hex Notebook is a modern data workspace that integrates notebooks, Python, SQL, and visualizations. It is designed for collaborative data analysis and project development, offering a user-friendly interface for writing code, executing SQL queries, and creating interactive data visualizations. Hex Notebook facilitates teamwork and streamlines the data analysis process, making it ideal for data scientists, analysts, and engineers.

## Prerequisites

1. Create Snowflake free trial account: https://signup.snowflake.com/
2. Create Hex free trial account: https://app.hex.tech/signup

## Implementation

After we start our Azure Subscription we will login to Azure Portal and will create the resources.

1. Create a new Azure Databricks Workspaces with VNET and NPIP (SCC) features - [link](https://learn.microsoft.com/en-us/azure/databricks/administration-guide/cloud-configurations/azure/vnet-inject) to documentation](https://learn.microsoft.com/en-us/azure/databricks/administration-guide/cloud-configurations/azure/vnet-inject). You don't need to spend much time now on configuring the security and network, just create new workspace with VNET/NPIP.
2. Create Azure Service Principal and use it for granting access between Azure Databricks and Azure Storage Account. 
3. Create the Azure Storage account and upload any kind of CSV, TXT, or JSON file, we would need this for querying. - [lint to documentation](https://learn.microsoft.com/en-us/azure/databricks/storage/azure-storage). It has many methods and we would like to use Azure Service Principal.
4. Create Azure Key Vault Secret and store Service Principal Secret - [link to documentation](https://learn.microsoft.com/en-us/azure/key-vault/general/quick-create-portal). The goal to create Databricks Scope and use it as an entry point to Azure Key Vault Secrets - - [link to documentation](https://learn.microsoft.com/en-us/azure/databricks/security/secrets/secret-scopes)

Right now we created independent Azure resources and they probably won't work with each other. Moreover, your Databricks workspace is in the private subnet. Our goal is to apply the configuration to be able to access Databricks Workspace and let Databricks Workspace access Azure Storage and Azure Key Vault. 

## Materials:
- [Snowflake official guides and documentation](https://docs.snowflake.com/)
- [Hex tutorials](https://learn.hex.tech/tutorials)
- [Full Snowflake Youtube tutorial](https://youtube.com/playlist?list=PLba2xJ7yxHB7SWc4Sm-Sp3uGN74ulI4pS&si=fkLQ9meJ36IwE0gA)
- [Snowflake vs Databricks](https://youtu.be/VLtq0eeHc14?si=JIFmDrN8OQg6Xvm1)


All discussions and weekly meetings are in the Discord channel - **data-engineering-projects**.






