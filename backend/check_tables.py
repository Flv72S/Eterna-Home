from sqlalchemy import create_engine, text, inspect

# Connessione al database eterna_home
engine = create_engine('postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home')

# Verifica delle tabelle esistenti
inspector = inspect(engine)
tables = inspector.get_table_names()
print("Tabelle presenti nel database:", tables)

# Verifica della struttura della tabella users
if 'users' in tables:
    columns = inspector.get_columns('users')
    print("\nStruttura della tabella users:")
    for column in columns:
        print(f"- {column['name']}: {column['type']}") 