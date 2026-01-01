-- FINAL: Create Dynamic Table with ALL 13 columns
-- Copy and run this ENTIRE block in Snowsight
-- Make sure you see "successfully created" message

USE DATABASE AI_GOOD;
USE SCHEMA PUBLIC;
USE WAREHOUSE COMPUTE_WH;

-- First, drop the old one completely
DROP DYNAMIC TABLE IF EXISTS INVENTORY_AT_RISK_DT;
DROP DYNAMIC TABLE IF EXISTS INVENTORY_METRICS_DT;

-- Now create with COMPLETE SELECT statement including all 4 new columns
CREATE DYNAMIC TABLE inventory_metrics_dt
  TARGET_LAG = '1 minute'
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
  CASE WHEN days_of_cover IS NULL OR lead_time_days IS NULL THEN NULL
       ELSE days_of_cover - lead_time_days END AS urgency_score,
  CASE
    WHEN days_of_cover IS NULL OR lead_time_days IS NULL THEN 'Unknown'
    WHEN days_of_cover <= 0 THEN 'Critical'
    WHEN (days_of_cover - lead_time_days) <= 0 THEN 'High'
    WHEN days_of_cover < 2 THEN 'High'
    WHEN days_of_cover <= (lead_time_days + 1) THEN 'High'
    WHEN days_of_cover <= 5 THEN 'Medium'
    ELSE 'Low'
  END AS priority,
  GREATEST(0, closing_stock - (30 * COALESCE(avg_daily_issue, 0))) AS potential_waste,
  ROUND((5 + lead_time_days) * COALESCE(avg_daily_issue, 0), 0) AS optimal_stock
FROM scored
WHERE rn = 1;

-- Verify the definition was saved correctly
SELECT 
    'Check the text column below - it should include urgency_score, priority, potential_waste, optimal_stock' AS instruction;

SHOW DYNAMIC TABLES LIKE 'INVENTORY_METRICS_DT';

