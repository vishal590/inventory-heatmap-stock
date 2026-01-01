-- Manually refresh Dynamic Tables to ensure they have all columns
-- Run this in Snowflake Snowsight

USE DATABASE AI_GOOD;
USE SCHEMA PUBLIC;
USE WAREHOUSE COMPUTE_WH;

-- Force refresh of the Dynamic Tables
ALTER DYNAMIC TABLE INVENTORY_METRICS_DT REFRESH;
ALTER DYNAMIC TABLE INVENTORY_AT_RISK_DT REFRESH;

-- Wait a moment, then check columns
SELECT 'Dynamic Tables refreshed. Wait 30 seconds, then run: DESCRIBE DYNAMIC TABLE INVENTORY_METRICS_DT;' AS instruction;

-- Check if columns exist by querying
SELECT 
    COLUMN_NAME,
    DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'PUBLIC' 
  AND TABLE_NAME = 'INVENTORY_METRICS_DT'
ORDER BY ORDINAL_POSITION;

