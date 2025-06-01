from sqlalchemy import create_engine, text

# Connessione al database postgres (default)
engine = create_engine('postgresql://postgres:N0nn0c4rl0!!@localhost/postgres')

# Creazione del database
with engine.connect() as conn:
    conn.execute(text('commit'))  # Necessario per creare un nuovo database
    conn.execute(text('CREATE DATABASE eterna_home'))
    print("Database 'eterna_home' creato con successo!") 