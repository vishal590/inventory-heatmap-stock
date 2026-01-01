-- Dynamic Tables for auto-refresh calculations
-- Run this in Snowflake Snowsight after running setup.sql
-- Dynamic Tables automatically refresh when source data changes

-- Set context (adjust if needed)
-- USE DATABASE AI_GOOD;
-- USE SCHEMA PUBLIC;
-- USE WAREHOUSE COMPUTE_WH;

-- Create Dynamic Table for inventory metrics (replaces the view with auto-refresh capability)
CREATE OR REPLACE DYNAMIC TABLE inventory_metrics_dt
  TARGET_LAG = '1 minute'  -- Refresh every minute (adjust based on needs)
  WAREHOUSE = COMPUTE_WH
AS
WITH usage AS (
  SELECT
    date,
    location,
    item,
    closing_stock,
    lead_time_days,
    AVG(issued) OVER (
      PARTITION BY location, item
      ORDER BY date
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS avg_daily_issue
  FROM stock_daily
),
scored AS (
  SELECT
    date,
    location,
    item,
    closing_stock,
    lead_time_days,
    COALESCE(avg_daily_issue, 0) AS avg_daily_issue,
    CASE WHEN avg_daily_issue IS NULL OR avg_daily_issue = 0 THEN NULL
         ELSE closing_stock / avg_daily_issue END AS days_of_cover,
    ROW_NUMBER() OVER (PARTITION BY location, item ORDER BY date DESC) AS rn
  FROM usage
)
SELECT
  date,
  location,
  item,
  closing_stock,
  avg_daily_issue,
  days_of_cover,
  lead_time_days,
  CASE
    WHEN days_of_cover IS NULL THEN 'unknown'
    WHEN days_of_cover < 2 THEN 'red'
    WHEN days_of_cover <= 5 THEN 'orange'
    ELSE 'green'
  END AS status,
  GREATEST(0, (5 * COALESCE(avg_daily_issue, 0)) - closing_stock) AS suggested_reorder,
  -- Urgency score: days_of_cover - lead_time_days (negative = critical)
  CASE WHEN days_of_cover IS NULL OR lead_time_days IS NULL THEN NULL
       ELSE days_of_cover - lead_time_days END AS urgency_score,
  -- Priority calculation
  CASE
    WHEN days_of_cover IS NULL OR lead_time_days IS NULL THEN 'Unknown'
    WHEN days_of_cover <= 0 THEN 'Critical'
    WHEN (days_of_cover - lead_time_days) <= 0 THEN 'High'
    WHEN days_of_cover < 2 THEN 'High'
    WHEN days_of_cover <= (lead_time_days + 1) THEN 'High'
    WHEN days_of_cover <= 5 THEN 'Medium'
    ELSE 'Low'
  END AS priority,
  -- Waste metrics: potential waste (overstock > 30 days)
  GREATEST(0, closing_stock - (30 * COALESCE(avg_daily_issue, 0))) AS potential_waste,
  -- Optimal stock level (5 days + lead time)
  ROUND((5 + lead_time_days) * COALESCE(avg_daily_issue, 0), 0) AS optimal_stock
FROM scored
WHERE rn = 1;

-- Create Dynamic Table for at-risk items (auto-refreshes from metrics table)
CREATE OR REPLACE DYNAMIC TABLE inventory_at_risk_dt
  TARGET_LAG = '1 minute'
  WAREHOUSE = COMPUTE_WH
AS
SELECT *
FROM inventory_metrics_dt
WHERE days_of_cover IS NULL OR days_of_cover <= 5;

-- Note: Update your Streamlit app to use inventory_metrics_dt instead of inventory_metrics_v
-- The Dynamic Table will automatically refresh when stock_daily changes

