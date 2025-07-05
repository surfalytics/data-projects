### DQX Demo Project

To run in databricks notebook, use the `dqx_demo_notebook.ipynb` file

To run locally in VS Code, use the `dqx_demo_notebook.ipynb` file


#### Configuring remote connection to Databricks in VS Code

1. Install UV package manager
Ex: 
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install dependencies
```
uv sync
```

3. Create access token in Databricks workspace
Go to Profile > Settings > User > Developer > Access tokens > Manage > Generate new token

4. Create databricks config in the home directory
```
~/.databrickscfg
[DEFAULT]
host = https://abcdefasdf.databricks.com
token = your_generated_token
serverless_compute_id = auto
```
