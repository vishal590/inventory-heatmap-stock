# AI for Good Hackathon - Inventory Heatmap & Stock-Out Alerts

## Overview
Solo project for the YourStory/Snowflake AI for Good Hackathon. Challenge: Inventory Heatmap & Stock-Out Alerts for Essential Goods. Goal: a Snowflake-based app that shows stock health by location/item, flags imminent stock-outs, and suggests reorder quantities built entirely on free Snowflake trial features.

## Problem
Hospitals/NGOs struggle to keep medicines/essentials in the right place at the right time. Data is siloed; stock issues are spotted too late. Need a single view with early warnings and actionable reorder guidance.

## Solution
- Ingest daily stock data (`date, location, item, opening_stock, received, issued, closing_stock, lead_time_days`).
- Compute avg_daily_issue, days_of_cover, status (red/orange/green), and suggested reorder qty.
- Streamlit-in-Snowflake UI:
  - Filters (location/item)
  - Heatmap by location x item (color-coded status)
  - At risk table (run-out in N days) with reorder suggestion
  - Export CSV; basic trend chart per item
- Optional: AI SQL/Cortex for plain-language summaries.

## Tech Stack
- Snowflake (free trial): Worksheets/SQL, (optional) Dynamic Tables, Streams & Tasks for refresh
- Streamlit in Snowflake for UI
- Optional Snowpark for simple demand estimate

## Data Schema (example)
Base (daily grain):
- `date`
- `location`
- `item`
- `opening_stock`
- `received`
- `issued`
- `closing_stock`
- `lead_time_days`

Derived:
- `avg_daily_issue` (recent window)
- `days_of_cover = closing_stock / NULLIF(avg_daily_issue, 0)`
- `status` thresholds (e.g., red <2 days, orange 2-5, green >5)
- `suggested_reorder = GREATEST(0, target_days*avg_daily_issue - closing_stock)`

## Starter SQL (metrics view)
```sql
-- rolling avg issue per item/location (7 days as example)
with usage as (
  select
    date,
    location,
    item,
    closing_stock,
    lead_time_days,
    avg(issued) over (
      partition by location, item
      order by date
      rows between 6 preceding and current row
    ) as avg_daily_issue
  from stock_daily
),
scored as (
  select
    location,
    item,
    closing_stock,
    coalesce(avg_daily_issue, 0) as avg_daily_issue,
    case when avg_daily_issue is null or avg_daily_issue = 0 then null
         else closing_stock / avg_daily_issue end as days_of_cover,
    lead_time_days
  from usage
)
select
  location,
  item,
  closing_stock,
  avg_daily_issue,
  days_of_cover,
  lead_time_days,
  case
    when days_of_cover is null then 'unknown'
    when days_of_cover < 2 then 'red'
    when days_of_cover <= 5 then 'orange'
    else 'green'
  end as status,
  greatest(0, (5 * coalesce(avg_daily_issue,0)) - closing_stock) as suggested_reorder
from scored;
```

## Setup (high level)
1) Sign up Snowflake free trial (no card). Create a small warehouse, DB, schema.
2) Load sample CSV into a table.
3) Create views for metrics/status/reorder suggestions.
4) Build Streamlit app in Snowsight using those views.
5) Capture screenshots; link working prototype, GitHub repo, and demo video in submission form.
6) Use provided PPT template for idea/prototype deck.

## Quickstart
- Snowflake: run `sql/setup.sql` in Snowsight/Worksheet (creates `stock_daily`, seeds sample rows, builds `inventory_metrics_v` and `inventory_at_risk_v`).
- Streamlit in Snowflake: create a new Snowsight Streamlit app and paste `app.py` content. Set context to the DB/Schema from setup and ensure the warehouse is active.
- Local demo (CSV fallback): `python -m venv .venv && .venv\\Scripts\\activate`, `pip install -r requirements.txt`, then `streamlit run app.py`. Without Snowflake connection, it uses `data/sample_stock.csv`.
- Optional secrets template: copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml` and fill Snowflake creds if you want to connect in hosted Streamlit.

## Submission Q&A
- What is your idea about? Snowflake + Streamlit dashboard that ingests daily stock data, computes avg daily issue/days-of-cover/status, shows a location x item heatmap, and flags at-risk items with reorder suggestions plus export/trend views.
- What problem are you trying to solve? Hospitals/NGOs spot stock issues too late because data is siloed, causing stock-outs or waste.
- Impact of your solution: Earlier visibility and guidance reduce stock-outs, cut waste, and keep critical supplies available where needed.
- Technology stack being used: Snowflake (SQL; optional Dynamic Tables/Streams/Tasks), Streamlit in Snowflake for UI, optional Snowpark/AI SQL for summaries.

## Submission Fields (prep answers)
- Challenge: Inventory Heatmap & Stock-Out Alerts.
- Idea: Single-view stock health with early warnings and reorder guidance in Snowflake + Streamlit.
- Problem: Late stock visibility leads to waste/stock-outs; data is siloed.
- Impact: Fewer stock-outs, reduced waste, actionable replenishment for critical supplies.
- Tech stack: Snowflake (SQL, optional Dynamic Tables/Streams & Tasks), Streamlit, optional Snowpark/AI SQL.
- Links: working prototype URL, GitHub repo, demo video, prototype deck (PDF <= 5 MB).
