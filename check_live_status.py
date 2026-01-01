import sys
sys.stdout.reconfigure(encoding='utf-8')

from snowflake.snowpark import Session
import toml

print("Checking if Dynamic Table has all columns for live app...")
print("=" * 60)

try:
    secrets = toml.load(open('.streamlit/secrets.toml'))
    config = secrets['snowflake']
    session = Session.builder.configs({
        'account': config['account'],
        'user': config['user'],
        'password': config['password'],
        'warehouse': config.get('warehouse', 'COMPUTE_WH'),
        'database': config.get('database', 'AI_GOOD'),
        'schema': config.get('schema', 'PUBLIC'),
        'role': config.get('role', 'ACCOUNTADMIN')
    }).create()

    print("1. Checking if columns exist in table...")
    try:
        result = session.sql("""
            SELECT 
                urgency_score, 
                priority, 
                potential_waste, 
                optimal_stock
            FROM INVENTORY_METRICS_DT 
            LIMIT 1
        """).collect()
        print("   ✅ Columns exist and are queryable!")
        if result:
            row = result[0]
            print(f"   Sample: urgency_score={row.get('URGENCY_SCORE')}, priority={row.get('PRIORITY')}")
    except Exception as e:
        print(f"   ❌ Columns missing: {str(e)[:100]}")
    
    print("\n2. Checking table definition...")
    result = session.sql("SHOW DYNAMIC TABLES LIKE 'INVENTORY_METRICS_DT'").collect()
    if result:
        definition = result[0]['text']
        has_new_cols = all(col in definition.lower() for col in ['urgency_score', 'priority', 'potential_waste', 'optimal_stock'])
        if has_new_cols:
            print("   ✅ Definition includes all 4 new columns")
        else:
            print("   ❌ Definition is missing new columns")
            print("   The CREATE statement may not have executed fully")
    
    print("\n3. Checking data freshness...")
    result = session.sql("""
        SELECT 
            data_timestamp,
            scheduling_state
        FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLES())
        WHERE table_name = 'INVENTORY_METRICS_DT'
    """).collect()
    if result:
        row = result[0]
        print(f"   State: {row['SCHEDULING_STATE']}")
        print(f"   Last data: {row['DATA_TIMESTAMP']}")
    
    print("\n" + "=" * 60)
    print("For Streamlit Cloud:")
    print("1. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)")
    print("2. The app cache will clear on next deployment")
    print("3. Or add ?clear_cache=true to the URL")
    
    session.close()
    
except Exception as e:
    print(f"Error: {str(e)}")

