from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, drop_database

# Database URL
DATABASE_URL = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test"

# Create engine
engine = create_engine(DATABASE_URL)

# Drop database if it exists
if database_exists(engine.url):
    drop_database(engine.url)
    print("Database dropped successfully!")
else:
    print("Database does not exist.") 