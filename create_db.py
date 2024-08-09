import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get individual components from environment variables
driver = os.getenv("DB_DRIVER")
server = os.getenv("DB_SERVER")
database = 'master'  # Connect to the master database to create a new database
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")

# Construct the connection string
connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'

# SQL command to create the database (change the db name if required)
create_db_query = "IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'FYP') CREATE DATABASE FYP;"

try:
    # Connect to the SQL Server
    with pyodbc.connect(connection_string, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(create_db_query)
            print("Database 'FYP' created or already exists.")
except Exception as e:
    print(f"An error occurred: {e}")
