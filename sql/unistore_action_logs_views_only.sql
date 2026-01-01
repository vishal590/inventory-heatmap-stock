-- Create views for action_logs table
-- Run this AFTER the table is created
-- The table should already exist (created by test script or simple.sql)

USE DATABASE AI_GOOD;
USE SCHEMA PUBLIC;
USE WAREHOUSE COMPUTE_WH;

-- Create view for recent actions (last 24 hours)
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

-- Create view for action summary by type
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

-- Create view for pending actions
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

-- Verify views were created
SELECT 'Views created successfully!' AS status;

