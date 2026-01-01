# SQL Setup Files for Inventory Heatmap & Stock-Out Alerts

## Setup Order

Run these SQL files in Snowflake Snowsight in the following order:

### 1. `setup.sql` (Required - Run First)
- Creates `stock_daily` table
- Seeds sample data
- Creates `inventory_metrics_v` view
- Creates `inventory_at_risk_v` view

**Usage:**
```sql
USE DATABASE AI_GOOD;
USE SCHEMA PUBLIC;
USE WAREHOUSE COMPUTE_WH;
-- Then run setup.sql
```

### 2. `dynamic_tables.sql` (Recommended)
- Converts views to Dynamic Tables for auto-refresh
- Creates `inventory_metrics_dt` (replaces view)
- Creates `inventory_at_risk_dt` (replaces view)
- Auto-refreshes every 1 minute when source data changes

**Usage:**
```sql
-- After running setup.sql
-- Run dynamic_tables.sql
```

**Note:** After creating Dynamic Tables, update your Streamlit app to use:
- `inventory_metrics_dt` instead of `inventory_metrics_v`
- `inventory_at_risk_dt` instead of `inventory_at_risk_v`

### 3. `streams_tasks.sql` (Optional - Advanced)
- Creates Stream on `stock_daily` to detect changes
- Creates Task to log changes
- Creates Task to check for critical items
- Demonstrates automation capabilities

**Usage:**
```sql
-- After running setup.sql (and optionally dynamic_tables.sql)
-- Run streams_tasks.sql
```

## Dynamic Tables vs Views

**Views (setup.sql):**
- ✅ Simple, no refresh overhead
- ❌ Must be queried to compute (on-demand)
- ❌ No automatic refresh

**Dynamic Tables (dynamic_tables.sql):**
- ✅ Auto-refresh when source data changes
- ✅ Pre-computed results (faster queries)
- ✅ Better for dashboards that need fresh data
- ⚠️ Uses warehouse credits for refresh

## Streams & Tasks

**Streams:**
- Detect INSERT, UPDATE, DELETE operations
- Track changes to tables
- Used for change data capture (CDC)

**Tasks:**
- Scheduled SQL statements
- Can process Stream data
- Can trigger alerts or other actions
- Run on a schedule (e.g., every minute)

## Monitoring

### Check Dynamic Table Status
```sql
SELECT * FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE name = 'INVENTORY_METRICS_DT'
ORDER BY refresh_start_time DESC;
```

### Check Task Status
```sql
SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE name = 'PROCESS_STOCK_CHANGES'
ORDER BY scheduled_time DESC;
```

### Check Stream Data
```sql
SELECT * FROM stock_daily_stream;
```

## Free Tier Considerations

- Dynamic Tables use warehouse credits for refresh
- Tasks use warehouse credits when they run
- Keep `TARGET_LAG` reasonable (1-5 minutes) to conserve credits
- Monitor credit usage in Snowflake account

## Troubleshooting

### Dynamic Table not refreshing?
- Check warehouse is running
- Verify `TARGET_LAG` is set correctly
- Check for errors: `SELECT * FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())`

### Task not running?
- Tasks are created in SUSPENDED state - use `ALTER TASK <name> RESUME`
- Check task schedule is valid
- Verify warehouse has credits

### Stream showing no data?
- Streams only show new changes after creation
- Insert/update data in `stock_daily` to see changes
- Stream data is consumed when queried (use carefully)

