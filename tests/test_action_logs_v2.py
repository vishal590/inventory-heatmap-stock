import sys
sys.stdout.reconfigure(encoding='utf-8')

from snowflake.snowpark import Session
import toml
import json

print("Testing action_logs with DataFrame API...")
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
    print("STEP 1: Test table access")
    print("=" * 60)
    try:
        result = session.sql("SELECT COUNT(*) AS cnt FROM action_logs").collect()
        print(f"   [OK] Table accessible - {result[0]['CNT']} rows")
    except Exception as e:
        print(f"   [ERROR] Cannot access table: {str(e)}")
        session.close()
        exit(1)
    
    print("\n" + "=" * 60)
    print("STEP 2: Test INSERT with DataFrame API")
    print("=" * 60)
    
    test_data = {
        "user_id": "TEST_USER",
        "action_type": "TEST_ACTION",
        "location": "Test Location",
        "item": "Test Item",
        "priority": "Medium",
        "days_of_cover": 5.0,
        "suggested_reorder": 100.0,
        "action_details": {"source": "test_script", "test": True},
        "status": "PENDING"
    }
    
    try:
        details_json = json.dumps(test_data["action_details"])
        details_json_escaped = details_json.replace("'", "''").replace("\\", "\\\\")
        
        insert_query = f"""
        INSERT INTO action_logs (
            user_id, action_type, location, item, priority,
            days_of_cover, suggested_reorder, action_details, status
        )
        SELECT 
            '{test_data["user_id"]}', '{test_data["action_type"]}',
            '{test_data["location"]}', '{test_data["item"]}',
            '{test_data["priority"]}',
            {test_data["days_of_cover"]}, {test_data["suggested_reorder"]},
            PARSE_JSON('{details_json_escaped}'),
            '{test_data["status"]}'
        """
        
        session.sql(insert_query).collect()
        print("   [OK] INSERT successful with SELECT statement!")
        
        result = session.sql("SELECT COUNT(*) AS cnt FROM action_logs").collect()
        print(f"   [VERIFIED] Table now has {result[0]['CNT']} rows")
        
        result = session.sql("SELECT * FROM action_logs WHERE action_type = 'TEST_ACTION' ORDER BY action_timestamp DESC LIMIT 1").collect()
        if result:
            row = result[0]
            print(f"   [VERIFIED] Inserted row:")
            print(f"      - Action ID: {row['ACTION_ID']}")
            print(f"      - User: {row['USER_ID']}")
            print(f"      - Type: {row['ACTION_TYPE']}")
            print(f"      - Location: {row['LOCATION']}")
            print(f"      - Item: {row['ITEM']}")
            print(f"      - Status: {row['STATUS']}")
            print(f"      - Details: {row['ACTION_DETAILS']}")
        
    except Exception as e:
        print(f"   [ERROR] INSERT failed: {str(e)}")
        import traceback
        traceback.print_exc()
        session.close()
        exit(1)
    
    session.close()
    print("\n[SUCCESS] All tests passed!")
    
except FileNotFoundError:
    print(f"[ERROR] File not found: {secrets_path}")
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

