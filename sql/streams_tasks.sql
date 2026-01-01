-- Streams & Tasks for scheduling and automation
-- Run this in Snowflake Snowsight after running setup.sql
-- Streams detect changes, Tasks can trigger actions

-- Set context (adjust if needed)
-- USE DATABASE AI_GOOD;
-- USE SCHEMA PUBLIC;
-- USE WAREHOUSE COMPUTE_WH;

-- Create a Stream on stock_daily to detect changes
CREATE OR REPLACE STREAM stock_daily_stream ON TABLE stock_daily;

-- Optional: Create a table to log when changes are detected
CREATE OR REPLACE TABLE stock_change_log (
  change_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  location STRING,
  item STRING,
  date DATE,
  change_type STRING,  -- 'INSERT', 'UPDATE', 'DELETE'
  old_closing_stock NUMBER,
  new_closing_stock NUMBER
);

-- Create a Task that processes stream changes and logs them
-- This task runs every minute and processes any new changes
CREATE OR REPLACE TASK process_stock_changes
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = '1 minute'
WHEN
  SYSTEM$STREAM_HAS_DATA('stock_daily_stream')
AS
  INSERT INTO stock_change_log (location, item, date, change_type, old_closing_stock, new_closing_stock)
  SELECT 
    location,
    item,
    date,
    METADATA$ACTION AS change_type,
    LAG(closing_stock) OVER (PARTITION BY location, item, date ORDER BY METADATA$ACTION_TIMESTAMP) AS old_closing_stock,
    closing_stock AS new_closing_stock
  FROM stock_daily_stream
  WHERE METADATA$ACTION IN ('INSERT', 'UPDATE');

-- Resume the task (tasks are created in SUSPENDED state by default)
ALTER TASK process_stock_changes RESUME;

-- Optional: Create a table to store critical item alerts
CREATE OR REPLACE TABLE critical_items_alerts (
  alert_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  location STRING,
  item STRING,
  days_of_cover NUMBER,
  closing_stock NUMBER,
  suggested_reorder NUMBER
);

-- Optional: Create a Task to check and log critical items at risk
-- This task runs every 5 minutes and logs items with <= 2 days of cover
CREATE OR REPLACE TASK check_at_risk_items
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = '5 minutes'  -- Check every 5 minutes
AS
  INSERT INTO critical_items_alerts (location, item, days_of_cover, closing_stock, suggested_reorder)
  SELECT 
    location,
    item,
    days_of_cover,
    closing_stock,
    suggested_reorder
  FROM inventory_metrics_dt
  WHERE days_of_cover IS NOT NULL 
    AND days_of_cover <= 2  -- Critical: less than 2 days of cover
    AND NOT EXISTS (
      -- Avoid duplicate alerts for the same item/location within the same hour
      SELECT 1 FROM critical_items_alerts 
      WHERE critical_items_alerts.location = inventory_metrics_dt.location
        AND critical_items_alerts.item = inventory_metrics_dt.item
        AND critical_items_alerts.alert_timestamp > DATEADD(hour, -1, CURRENT_TIMESTAMP())
    );

-- Resume the alert task
ALTER TASK check_at_risk_items RESUME;

-- View task status
-- SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY());

-- View stream status
-- SELECT * FROM stock_daily_stream;

