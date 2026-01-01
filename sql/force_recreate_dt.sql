-- Force complete recreation - run this step by step
-- Run each section separately in Snowsight

USE DATABASE AI_GOOD;
USE SCHEMA PUBLIC;
USE WAREHOUSE COMPUTE_WH;

-- ============================================
-- STEP 1: Drop both tables completely
-- ============================================
DROP DYNAMIC TABLE IF EXISTS INVENTORY_AT_RISK_DT;
DROP DYNAMIC TABLE IF EXISTS INVENTORY_METRICS_DT;

-- Wait a few seconds, then continue to STEP 2
SELECT 'Tables dropped. Wait 5 seconds, then run STEP 2' AS status;

-- ============================================
-- STEP 2: Create INVENTORY_METRICS_DT with ALL columns
-- ============================================
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

SELECT 'INVENTORY_METRICS_DT created. Wait 30-60 seconds for initialization, then run STEP 3' AS status;

-- ============================================
-- STEP 3: Verify columns exist
-- ============================================
SELECT 
    COLUMN_NAME,
    DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'PUBLIC' 
  AND TABLE_NAME = 'INVENTORY_METRICS_DT'
ORDER BY ORDINAL_POSITION;

-- ============================================
-- STEP 4: Test query with new columns
-- ============================================
SELECT 
    urgency_score, 
    priority, 
    potential_waste, 
    optimal_stock
FROM INVENTORY_METRICS_DT 
LIMIT 1;

-- ============================================
-- STEP 5: Create dependent table (only after STEP 4 works)
-- ============================================
CREATE DYNAMIC TABLE inventory_at_risk_dt
  TARGET_LAG = '1 minute'
  WAREHOUSE = COMPUTE_WH
AS
SELECT *
FROM inventory_metrics_dt
WHERE days_of_cover IS NULL OR days_of_cover <= 5;

SELECT '✅ Both Dynamic Tables created successfully!' AS status;

