from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

# Database URL
DATABASE_URL = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test"

# Create engine
engine = create_engine(DATABASE_URL)

# Create database if it doesn't exist
if not database_exists(engine.url):
    create_database(engine.url)
    print("Database created successfully!")
else:
    print("Database already exists.") 