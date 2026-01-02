# Test Suite

This directory contains test and verification scripts for the Inventory Heatmap & Stock-Out Alerts application.

## Test Files

### Connection Tests
- `test_snowflake_connection.py` - Tests Snowflake connection using Streamlit secrets
- `test_connection_simple.py` - Simple Snowflake connection test

### Data Validation Tests
- `test_new_columns.py` - Tests for data column validation and structure

### Action Logs Tests
- `test_action_logs.py` - Tests action logs table access and functionality
- `test_action_logs_v2.py` - Updated version of action logs tests
- `test_create_action_logs.py` - Tests creating action log entries

### Verification Scripts
- `check_snowflake_tables.py` - Checks Snowflake table structure
- `check_table_structure.py` - Validates table schemas
- `check_dt_columns_direct.py` - Checks Dynamic Table columns
- `check_actual_definition.py` - Verifies table definitions
- `check_live_status.py` - Checks live table status
- `verify_dynamic_tables.py` - Verifies Dynamic Tables configuration

## Running Tests

These are standalone scripts that can be run directly:

```bash
# Test connection
python tests/test_snowflake_connection.py
python tests/test_connection_simple.py

# Validate data
python tests/test_new_columns.py

# Test action logs
python tests/test_action_logs.py
python tests/test_action_logs_v2.py
python tests/test_create_action_logs.py

# Verify tables
python tests/check_snowflake_tables.py
python tests/verify_dynamic_tables.py
```

## Note

These are utility and verification scripts rather than formal unit tests. For production use, consider organizing them into a proper test framework (pytest, unittest) with test fixtures and assertions.

