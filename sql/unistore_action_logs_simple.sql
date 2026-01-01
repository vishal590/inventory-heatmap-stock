-- Simple version: Create table first, then views
-- Run this in Snowflake Snowsight

USE DATABASE AI_GOOD;
USE SCHEMA PUBLIC;
USE WAREHOUSE COMPUTE_WH;

-- Step 1: Drop existing table/views if they exist (optional, for clean start)
DROP VIEW IF EXISTS pending_actions_v;
DROP VIEW IF EXISTS action_summary_v;
DROP VIEW IF EXISTS recent_actions_v;
DROP TABLE IF EXISTS action_logs;

-- Step 2: Create the action_logs table
CREATE TABLE action_logs (
  action_id NUMBER AUTOINCREMENT START 1 INCREMENT 1,
  action_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  user_id STRING,
  action_type STRING,
  location STRING,
  item STRING,
  action_details VARIANT,
  priority STRING,
  days_of_cover NUMBER,
  suggested_reorder NUMBER,
  status STRING DEFAULT 'PENDING',
  PRIMARY KEY (action_id)
);

-- Step 3: Verify table was created
SELECT 'Table created successfully' AS status, COUNT(*) AS row_count FROM action_logs;

-- Step 4: Create indexes
CREATE INDEX idx_action_timestamp ON action_logs (action_timestamp);
CREATE INDEX idx_action_type ON action_logs (action_type);
CREATE INDEX idx_location_item ON action_logs (location, item);

-- Step 5: Create views
CREATE VIEW recent_actions_v AS
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

CREATE VIEW action_summary_v AS
SELECT 
  action_type,
  COUNT(*) AS action_count,
  COUNT(DISTINCT location || '|' || item) AS unique_items_acted_upon,
  MIN(action_timestamp) AS first_action,
  MAX(action_timestamp) AS last_action
FROM action_logs
GROUP BY action_type
ORDER BY action_count DESC;

CREATE VIEW pending_actions_v AS
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

-- Step 6: Verify everything was created
SELECT 'Setup complete!' AS status;
SELECT 'Tables:' AS type, COUNT(*) AS count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'PUBLIC' AND TABLE_NAME = 'ACTION_LOGS'
UNION ALL
SELECT 'Views:' AS type, COUNT(*) AS count FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA = 'PUBLIC' AND TABLE_NAME IN ('RECENT_ACTIONS_V', 'ACTION_SUMMARY_V', 'PENDING_ACTIONS_V');

