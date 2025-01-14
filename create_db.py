import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# # Get individual components from environment variables
# driver = os.getenv("DB_DRIVER")
# server = os.getenv("DB_SERVER")
# database = 'master'  # Connect to the master database to create a new database
# username = os.getenv("DB_USERNAME")
# password = os.getenv("DB_PASSWORD")

# # Construct the connection string
# connection_string = f'DRIVER={{{driver}}};SERVER={{{server}}};DATABASE={database};UID={username};PWD={password}'
# DB_DATABASE = os.getenv("DB_DATABASE")
# # SQL command to create the database (change the db name if required)
# create_db_query = f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{DB_DATABASE}') CREATE DATABASE FYP;"

# try:
#     # Connect to the SQL Server
#     with pyodbc.connect(
#         driver=f'{{{driver}}}',
#         server=server,
#         database=database,
#         uid=username,
#         pwd=password,
#         autocommit=True,
#     ) as conn:
#         with conn.cursor() as cursor:
#             cursor.execute(create_db_query)
#             print(f"Database '{DB_DATABASE}' created or already exists.")
# except Exception as e:
#     print(f"An error occurred: {e}")
    

# Get individual components from environment variables
driver = os.getenv("DB_DRIVER")
server = os.getenv("DB_SERVER")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")

# Construct the connection string
#connection_string = f'DRIVER={{{driver}}};SERVER={{{server}}};DATABASE={database};UID={username};PWD={password}'
DB_DATABASE = os.getenv("DB_DATABASE")
# SQL command to create the database (change the db name if required)
create_db_query = f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{DB_DATABASE}') CREATE DATABASE [{DB_DATABASE}];"

try:
    connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};"
    with pyodbc.connect(connection_string, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(create_db_query)
            print(f"Database {database} created or already exists.")
except Exception as e:
    print("Error details:")
    print(f"Driver: {driver}, Server: {server}, Database: {database}, User: {username}")
    print(f"An error occurred: {e}")