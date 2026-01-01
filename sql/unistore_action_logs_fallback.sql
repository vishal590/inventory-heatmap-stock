-- Fallback version: Regular table if HYBRID TABLE is not supported
-- Use this if you get an error with HYBRID TABLE
-- Run this in Snowflake Snowsight

USE DATABASE AI_GOOD;
USE SCHEMA PUBLIC;
USE WAREHOUSE COMPUTE_WH;

-- Create a regular table for action logs (fallback if Unistore not available)
CREATE OR REPLACE TABLE action_logs (
  action_id NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
  action_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  user_id STRING,
  action_type STRING,  -- 'EXPORT_CSV', 'VIEW_DETAILS', 'ACKNOWLEDGE_ALERT', 'CREATE_PO', 'DISMISS_ALERT'
  location STRING,
  item STRING,
  action_details VARIANT,  -- JSON object with additional details
  priority STRING,  -- Priority level of the item acted upon
  days_of_cover NUMBER,
  suggested_reorder NUMBER,
  status STRING DEFAULT 'PENDING'  -- 'PENDING', 'COMPLETED', 'CANCELLED'
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_action_timestamp ON action_logs (action_timestamp);

CREATE INDEX IF NOT EXISTS idx_action_type ON action_logs (action_type);

CREATE INDEX IF NOT EXISTS idx_location_item ON action_logs (location, item);

-- Create views
CREATE OR REPLACE VIEW recent_actions_v AS
SELECT 
  action_id,
  action_timestamp,
  user_id,
  action_type,
  location,
  item,
  priority,
  days_of_cover,
  suggested_reorder,
  status,
  action_details
FROM action_logs
WHERE action_timestamp >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
ORDER BY action_timestamp DESC;

CREATE OR REPLACE VIEW action_summary_v AS
SELECT 
  action_type,
  COUNT(*) AS action_count,
  COUNT(DISTINCT location || '|' || item) AS unique_items_acted_upon,
  MIN(action_timestamp) AS first_action,
  MAX(action_timestamp) AS last_action
FROM action_logs
GROUP BY action_type
ORDER BY action_count DESC;

CREATE OR REPLACE VIEW pending_actions_v AS
SELECT 
  action_id,
  action_timestamp,
  user_id,
  action_type,
  location,
  item,
  priority,
  days_of_cover,
  suggested_reorder,
  action_details
FROM action_logs
WHERE status = 'PENDING'
ORDER BY 
  CASE priority
    WHEN 'Critical' THEN 1
    WHEN 'High' THEN 2
    WHEN 'Medium' THEN 3
    WHEN 'Low' THEN 4
    ELSE 5
  END,
  action_timestamp DESC;

