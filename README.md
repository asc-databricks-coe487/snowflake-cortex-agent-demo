# Zoom FTL Pipeline

Multi-agent AI pipeline for FTL Bronze → Silver → Gold migration.
Built on Snowflake Cortex with Streamlit orchestration.

## What's in This Repo

| Folder | Contents |
|--------|----------|
| `streamlit_app.py` | Main 3-agent pipeline UI |
| `pages/` | Saved runs viewer |
| `sql/procedures/` | All Snowflake stored procedures |
| `sql/agents/` | Agent definitions (DESCRIBE output) |
| `tests/` | Unit, functional, regression tests |


## How to Deploy a Change

1. Edit files locally
2. `git add . && git commit -m "your message" && git push`
3. In Snowflake Worksheet:
   `ALTER GIT REPOSITORY ZOOM_AI_POC.PUBLIC.FTL_PIPELINE_REPO FETCH;`
4. Refresh Streamlit app
