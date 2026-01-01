-- Unistore Action Logs for tracking user actions on inventory recommendations
-- Run this in Snowflake Snowsight after running setup.sql
-- Unistore provides hybrid tables that combine transactional and analytical workloads

-- Set context (adjust if needed)
-- USE DATABASE AI_GOOD;
-- USE SCHEMA PUBLIC;
-- USE WAREHOUSE COMPUTE_WH;

-- Create a hybrid table for action logs using Unistore
-- This table supports both transactional writes and analytical queries
CREATE OR REPLACE HYBRID TABLE action_logs (
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

-- Create an index on action_timestamp for faster queries
CREATE INDEX IF NOT EXISTS idx_action_timestamp ON action_logs (action_timestamp);

-- Create an index on action_type for filtering
CREATE INDEX IF NOT EXISTS idx_action_type ON action_logs (action_type);

-- Create an index on location and item for location/item-based queries
CREATE INDEX IF NOT EXISTS idx_location_item ON action_logs (location, item);

-- Optional: Create a view for recent actions (last 24 hours)
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

-- Optional: Create a view for action summary by type
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

-- Optional: Create a view for pending actions (actions that need follow-up)
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

-- Note: Hybrid tables in Unistore support:
-- - Fast transactional inserts (for logging actions)
-- - Analytical queries (for reporting and dashboards)
-- - Real-time updates and queries
-- - ACID transactions

