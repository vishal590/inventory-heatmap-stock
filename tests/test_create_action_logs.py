import sys
sys.stdout.reconfigure(encoding='utf-8')

from snowflake.snowpark import Session
import toml

print("Testing action_logs table creation...")
print("=" * 60)

try:
    secrets_path = ".streamlit/secrets.toml"
    with open(secrets_path, 'r') as f:
        secrets = toml.load(f)
    
    config = secrets["snowflake"]
    connection_parameters = {
        "account": config["account"],
        "user": config["user"],
        "password": config["password"],
        "warehouse": config.get("warehouse", "COMPUTE_WH"),
        "database": config.get("database", "AI_GOOD"),
        "schema": config.get("schema", "PUBLIC"),
        "role": config.get("role", "ACCOUNTADMIN")
    }
    
    print("[CONNECTING] Connecting to Snowflake...")
    session = Session.builder.configs(connection_parameters).create()
    print("[OK] Connected!\n")
    
    print("=" * 60)
    print("STEP 1: Check if table exists")
    print("=" * 60)
    try:
        result = session.sql("SELECT COUNT(*) AS cnt FROM action_logs").collect()
        print(f"   [EXISTS] action_logs table exists ({result[0]['CNT']} rows)")
        print("   [INFO] Table already exists. If you want to recreate, run DROP TABLE first.")
    except Exception as e:
        print(f"   [NOT EXISTS] action_logs table does not exist yet")
        print(f"   Error: {str(e)[:100]}")
    
    print("\n" + "=" * 60)
    print("STEP 2: Try creating table with simple syntax")
    print("=" * 60)
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS action_logs (
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
    )
    """
    
    try:
        session.sql(create_table_sql).collect()
        print("   [OK] Table creation command executed")
        
        result = session.sql("SELECT COUNT(*) AS cnt FROM action_logs").collect()
        print(f"   [VERIFIED] Table exists with {result[0]['CNT']} rows")
    except Exception as e:
        print(f"   [ERROR] Failed to create table")
        print(f"   Error: {str(e)}")
        print("\n   [TROUBLESHOOTING]")
        print("   - Check if you have CREATE TABLE permission")
        print("   - Check if AUTOINCREMENT is supported in your Snowflake edition")
        print("   - Try running: SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE()")
    
    print("\n" + "=" * 60)
    print("STEP 3: Check current role and permissions")
    print("=" * 60)
    try:
        result = session.sql("SELECT CURRENT_ROLE() AS role, CURRENT_WAREHOUSE() AS warehouse, CURRENT_DATABASE() AS db, CURRENT_SCHEMA() AS schema").collect()
        if result:
            row = result[0]
            print(f"   Role: {row['ROLE']}")
            print(f"   Warehouse: {row['WAREHOUSE']}")
            print(f"   Database: {row['DB']}")
            print(f"   Schema: {row['SCHEMA']}")
    except Exception as e:
        print(f"   [ERROR] {str(e)}")
    
    session.close()
    print("\n[COMPLETE] Test finished!")
    
except FileNotFoundError:
    print(f"[ERROR] File not found: {secrets_path}")
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

