from snowflake.snowpark import Session
import toml

print("Testing Snowflake Connection...")
print("=" * 50)

try:
    secrets_path = ".streamlit/secrets.toml"
    with open(secrets_path, 'r') as f:
        secrets = toml.load(f)
    
    if "snowflake" in secrets:
        print("[OK] Found secrets in secrets.toml")
        config = secrets["snowflake"]
        print(f"   Account: {config['account']}")
        print(f"   User: {config['user']}")
        
        connection_parameters = {
            "account": config["account"],
            "user": config["user"],
            "password": config["password"],
            "warehouse": config.get("warehouse", "COMPUTE_WH"),
            "database": config.get("database", "AI_GOOD"),
            "schema": config.get("schema", "PUBLIC"),
            "role": config.get("role", "ACCOUNTADMIN")
        }
        
        print("\n[CONNECTING] Attempting to connect (this may take 10-30 seconds)...")
        session = Session.builder.configs(connection_parameters).create()
        
        print("[SUCCESS] Connection successful!")
        
        result = session.sql("SELECT CURRENT_USER() AS user, CURRENT_ACCOUNT() AS account").collect()
        if result:
            row = result[0]
            print(f"   Connected as: {row['USER']}")
            print(f"   Account: {row['ACCOUNT']}")
        
        session.close()
        print("\n[PASS] Connection test passed!")
        
    else:
        print("[ERROR] No 'snowflake' section in secrets.toml")
        
except FileNotFoundError:
    print(f"[ERROR] File not found: {secrets_path}")
except Exception as e:
    print(f"\n[ERROR] Connection failed!")
    print(f"   Error: {str(e)}")
    print(f"   Error type: {type(e).__name__}")
    
    error_msg = str(e).lower()
    if "404" in error_msg or "not found" in error_msg:
        print("\n[FIX] Account identifier needs a REGION suffix!")
        print("   The account 'NX81864' is correct but needs region.")
        print("\n   Try these common regions in secrets.toml:")
        print('   account = "NX81864.us-east-1"     (US East - most common)')
        print('   account = "NX81864.us-west-2"     (US West)')
        print('   account = "NX81864.eu-west-1"     (Europe)')
        print('   account = "NX81864.ap-southeast-1" (Asia Pacific)')
        print("\n   Or find your region by running in Snowsight:")
        print("   SELECT CURRENT_REGION() AS region;")
        print("   Then use: account = 'NX81864.' + region")
    elif "account" in error_msg or "identifier" in error_msg:
        print("\n[FIX] Account identifier issue")
        print("   Check the account format in secrets.toml")
    elif "password" in error_msg or "authentication" in error_msg:
        print("\n[FIX] Check username and password")
    elif "warehouse" in error_msg:
        print("\n[FIX] Run in Snowflake: ALTER WAREHOUSE COMPUTE_WH RESUME;")
    elif "database" in error_msg:
        print("\n[FIX] Run in Snowflake: CREATE DATABASE IF NOT EXISTS AI_GOOD;")

print("\n" + "=" * 50)

