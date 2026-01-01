import sys
sys.stdout.reconfigure(encoding='utf-8')

from snowflake.snowpark import Session
import toml

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

    print("Testing if new columns exist by querying...")
    print("=" * 60)
    
    try:
        result = session.sql("""
            SELECT 
                date, location, item,
                urgency_score, 
                priority, 
                potential_waste, 
                optimal_stock
            FROM INVENTORY_METRICS_DT 
            LIMIT 1
        """).collect()
        
        if result:
            print("✅ SUCCESS! All columns exist and are queryable!")
            row = result[0]
            print(f"\nSample data:")
            print(f"  Location: {row['LOCATION']}")
            print(f"  Item: {row['ITEM']}")
            print(f"  Urgency Score: {row.get('URGENCY_SCORE', 'NULL')}")
            print(f"  Priority: {row.get('PRIORITY', 'NULL')}")
            print(f"  Potential Waste: {row.get('POTENTIAL_WASTE', 'NULL')}")
            print(f"  Optimal Stock: {row.get('OPTIMAL_STOCK', 'NULL')}")
        else:
            print("⚠️  Table is empty - waiting for first refresh")
            
    except Exception as e:
        error_msg = str(e)
        if "invalid identifier" in error_msg.lower() or "does not exist" in error_msg.lower():
            print(f"❌ Columns still missing: {error_msg}")
            print("\nThe Dynamic Table may need more time to refresh.")
            print("Try running:")
            print("  ALTER DYNAMIC TABLE INVENTORY_METRICS_DT REFRESH;")
            print("\nThen wait 1-2 minutes and check again.")
        else:
            print(f"Error: {error_msg}")
            import traceback
            traceback.print_exc()
    
    session.close()
    
except Exception as e:
    print(f"Error: {str(e)}")

