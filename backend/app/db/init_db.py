# backend/app/db/init_db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import time

# Import your Base and all models that inherit from it
from shared.db import base  # Import Job or any other model classes

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

def init_db():
    engine = None
    max_retries = 10
    retry_delay = 5 # seconds

    for i in range(max_retries):
        try:
            print(f"Attempt {i+1}/{max_retries}: Connecting to database at {DATABASE_URL}...")
            engine = create_engine(DATABASE_URL)
            # Try to connect to ensure the database is ready
            with engine.connect() as connection:
                base.Base.metadata.drop_all(bind=engine) # Optional: drops all tables
                base.Base.metadata.create_all(bind=engine) # Creates all tables defined in Base
            print("Database tables created successfully!")
            break
        except Exception as e:
            print(f"Database connection failed: {e}")
            if i < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Could not connect to database.")
                raise # Re-raise the exception if all retries fail

if __name__ == "__main__":
    init_db()