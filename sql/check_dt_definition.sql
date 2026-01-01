-- Check the actual SQL definition of the Dynamic Table
-- Run this in Snowflake Snowsight

USE DATABASE AI_GOOD;
USE SCHEMA PUBLIC;

-- Show the full definition
SHOW DYNAMIC TABLES LIKE 'INVENTORY_METRICS_DT';

-- Also check via INFORMATION_SCHEMA
SELECT 
    "text" AS table_definition
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLES())
WHERE table_schema = 'PUBLIC' 
  AND table_name = 'INVENTORY_METRICS_DT';

