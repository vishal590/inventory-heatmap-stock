import streamlit as st
from snowflake.snowpark import Session

print("Testing Snowflake Connection...")
print("=" * 50)

try:
    if "snowflake" in st.secrets:
        print("✅ Found secrets in st.secrets['snowflake']")
        print(f"   Account: {st.secrets['snowflake']['account']}")
        print(f"   User: {st.secrets['snowflake']['user']}")
        print(f"   Warehouse: {st.secrets['snowflake'].get('warehouse', 'COMPUTE_WH')}")
        print(f"   Database: {st.secrets['snowflake'].get('database', 'AI_GOOD')}")
        print(f"   Schema: {st.secrets['snowflake'].get('schema', 'PUBLIC')}")
        
        connection_parameters = {
            "account": st.secrets["snowflake"]["account"],
            "user": st.secrets["snowflake"]["user"],
            "password": st.secrets["snowflake"]["password"],
            "warehouse": st.secrets["snowflake"].get("warehouse", "COMPUTE_WH"),
            "database": st.secrets["snowflake"].get("database", "AI_GOOD"),
            "schema": st.secrets["snowflake"].get("schema", "PUBLIC"),
            "role": st.secrets["snowflake"].get("role", "ACCOUNTADMIN")
        }
        
        print("\n🔄 Attempting to connect...")
        session = Session.builder.configs(connection_parameters).create()
        
        print("✅ Connection successful!")
        
        result = session.sql("SELECT CURRENT_USER() AS user, CURRENT_ACCOUNT() AS account, CURRENT_DATABASE() AS database, CURRENT_WAREHOUSE() AS warehouse").collect()
        if result:
            row = result[0]
            print(f"\n📊 Connection Details:")
            print(f"   User: {row['USER']}")
            print(f"   Account: {row['ACCOUNT']}")
            print(f"   Database: {row['DATABASE']}")
            print(f"   Warehouse: {row['WAREHOUSE']}")
        
        result = session.sql("SELECT COUNT(*) AS count FROM stock_daily").collect()
        if result:
            print(f"\n📦 Data Check:")
            print(f"   Rows in stock_daily: {result[0]['COUNT']}")
        
        session.close()
        print("\n✅ All tests passed! Connection is working.")
        
    else:
        print("❌ No 'snowflake' section found in st.secrets")
        print("   Available secrets:", list(st.secrets.keys()) if hasattr(st.secrets, 'keys') else "None")
        
except Exception as e:
    print(f"\n❌ Connection failed!")
    print(f"   Error: {str(e)}")
    print(f"   Error type: {type(e).__name__}")
    
    if "account" in str(e).lower() or "identifier" in str(e).lower():
        print("\n💡 Tip: Your account identifier might need a region.")
        print("   Try: 'getyhji.us-east-1' instead of 'getyhji'")
    elif "password" in str(e).lower() or "authentication" in str(e).lower():
        print("\n💡 Tip: Check your username and password in secrets.toml")
    elif "warehouse" in str(e).lower():
        print("\n💡 Tip: Make sure warehouse is running: ALTER WAREHOUSE COMPUTE_WH RESUME;")
    elif "database" in str(e).lower():
        print("\n💡 Tip: Make sure database exists: CREATE DATABASE IF NOT EXISTS AI_GOOD;")

print("\n" + "=" * 50)

