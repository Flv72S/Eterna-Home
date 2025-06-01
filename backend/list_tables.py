from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Mostra informazioni sul database corrente
    current_db = conn.execute(text('SELECT current_database()')).scalar()
    current_schema = conn.execute(text('SELECT current_schema()')).scalar()
    print(f'Database corrente: {current_db}')
    print(f'Schema corrente: {current_schema}')
    print('\nTabelle in tutti gli schemi:')
    
    # Query diretta per elencare tutte le tabelle
    result = conn.execute(text("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name
    """))
    
    current_schema = None
    for schema, table in result:
        if schema != current_schema:
            print(f'\nSchema: {schema}')
            current_schema = schema
        print(f'  - {table}') 