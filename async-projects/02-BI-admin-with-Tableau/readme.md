
# BI Admin with Tableau Server

During this async project, we want to learn the key capabilities of BI Admin. This role usually assign on Data Analyst or BI Developer and it is great competitive advantage for you to have because all companies have BI servers and usually they don't have any dedicated BI Admin roles.

In the past the free Tableau courses in Coursera give a license. You can check them:

- [Data Visualization and Communication with Tableau](https://www.coursera.org/learn/analytics-tableau)
- [Fundamentals of Visualization with Tableau](https://www.coursera.org/learn/data-visualization-tableau?specialization=data-visualization)

# Week 1

First we should prepare everything we need before actual execute. We take into consideration, that Tabelau Trial is valid for 14 days or you may need to obtain Student License for 1 year. You may need to ask someone with student id to help you or find your old id.

Let's define the questions that we want to answer before we start.

0. Start this free course [Data Visualization and Communication with Tableau](https://www.coursera.org/learn/analytics-tableau) and try to catch key ideas for Tableau Desktop and maybe you even will obtain the Tableau License.
1. What is Tableau Desktop and how we can download it?
2. What options we have for Tableau Server? (i.e. Online vs Self-Hosted, Windows vs Linux)
3. What is bare mimimum hardware requirements for Tabelau Server?
4. Decide what Public Cloud provider you wnat to use got creating a trial account and a virtual machine for your Tableau Server based on hardware requirements
  - Azure
  - AWS
  - GCP
5. Create a Tableau Public Account (this is also a Tableau Server managed by Tableau).
6. Using Tableau Public find any SuporStore dashboard that looks very cool and download it. Your goal will be to recreate this dashboard later in your Tableau Desktop (trial) and publish into your Public Account. This is a great asset for the Resume.

Before we dive into the BI Admin topic, we want to make sure, we can get a license and understand key concenpts in Tableau:
- Desktop/Client
- Dimension/Measure
- Data Source/Data Model
- Live/Extract
- Workbook/View/Dashboard/Story
- Filters
- Sets
- LOD calculations
- Calculated Fields
- Parameters
- ability to decouple and understand the dashboard from Tableau Public and recreate it

# Week 2

I hope you have Tableau License for Desktop and spent some time to learn Tableau based on resources above.

You also created the Tableau Public account and published the Dashboard. I hope you dashboard looks [nice](https://public.tableau.com/app/profile/waqar.ahmed.shaikh/viz/SuperstoreOverviewDashboard_17090332693110/HomeLM). 

You don't need to invet bicycle, just grab the dashboard and redo from skratch.

Anyway, idea is simple -> publich to Tableau Public is the same as publish to Tableau Server.

You should know what is:
- Tableau Data Source
- Extract vs Live Connection
- Dimensions/Measures
- Continiues/Discrete
- Key Dashboard and Data Viz rules
- Have in mind Dashboards examples

Great resources for Dashboards best practices (vendor agnostic):
1. [The Big Book of Dashboards](https://www.tableau.com/big-book-dashboards)
2. [Information Dashboard Design: Displaying Data for At-a-Glance Monitoring](https://www.amazon.ca/Information-Dashboard-Design-At-Glance-dp-1938377001/dp/1938377001/ref=dp_ob_image_bk)

> You have to read these book if you are serious about data career.

During week 2 we will focus on collecting requirements for our BI server.

Let's start from assumptions:
1. Our e-commerce company has 600 employees
2. 60 users (10%) require access to the BI
3. Among 60 users we have the ratio:
   - 5 developers - actual people with Tableau Desktop
   - 10 power users - can work with Tableau Server and create new dashboards using Tableau Server
   - 45 viewers, who can interact with dashboards (mostly business users or executives)
4. We have several departments: Product, Marketing, Sales, Finance, Customer Services, Engineering. And 55 users are distributed among them. The 3 developers are in Data Team, 1 in Product, 1 in Marketing (like BI champions).

> Learn about [Tableau License](https://help.tableau.com/current/blueprint/en-us/bp_license_types.htm). You can also try to estimate the cost of BI for this organisation.

Before we will implement BI server, we should come up with the:
1. Plan for Role Based Access i.e. create groups and roles and distributed users among them. We can use a table in markdown or spreadsheet.
2. Define the department fodlers/projects and assign the groups. Idea that Marketing folder only allowes marketing users to look the dashboard.
3. There will be one more case - adding [role based filters](https://help.tableau.com/current/pro/desktop/en-us/publish_userfilters.htm) for Sales, i.e. Sales from Vancouver aitomatically filter only Vancouver and so on. (this is feature of BI).
4. We need to understand [the minimum size of Tableau Server](https://help.tableau.com/current/server/en-us/server_hardware_min.htm) for Test and for Production and then find the cost of VM on AWS or Azure using free trial. Assume, we have 200$ free Azure trial. Using Azure Calculator we can estimate cost of VM and see how long we can run Dev VM for Tableau Server using available credits.

Next week, we will install Tableau Server on Windows VM and connect Tableau Desktop. And do several key admin duties.


