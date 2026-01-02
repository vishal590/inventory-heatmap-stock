from snowflake.snowpark import Session
import toml

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

result = session.sql('DESCRIBE TABLE action_logs').collect()
print('action_logs table columns:')
for i, r in enumerate(result):
    null_info = 'NULL' if r['null?'] == 'Y' else 'NOT NULL'
    default_info = f" DEFAULT {r['default']}" if r['default'] else ""
    print(f"  {i+1}. {r['name']:25s} {r['type']:20s} {null_info}{default_info}")

session.close()

