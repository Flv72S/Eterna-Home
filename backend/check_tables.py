from sqlalchemy import create_engine, text

# Connessione al database
engine = create_engine('postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test')

# Query per ottenere le tabelle
with engine.connect() as conn:
    result = conn.execute(text('SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\''))
    print('Tabelle nel database:')
    for row in result:
        print(f'- {row[0]}') 