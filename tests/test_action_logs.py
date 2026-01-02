import sys
sys.stdout.reconfigure(encoding='utf-8')

from snowflake.snowpark import Session
import toml
import json

print("Testing action_logs table access...")
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
    print("STEP 2: Test INSERT operation")
    print("=" * 60)
    
    test_action = {
        "source": "test_script",
        "test": True
    }
    details_json = json.dumps(test_action)
    
    details_json_escaped = details_json.replace("'", "''").replace("\\", "\\\\")
    insert_query = f"""
    INSERT INTO action_logs (
        user_id, action_type, location, item, priority,
        days_of_cover, suggested_reorder, action_details, status
    ) VALUES (
        'TEST_USER', 'TEST_ACTION',
        'Test Location', 'Test Item',
        'Medium',
        5.0, 100.0,
        '{details_json_escaped}'::VARIANT,
        'PENDING'
    )
    """
    
    try:
        session.sql(insert_query).collect()
        print("   [OK] INSERT successful!")
        
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
        
    except Exception as e:
        print(f"   [ERROR] INSERT failed: {str(e)}")
        import traceback
        traceback.print_exc()
        session.close()
        exit(1)
    
    print("\n" + "=" * 60)
    print("STEP 3: Test table structure")
    print("=" * 60)
    try:
        result = session.sql("DESCRIBE TABLE action_logs").collect()
        print("   Table columns:")
        for row in result:
            print(f"      - {row['name']:20s} ({row['type']})")
    except Exception as e:
        print(f"   [ERROR] {str(e)}")
    
    session.close()
    print("\n[SUCCESS] All tests passed!")
    
except FileNotFoundError:
    print(f"[ERROR] File not found: {secrets_path}")
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

