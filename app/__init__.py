# import os
# from sqlalchemy import create_engine
# from sqlalchemy.exc import ProgrammingError
# from app.database import Base
# from dotenv import load_dotenv
# from app.models.user_model import User
# import pyodbc
# # from app.models.patient_guardian_model import PatientGuardian
# # from app.models.patient_list_model import PatientList  # Import the new model

# # Load environment variables from .env file
# load_dotenv()

# # Get the database URL from environment variables
# DATABASE_URL = os.getenv("DB_URL")
# # DATABASE_URL = "mssql+pyodbc://sa:ILOVEFYP123!@localhost:1433/FYP?driver=ODBC+Driver+17+for+SQL+Server"
# print(DATABASE_URL, "Trying...")
# # Create engine for MSSQL database
# engine = create_engine(DATABASE_URL)
# # Get individual components from environment variables
# driver = os.getenv("DB_DRIVER")
# server = os.getenv("DB_SERVER")
# database = 'master'  # Connect to the master database to create a new database
# username = os.getenv("DB_USERNAME")
# password = os.getenv("DB_PASSWORD")

# # Construct the connection string
# connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'

# # SQL command to create the database (change the db name if required)
# create_db_query = "IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'FYP') CREATE DATABASE FYP;"

# try:
#     # Connect to the SQL Server
#     with pyodbc.connect(connection_string, autocommit=True) as conn:
#         with conn.cursor() as cursor:
#             cursor.execute(create_db_query)
#             print("Database 'FYP' created or already exists.")
# except Exception as e:
#     print(f"An error occurred: {e}")
# # Create all tables in the database
# try:
#     Base.metadata.create_all(bind=engine)
#     print("Tables created successfully.")
# except ProgrammingError as e:
#     print(f"An error occurred: {e}")
