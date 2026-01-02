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

    print("Querying INVENTORY_METRICS_DT directly...")
    print("=" * 60)
    
    try:
        df = session.table("INVENTORY_METRICS_DT").limit(1).to_pandas()
        if not df.empty:
            print(f"Columns found: {list(df.columns)}")
            print(f"\nTotal columns: {len(df.columns)}")
            print("\nColumn list:")
            for col in df.columns:
                print(f"  - {col}")
            
            required = ["urgency_score", "priority", "potential_waste", "optimal_stock"]
            missing = [col for col in required if col.upper() not in [c.upper() for c in df.columns]]
            
            if missing:
                print(f"\n⚠️  Still missing: {missing}")
                print("\nThe Dynamic Table may need a moment to refresh.")
                print("Wait 1-2 minutes and check again, or manually refresh:")
                print("  ALTER DYNAMIC TABLE INVENTORY_METRICS_DT REFRESH;")
            else:
                print(f"\n✅ All columns present!")
        else:
            print("Table is empty - waiting for first refresh")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    session.close()
    
except Exception as e:
    print(f"Error: {str(e)}")

