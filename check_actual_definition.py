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

    print("Checking actual Dynamic Table definition...")
    print("=" * 60)
    
    result = session.sql("SHOW DYNAMIC TABLES LIKE 'INVENTORY_METRICS_DT'").collect()
    
    if result:
        row = result[0]
        print("Row data:")
        print(row)
        print("\n" + "=" * 60)
        
        try:
            definition = row['TEXT'] if 'TEXT' in str(row) else (row['text'] if 'text' in str(row) else '')
            if definition:
                print("Table Definition (first 1000 chars):")
                print(definition[:1000])
                print("\n" + "=" * 60)
                print("Checking if new columns are in definition:")
                
                columns_to_check = ['urgency_score', 'priority', 'potential_waste', 'optimal_stock']
                definition_lower = definition.lower()
                
                for col in columns_to_check:
                    if col.lower() in definition_lower:
                        print(f"  ✓ {col} - FOUND in definition")
                    else:
                        print(f"  ✗ {col} - NOT FOUND in definition")
        except:
            print("Could not extract definition. Row structure:")
            print(f"  Type: {type(row)}")
            print(f"  String representation: {str(row)[:500]}")
    else:
        print("No table found")
    
    session.close()
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()

