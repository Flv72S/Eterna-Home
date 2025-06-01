from sqlalchemy import create_engine, inspect, text

DATABASE_URL = 'postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    print('Tabelle prima della rimozione:', tables)
    for table_name in tables:
        print(f'Dropping table: {table_name}')
        conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
    # Ricontrolla le tabelle dopo
    tables_after = inspect(conn).get_table_names()
    print('Tabelle dopo la rimozione:', tables_after)
    print('Done.') 