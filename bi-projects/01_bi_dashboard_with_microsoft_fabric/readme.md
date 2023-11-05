# Building end-to-end Power BI dashboard with Microsoft Fabric

## Objective

Microsoft Fabric is a new analytics service that combines all Azure analaytics capabilities. We want to create Power BI Dashboard using Microsoft Fabric services. We will use Dataflows Gen2 and Pipelines to ingest data into a Lakehouse and create a dimensional model that will be connected to Power BI. 

## Key terms

**Microfoft Fabric** - is an all-in-one analytics solution for enterprises that covers everything from data movement to data science, Real-Time Analytics, and business intelligence. It offers a comprehensive suite of services, including data lake, data engineering, and data integration, all in one place. In other workds, Microsoft combine all analytics services into single unified interface. It is new offering of Microsoft Azure and should replace Synapse Analytics.

**Lakehouse** -  is a data architecture platform for storing, managing, and analyzing structured and unstructured data in a single location. Initially, this term came from Databricks and Snowflake and means mix of Data Warehouse and Data Lake. 

**Dataflow** - allows you to visually design data transformations and manage data movement at scale using the power of Azure's compute infrastructure.

**Pipeline** - pipeline is a set of data transofmations or other operations and offen know as ETL/ELT job.

**Dimensional Model** - is a data structure technique optimized for data warehousing and business intelligence. It involves the use of "fact" tables containing the measures of business processes, and "dimension" tables containing the context (who, what, where, when, why, and how) for the facts, making data easier to understand and use. This model is particularly efficient for querying large data sets. 

**Power BI** - it is a BI tool from Microsoft. You can learn more about it in the [official documentation](https://learn.microsoft.com/en-us/power-bi/fundamentals/power-bi-overview).

## Prerequisites

1. Azure Subscription. You can start from a [Free](https://azure.microsoft.com/en-us/free/)[ Trial](https://azure.microsoft.com/en-us/free/).
2. Basic knowledge of Cloud Computing and Microsoft Azure. You can check these trainings:
   2.1 [Introduction to Microsoft Azure Cloud Services](https://www.coursera.org/learn/microsoft-azure-cloud-services)
   2.2 [Microsoft Azure Management Tools and Security Solutions](https://www.coursera.org/learn/microsoft-azure-services-lifecycles)
   2.3 [Microsoft Azure Services and Lifecycles](https://www.coursera.org/learn/microsoft-azure-services-lifecycles)
3. SQL and Power BI
4. Traditional Azure Data Factory

Even if something not yet clear, we will cover these topics.


## Implementation

We will run this tutorial [Fabric for Power BI users](https://learn.microsoft.com/en-us/power-bi/fundamentals/fabric-get-started)

## Materials

1. [Get started with Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-getting-started)
2. [Get started creating in the Power BI service](https://learn.microsoft.com/en-us/power-bi/fundamentals/service-get-started)
3. [Azure Data Factory tutorials](https://learn.microsoft.com/en-us/azure/data-factory/data-factory-tutorials#copy-and-ingest-data)
