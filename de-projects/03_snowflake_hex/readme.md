# Inroduction to modern data tools: Snowflake Data Warehouse and Hex Notebook

## Objective

* To provide participants with a comprehensive understanding of Snowflake Data Warehouse and Hex Notebook.
* To equip participants with practical skills in implementing data projects using Snowflake and Hex.
* To enable participants to apply these tools in real-world data analysis scenarios.

## Key Terms

**Snowflake Data Warehouse**: Snowflake Data Warehouse is a cloud-based platform that offers a comprehensive suite of features for data warehousing, data lakes, data engineering, data science, and data application development. It is designed for secure sharing and consumption of shared data. Its unique architecture supports various data workloads and enables scalable, flexible, and efficient data storage and analysis.

**SnowCLI**: SnowCLI is a Command Line Interface tool specifically designed for managing Snowflake. It provides a convenient way for users to interact with Snowflake, perform administrative tasks, manage data, execute queries, and automate workflows directly from the command line.

**SnowSQL**: SnowSQL is a specialized SQL client for Snowflake. It allows users to execute SQL queries against Snowflake data warehouses, manage database objects, and perform various database operations. SnowSQL is designed to leverage Snowflake's capabilities, providing a seamless and optimized experience for running SQL commands.

**Snowpipe**: Snowpipe is a tool for continuous, automated data ingestion into Snowflake. It enables real-time data loading, allowing users to automatically import data into Snowflake as soon as it becomes available. Snowpipe is essential for scenarios requiring up-to-date data, such as real-time analytics and data streaming.

**Time Travel**: Time Travel is a unique feature of Snowflake that allows users to access historical data within a defined period. This feature enables users to query past states of data or restore data from a specific point in time, providing significant benefits for data recovery, auditing, and analysis.

**Snowflake Architecture**: The Snowflake Architecture is characterized by its multi-cluster, shared data architecture. This innovative design separates compute and storage resources, allowing Snowflake to offer high performance, scalability, and concurrency. It enables users to run multiple workloads without performance degradation and manage data efficiently across the organization.

**Hex Notebook (www.hex.tech)**: Hex Notebook is a modern data workspace that integrates notebooks, SQL, and visualizations. It is designed for collaborative data analysis and project development, offering a user-friendly interface for writing code, executing SQL queries, and creating interactive data visualizations. Hex Notebook facilitates teamwork and streamlines the data analysis process, making it ideal for data scientists, analysts, and engineers.

## Prerequisites



## Implementation

After we start our Azure Subscription we will login to Azure Portal and will create the resources.

1. Create a new Azure Databricks Workspaces with VNET and NPIP (SCC) features - [link](https://learn.microsoft.com/en-us/azure/databricks/administration-guide/cloud-configurations/azure/vnet-inject) to documentation](https://learn.microsoft.com/en-us/azure/databricks/administration-guide/cloud-configurations/azure/vnet-inject). You don't need to spend much time now on configuring the security and network, just create new workspace with VNET/NPIP.
2. Create Azure Service Principal and use it for granting access between Azure Databricks and Azure Storage Account. 
3. Create the Azure Storage account and upload any kind of CSV, TXT, or JSON file, we would need this for querying. - [lint to documentation](https://learn.microsoft.com/en-us/azure/databricks/storage/azure-storage). It has many methods and we would like to use Azure Service Principal.
4. Create Azure Key Vault Secret and store Service Principal Secret - [link to documentation](https://learn.microsoft.com/en-us/azure/key-vault/general/quick-create-portal). The goal to create Databricks Scope and use it as an entry point to Azure Key Vault Secrets - - [link to documentation](https://learn.microsoft.com/en-us/azure/databricks/security/secrets/secret-scopes)

Right now we created independent Azure resources and they probably won't work with each other. Moreover, your Databricks workspace is in the private subnet. Our goal is to apply the configuration to be able to access Databricks Workspace and let Databricks Workspace access Azure Storage and Azure Key Vault. 

## Materials:
- [Network access](https://learn.microsoft.com/en-us/azure/databricks/security/network/)
- [Manage virtual networks](https://learn.microsoft.com/en-us/azure/databricks/security/network/manage-vpcs)
- [Deploy Azure Databricks in your Azure virtual network (VNet injection)](https://learn.microsoft.com/en-us/azure/databricks/administration-guide/cloud-configurations/azure/vnet-inject)
- [Secure cluster connectivity (No Public IP / NPIP)](https://learn.microsoft.com/en-us/azure/databricks/security/network/secure-cluster-connectivity)

All discussions and weekly meetings will be in the Discord channel - **data-engineering-projects**.






