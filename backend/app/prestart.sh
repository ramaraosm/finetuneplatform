#!/bin/bash

# This script runs database migrations/initialization before starting the main app.
# It's crucial for ensuring the DB is ready before the app tries to connect.

echo "Running database initialization..."

# Execute the Python script that creates tables
python /app/app/db/init_db.py

echo "Database initialization complete."

# Now, execute the main command for your backend application (e.g., Uvicorn)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload