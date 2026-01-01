-- Snowflake Cortex AI Functions for Inventory Analysis
-- Run this in Snowflake Snowsight to add AI-powered SQL functions
-- These functions use Snowflake Cortex for AI-powered insights

-- Set context (adjust if needed)
-- USE DATABASE AI_GOOD;
-- USE SCHEMA PUBLIC;
-- USE WAREHOUSE COMPUTE_WH;

-- ============================================================================
-- Function 1: Generate AI Summary for At-Risk Items
-- ============================================================================
-- This function uses Cortex to generate plain-language summaries of inventory status
CREATE OR REPLACE FUNCTION generate_inventory_summary()
RETURNS STRING
LANGUAGE SQL
AS
$$
  SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'llama2-70b-chat',
    ARRAY_CONSTRUCT(
      OBJECT_CONSTRUCT(
        'role', 'user',
        'content', 
        'Analyze this inventory situation and provide a concise, actionable summary for procurement teams:\n\n' ||
        'Critical items (red status):\n' ||
        COALESCE(
          (SELECT LISTAGG(
            '- ' || item || ' at ' || location || ': Only ' || ROUND(days_of_cover, 1) || ' days left, reorder ' || suggested_reorder || ' units',
            '\n'
          ) WITHIN GROUP (ORDER BY days_of_cover ASC)
          FROM inventory_metrics_dt
          WHERE status = 'red' AND days_of_cover IS NOT NULL
          LIMIT 10),
          'None'
        ) || '\n\n' ||
        'Warning items (orange status):\n' ||
        COALESCE(
          (SELECT LISTAGG(
            '- ' || item || ' at ' || location || ': ' || ROUND(days_of_cover, 1) || ' days left, reorder ' || suggested_reorder || ' units',
            '\n'
          ) WITHIN GROUP (ORDER BY days_of_cover ASC)
          FROM inventory_metrics_dt
          WHERE status = 'orange' AND days_of_cover IS NOT NULL
          LIMIT 10),
          'None'
        ) || '\n\n' ||
        'Provide a brief, professional summary highlighting priorities and recommended actions.'
      )
    )
  )::STRING AS summary
$$;

-- ============================================================================
-- Function 2: AI-Powered Reorder Recommendation Explanation
-- ============================================================================
-- Explains why a specific item needs reordering using AI
CREATE OR REPLACE FUNCTION explain_reorder_recommendation(
  p_location STRING,
  p_item STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
  SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'llama2-70b-chat',
    ARRAY_CONSTRUCT(
      OBJECT_CONSTRUCT(
        'role', 'user',
        'content',
        'Explain why this inventory item needs reordering in simple terms:\n\n' ||
        'Item: ' || p_item || '\n' ||
        'Location: ' || p_location || '\n' ||
        COALESCE(
          (SELECT 
            'Current stock: ' || closing_stock || ' units\n' ||
            'Days of cover remaining: ' || ROUND(days_of_cover, 1) || ' days\n' ||
            'Average daily consumption: ' || ROUND(avg_daily_issue, 2) || ' units/day\n' ||
            'Lead time: ' || lead_time_days || ' days\n' ||
            'Suggested reorder: ' || suggested_reorder || ' units\n' ||
            'Priority: ' || priority || '\n' ||
            'Urgency score: ' || ROUND(urgency_score, 1) || ' (negative means critical)\n\n' ||
            'Provide a clear, actionable explanation for procurement teams.'
          FROM inventory_metrics_dt
          WHERE location = p_location AND item = p_item
          LIMIT 1),
          'Item not found in inventory metrics.'
        )
      )
    )
  )::STRING AS explanation
$$;

-- ============================================================================
-- View: At-Risk Items with AI Summary Column (Placeholder)
-- ============================================================================
-- Note: Views cannot directly call Cortex functions, but you can use the functions in queries
-- Example query to use with this view:
-- SELECT *, explain_reorder_recommendation(location, item) AS ai_explanation
-- FROM inventory_at_risk_v;

-- ============================================================================
-- Example Queries Using Cortex AI Functions
-- ============================================================================

-- Example 1: Get AI summary of all at-risk items
-- SELECT generate_inventory_summary() AS ai_summary;

-- Example 2: Get AI explanation for a specific item
-- SELECT explain_reorder_recommendation('Central', 'Amoxicillin') AS ai_explanation;

-- Example 3: Get AI explanations for all critical items
-- SELECT 
--   location,
--   item,
--   days_of_cover,
--   suggested_reorder,
--   explain_reorder_recommendation(location, item) AS ai_explanation
-- FROM inventory_metrics_dt
-- WHERE status = 'red'
-- ORDER BY days_of_cover ASC;

-- ============================================================================
-- Optional: Create a Task to Generate Daily AI Summary
-- ============================================================================
-- This task generates an AI summary daily and stores it in a table
CREATE OR REPLACE TABLE daily_ai_summaries (
  summary_date DATE DEFAULT CURRENT_DATE(),
  summary_text STRING,
  generated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Task to generate daily AI summary (runs once per day at 8 AM UTC)
-- Note: Uncomment and adjust schedule as needed
/*
CREATE OR REPLACE TASK generate_daily_ai_summary
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 8 * * * UTC'
AS
  INSERT INTO daily_ai_summaries (summary_text)
  SELECT generate_inventory_summary();

ALTER TASK generate_daily_ai_summary RESUME;
*/

-- ============================================================================
-- Notes:
-- ============================================================================
-- 1. Cortex functions require appropriate privileges and may consume credits
-- 2. The 'llama2-70b-chat' model is used as an example - adjust based on availability
-- 3. These functions can be called from Streamlit app or SQL queries
-- 4. For better performance, consider caching results or using them selectively
-- 5. Cortex functions are available in Snowflake accounts with Cortex enabled
-- 6. Alternative models: 'mistral-large', 'mixtral-8x7b', 'llama3-70b', etc.

