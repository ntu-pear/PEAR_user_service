#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Run the database creation script
python create_db.py

# Run the database initialization script
python init_db.py

#initialize alembic for data migration

# #Run unit test for user
# python -m pytest tests/test_user_route.py

# Start the FastAPI application with Uvicorn
exec "$@"
