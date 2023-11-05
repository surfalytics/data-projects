# Deploying Azure Databricks in a Virtual Network with No Public IP

## Objective

Deploy new Azure Databrick Workspace in VNET with NPIP feature and configure the access to the Workspace to be able to access it. The next step is to create new Notebooks and read CSV files in Azure Storage Account. By default Workspace will be blocked from the internet.

## Key Terms

**Azure Databricks** -  is a cloud-based analytics platform optimized for the Microsoft Azure cloud services platform. It provides a collaborative environment for data science, data engineering, and business analytics, leveraging the Apache Spark big data framework at its core.  You can find it on AWS and GPC as well. Usually, organisations use Databricks for their primary data platform also known as lake house. One of the most common is Delta Lake ( we will build Delta Lake for one of the projects).

**Databricks Control Plane** -  is the management layer that handles the configuration of workspaces, users, and permissions, and is managed by Databricks. 

**Databricks Data Plane** - is where data processing tasks occur, running on Databricks clusters within the user's Azure subscription to perform computations and data analytics.

**Workspace** - is a collaborative environment where data professionals can work together on various aspects of big data and machine learning projects. It serves as an organizational unit and a web application that allows users to manage their Databricks assets. 

**Databricks Runtime** - is a set of core components that run on clusters to provide optimized execution for various workloads on Databricks platforms. It includes an optimized version of Apache Spark, along with additional enhancements and improvements for performance, security, and functionality, such as optimized I/O for cloud storage systems, and data science libraries. It is designed to be scalable, reliable, and efficient, allowing data engineers and scientists to run big data analytics and machine learning workloads effectively.

**Databrikcs Scope** - scope is a feature used in Databricks Secrets, which allows you to store and access sensitive information such as API keys, database connection strings, and credentials securely.

**VNET** - Azure Virtual Network (VNet) is a service that enables Azure resources, like virtual machines (VMs), to securely communicate with each other, the internet, and on-premises networks. It provides a private, isolated network space within the Azure cloud where you can configure IP addresses, subnets, route tables, and network gateways.

**Public Subnet** - typically contains resources with public IP addresses and is accessible from the internet.

**Private Subnet** - a private subnet hosts resources with private IP addresses, intended for internal network traffic, and is not directly accessible from the internet without specific routing or forwarding rules.

**Azure Storage** - An Azure Storage account is a secure and scalable cloud storage solution provided by Microsoft Azure, used for various data objects including blobs, files, queues, tables, and disks. It offers a unique namespace to store and access your Azure Storage data across the globe. For analytics purposes, we usually use Azure Data Lake Gen2.

**UDR** - Azure User-Defined Routes (UDR) allow for the customization of network traffic routing for Azure Virtual Networks (VNets). By creating UDRs, you can direct network traffic from a subnet to a virtual appliance, VPN gateway, Azure firewall, internet, or other specific endpoints, overriding Azure's default system routes.

**Network Security Rule**s - control the inbound and outbound network traffic to network interfaces (NICs), VMs, and subnets. These rules define how traffic is allowed or denied by source and destination IP address, port, and protocol, thereby providing a filtering mechanism to ensure secure network connectivity.

**Secure cluster connectivity (No Public IP / NPIP)** - With secure cluster connectivity enabled, customer virtual networks have no open ports, and Databricks Runtime cluster nodes in the classic compute plane have no public IP addresses. Secure cluster connectivity is also known as No Public IP (NPIP).

**Data exfiltration** occurs when malware and/or a malicious actor carries out an unauthorized data transfer from a computer. It is also commonly called data extrusion or data exportation. Data exfiltration is also considered a form of data theft.

**Azure Service **Principal** - The service principal is an identity created for use with applications, hosted services, and automated tools to access Azure resources. This identity allows the service to authenticate with Azure AD and gain access to specific resources by assigned roles, thereby enabling controlled, programmatic access in a secure manner.

## Prerequisites

1. Azure Subscription. You can start from a [Free](https://azure.microsoft.com/en-us/free/)[ Trial](https://azure.microsoft.com/en-us/free/).
2. Basic knowledge of Cloud Computing and Microsoft Azure. You can check these trainings:
   2.1 [Introduction to Microsoft Azure Cloud Services](https://www.coursera.org/learn/microsoft-azure-cloud-services)
   2.2 [Microsoft Azure Management Tools and Security Solutions](https://www.coursera.org/learn/microsoft-azure-services-lifecycles)
   2.3 [Microsoft Azure Services and Lifecycles](https://www.coursera.org/learn/microsoft-azure-services-lifecycles)

## Implementation

After we start our Azure Subscription we will login to Azure Portal and will create the resources.

1. Create a new Azure Databricks Workspaces with VNET and NPIP (SCC) features - [link](https://learn.microsoft.com/en-us/azure/databricks/administration-guide/cloud-configurations/azure/vnet-inject) to documentation](https://learn.microsoft.com/en-us/azure/databricks/administration-guide/cloud-configurations/azure/vnet-inject). You don't need to spend much time now on configuring the security and network, just create new workspace with VNET/NPIP.
2. Create Azure Service Principal and use it for granting access between Azure Databricks and Azure Storage Account. 
3. Create the Azure Storage account and upload any kind of CSV, TXT, or JSON file, we would need this for querying. - [lint to documentation](https://learn.microsoft.com/en-us/azure/databricks/storage/azure-storage). It has many methods and we would like to use Azure Service Principal.
4. Create Azure Key Vault Secret and store Service Principal Secret - [link to documentation](https://learn.microsoft.com/en-us/azure/key-vault/general/quick-create-portal). The goal to create Databricks Scope and use it as an entry point to Azure Key Vault Secrets - - [link to documentation](https://learn.microsoft.com/en-us/azure/databricks/security/secrets/secret-scopes)

Right now we created independent Azure resources and they probably won't work with each other. Moreover, your Databricks workspace is in the private subnet. Our goal is to apply the configuration to be able to access Databricks Workspace and let Databricks Workspace access Azure Storage and Azure Key Vault. 

Materials:
- [Network access](https://learn.microsoft.com/en-us/azure/databricks/security/network/)
- [Manage virtual networks](https://learn.microsoft.com/en-us/azure/databricks/security/network/manage-vpcs)
- [Deploy Azure Databricks in your Azure virtual network (VNet injection)](https://learn.microsoft.com/en-us/azure/databricks/administration-guide/cloud-configurations/azure/vnet-inject)
- [Secure cluster connectivity (No Public IP / NPIP)](https://learn.microsoft.com/en-us/azure/databricks/security/network/secure-cluster-connectivity)

All discussions and weekly meetings will be in the Discord channel - **data-engineering-projects**.





