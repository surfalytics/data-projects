### About the project

End-to-end data engineering project that covers data ingesting using Python and open API endpoint, data processing using PySpark, data storing using AWS S3, further data processing using other AWS services and data visualization using Amazon QuickSight.


### Project decomposition

1. You dump data from API to S3 with even Python request library (any open API including Spotify or Github or Linkedin Profile), it will be a JSON(s) - first job
2. Then you parse JSON and normilise it with PySaprk and save in Parquet into the another folder in S3
3. Then you add Athena SQL for querieng the Parquet with Athena SQL with partition projection
4. Then you need Redshift for storing this into Data Warehouse, you will push data into Redshift and here you have nice options:
* Using Redshift Serverless
* Using Redshift Spectrum (similar idea to Athena) and use dbt-external package to create external tables that will push data from S3 to Redshift permament storage
* Using only Redshift
5. Finally, you can connect any BI including AWS QUickSight for dashboard.

This will be Modern aws data analytics solution and you will learn difference with the Athena, Glue, Redshift, Redshift Spectrum, Redshift Serverless and overall Idea Data Lake vs Data Warehouse.

