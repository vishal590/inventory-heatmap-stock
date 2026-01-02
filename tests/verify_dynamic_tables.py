import sys
sys.stdout.reconfigure(encoding='utf-8')

from snowflake.snowpark import Session
import toml

print("Verifying Dynamic Tables have all columns...")
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
    print("Checking INVENTORY_METRICS_DT columns:")
    print("=" * 60)
    try:
        result = session.sql("DESCRIBE DYNAMIC TABLE INVENTORY_METRICS_DT").collect()
        required_columns = ["date", "location", "item", "closing_stock", "avg_daily_issue", 
                           "days_of_cover", "lead_time_days", "status", "suggested_reorder",
                           "urgency_score", "priority", "potential_waste", "optimal_stock"]
        
        actual_columns = [row['name'].lower() for row in result]
        print(f"   Found {len(actual_columns)} columns:")
        for row in result:
            print(f"      - {row['name']:25s} ({row['type']})")
        
        print(f"\n   Required columns check:")
        missing = []
        for col in required_columns:
            if col in actual_columns:
                print(f"      ✓ {col}")
            else:
                print(f"      ✗ {col} - MISSING")
                missing.append(col)
        
        if missing:
            print(f"\n   ⚠️  Missing columns: {', '.join(missing)}")
        else:
            print(f"\n   ✅ All required columns present!")
            
    except Exception as e:
        print(f"   [ERROR] {str(e)}")
    
    print("\n" + "=" * 60)
    print("Checking INVENTORY_AT_RISK_DT:")
    print("=" * 60)
    try:
        result = session.sql("SELECT COUNT(*) AS cnt FROM INVENTORY_AT_RISK_DT").collect()
        count = result[0]['CNT'] if result else 0
        print(f"   [OK] Table exists with {count} rows")
        
        result = session.sql("DESCRIBE DYNAMIC TABLE INVENTORY_AT_RISK_DT").collect()
        print(f"   Columns: {len(result)}")
        for row in result[:5]:
            print(f"      - {row['name']:25s} ({row['type']})")
        if len(result) > 5:
            print(f"      ... and {len(result) - 5} more")
    except Exception as e:
        print(f"   [ERROR] {str(e)}")
    
    session.close()
    print("\n[SUCCESS] Verification complete!")
    
except FileNotFoundError:
    print(f"[ERROR] File not found: {secrets_path}")
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

