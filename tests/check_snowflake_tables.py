from snowflake.snowpark import Session
import toml

print("Checking Snowflake Database Structure...")
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
    print("[OK] Connected successfully!\n")
    
    print("=" * 60)
    print("1. CHECKING DATABASE AND SCHEMA")
    print("=" * 60)
    
    result = session.sql("SELECT CURRENT_DATABASE() AS db, CURRENT_SCHEMA() AS schema").collect()
    if result:
        print(f"   Database: {result[0]['DB']}")
        print(f"   Schema: {result[0]['SCHEMA']}\n")
    
    print("=" * 60)
    print("2. CHECKING TABLES")
    print("=" * 60)
    
    tables_to_check = [
        "stock_daily",
        "inventory_metrics_v",
        "inventory_at_risk_v",
        "inventory_metrics_dt",
        "inventory_at_risk_dt",
        "action_logs",
        "critical_items_alerts"
    ]
    
    for table_name in tables_to_check:
        try:
            result = session.sql(f"SELECT COUNT(*) AS cnt FROM {table_name}").collect()
            count = result[0]['CNT'] if result else 0
            print(f"   [OK] {table_name:30s} - EXISTS ({count} rows)")
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg:
                print(f"   [MISSING] {table_name:30s} - NOT FOUND")
            else:
                print(f"   [ERROR] {table_name:30s} - {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    print("3. CHECKING TABLE STRUCTURES")
    print("=" * 60)
    
    print("\n   stock_daily table columns:")
    try:
        result = session.sql("DESCRIBE TABLE stock_daily").collect()
        for row in result:
            print(f"      - {row['name']:20s} ({row['type']})")
    except Exception as e:
        print(f"      [ERROR] {str(e)}")
    
    print("\n   inventory_metrics_v view columns:")
    try:
        result = session.sql("DESCRIBE VIEW inventory_metrics_v").collect()
        for row in result:
            print(f"      - {row['name']:20s} ({row['type']})")
    except Exception as e:
        print(f"      [ERROR] {str(e)}")
    
    print("\n" + "=" * 60)
    print("4. CHECKING DATA")
    print("=" * 60)
    
    try:
        result = session.sql("SELECT COUNT(*) AS cnt FROM stock_daily").collect()
        count = result[0]['CNT']
        print(f"   stock_daily rows: {count}")
        
        if count > 0:
            result = session.sql("SELECT MIN(date) AS min_date, MAX(date) AS max_date, COUNT(DISTINCT location) AS locations, COUNT(DISTINCT item) AS items FROM stock_daily").collect()
            if result:
                row = result[0]
                print(f"   Date range: {row['MIN_DATE']} to {row['MAX_DATE']}")
                print(f"   Locations: {row['LOCATIONS']}")
                print(f"   Items: {row['ITEMS']}")
    except Exception as e:
        print(f"   [ERROR] {str(e)}")
    
    print("\n" + "=" * 60)
    print("5. CHECKING VIEWS")
    print("=" * 60)
    
    views_to_check = [
        "inventory_metrics_v",
        "inventory_at_risk_v",
        "recent_actions_v",
        "action_summary_v",
        "pending_actions_v"
    ]
    
    for view_name in views_to_check:
        try:
            result = session.sql(f"SELECT COUNT(*) AS cnt FROM {view_name}").collect()
            count = result[0]['CNT'] if result else 0
            print(f"   [OK] {view_name:30s} - EXISTS ({count} rows)")
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg:
                print(f"   [MISSING] {view_name:30s} - NOT FOUND")
            else:
                print(f"   [ERROR] {view_name:30s} - {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    print("6. CHECKING DYNAMIC TABLES")
    print("=" * 60)
    
    try:
        result = session.sql("SHOW DYNAMIC TABLES IN SCHEMA").collect()
        if result:
            for row in result:
                print(f"   [OK] {row['name']:30s} - Status: {row.get('state', 'UNKNOWN')}")
        else:
            print("   [INFO] No Dynamic Tables found")
    except Exception as e:
        print(f"   [ERROR] {str(e)}")
    
    print("\n" + "=" * 60)
    print("7. SUMMARY")
    print("=" * 60)
    
    print("\n   Required tables for basic functionality:")
    print("   - stock_daily (main data table)")
    print("   - inventory_metrics_v (metrics view)")
    print("\n   Optional but recommended:")
    print("   - inventory_metrics_dt (Dynamic Table for auto-refresh)")
    print("   - action_logs (Unistore for action tracking)")
    print("\n   To set up missing tables, run SQL files in order:")
    print("   1. sql/setup.sql (creates stock_daily and views)")
    print("   2. sql/dynamic_tables.sql (creates Dynamic Tables)")
    print("   3. sql/unistore_action_logs.sql (creates action_logs)")
    print("   4. sql/streams_tasks.sql (creates Streams & Tasks)")
    
    session.close()
    print("\n[SUCCESS] Database check completed!")
    
except FileNotFoundError:
    print(f"[ERROR] File not found: {secrets_path}")
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    print(f"   Error type: {type(e).__name__}")

print("\n" + "=" * 60)

