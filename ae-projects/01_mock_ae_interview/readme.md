# Analytics Engineering - Mock Interview

## Part 1

### Context

You're joining a fintech company where the data warehouse processes millions of transactions every day.

Recently, the product team introduced a new feature called money vaults. These vaults provide users with a separate space to store their savings, keeping them distinct from their spendable account—a useful way to safeguard emergency funds.

The company regularly conducts experiments to assess the impact of new product features. A major shift recently took place when the feature flagging system was migrated to LaunchDarkly, resulting in a complete transformation of the data structure used for experiments. To ensure continuity in tracking key metrics for the vaults feature during this transition, product analysts quickly developed an interim solution—an ad-hoc dashboard in a BI tool using custom SQL.

This dashboard is actively monitored by the product manager and is shared with the entire company during weekly all-hands meetings. While it serves as a solid MVP, there are challenges: it takes a long time to load and lacks flexibility in slicing and analyzing key metrics.

### Question

How would you build a complete solution that fixes these challenges?

## Part 2

### SQL Challenge

This SQL query is used in the company's BI tool to power the Vault feature launch experiment dashboard.

### Tasks:

- **Understand the Query:** Review the SQL query and explain its purpose. If needed, feel free to clean up the code as part of your explanation.
- **Improve Readability:** Rewrite the query to enhance clarity and maintainability.
- **UNION vs. UNION ALL:** Explain the difference between `UNION` and `UNION ALL`.
- **Deduplicate Experiment Entries:** Some users may enter the same experiment variation multiple times. Modify the query to ensure only the first occurrence of each user’s entry into each experiment is retained.
- **Convert Timestamps to Dates:** Adjust the query so that timestamps are displayed as dates.
- **Optimize for Performance:** Suggest ways to improve the query’s runtime efficiency.
- **Track Experiment Allocation Over Time:** Modify the query to display how users are assigned to each experiment group over time, ensuring there is one row per user per day.

```sql

WITH directpushlaunchdarklyevents AS(
   SELECT event_id,
		event_contextkeys_user,
    event_creationdate,
 event_key AS experiment_name,
       event_variationname AS experiment_variation_name,
event_value AS experiment_variation_description,
 CASE 
  WHEN LOWER(event_value)='t' THEN TRUE
 WHEN LOWER(event_value)='f' THEN FALSE 
 END AS is_experiment_variation
FROM partner_directpush_launchdarkly_events  
  WHERE is_active='Y'
),

legacyfeatureflagevents AS (  
SELECT id AS event_id,
  user AS event_contextkeysuser,
"timestamp" as event_creationdate,
 key AS experiment_name,
variation_name AS experiment_variation_name,
   NULL AS experiment_variation_description,
 value::BOOLEAN AS is_experiment_variation
FROM legacy_feature_flag_events
),

union_all_rows AS (
SELECT * FROM directpush_launchdarkly_events
   UNION ALL
SELECT * FROM legacy_feature_flag_events
),

final AS (
  SELECT experiment_name,
is_experiment_variation,
 created_on,
COUNT(DISTINCT union_all_rows.event_contextkeys_user) AS num_users
 FROM union_all_rows
GROUP BY 1, 2,3
)

SELECT experiment_name,
 created_on,
 CASE WHEN is_experiment_variation=TRUE THEN num_users END AS num_user_true,
CASE WHEN is_experiment_variation=FALSE THEN num_users END AS num_user_false
 FROM final
WHERE experiment_name='vault-launch'
 GROUP BY 1,2,3
ORDER BY num_user_true DESC, num_user_false DESC;
```

## Part 3

### Data Modeling

**How would you design a data mart to make this data easily accessible for analysts?** Your solution should be scalable over time while ensuring that the mart remains the single source of truth for experiment analysis.

### Key Considerations:

1. **Performance Issues:** The current dashboard takes an hour to load, requiring the product manager to open it well in advance of their weekly pod meeting.
2. **Subscription Tier Breakdown:** Analysts need visibility into experiment distribution across the company's three subscription tiers to ensure there are no biases in user allocation. The current query, however, groups all users together, making this analysis impossible.
3. **Historical Experiment Allocation:** Engineers need to track how users are assigned to control and test groups over time. Right now, the query only displays the most recent distribution, preventing them from monitoring allocation trends.

Assume that additional raw data sources in the data warehouse provide details about users and their subscriptions. Even if these sources are not explicitly provided in this case interview, please consider incorporating them into your proposed data model.

## Part 4

### DBT Implementation

Next, we’ll develop a **dbt implementation plan** based on your ERD. We'll go through the following key aspects step by step:

1. **Model Architecture & Layering:** What models should be created, and where should they be placed within your dbt project structure?
2. **Materializations:** Which materialization types would you choose, and what are the trade-offs of each option?
3. **Testing Strategy:** What tests should be implemented, and where would you apply them to ensure data reliability?
4. **Optimizing Development & QA:** The production dataset contains **14 billion rows**, and the nightly run takes **3 hours** to complete. How can you create a more efficient process for local testing and quality assurance?

## Part 5

### Development, Deployment and Post-Deployment

Your **dbt models are ready!** It’s time to open a pull request.

### Key Considerations:

1. **Pull Request Size:** How can you ensure your pull request is appropriately scoped and not too large or too small?
2. **Git Workflow:** Write the Git commands needed to perform the following actions:
    - Create a new branch
    - Commit your code changes
    - Sync your branch with the latest updates from the main branch
    - Push your changes to the remote repository
    - Update your local branch with changes from the remote branch
3. **Monitoring & Alerts:** Where should test failure alerts be sent to notify your team? Outline an error-handling process to efficiently resolve issues, including who is responsible for fixing failures and the expected turnaround time before deploying a fix.
4. **Maintaining Downstream Stability:** If you need to rename tables or columns in the **mart layer**, how would you ensure that downstream dependencies remain intact?
