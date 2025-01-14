import os
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError
from app.database import Base
from dotenv import load_dotenv
from app.models import privacy_level_setting_model,role_model,secret_question_model,user_model,user_role_model,user_secret_question_model


# Load environment variables from .env file
load_dotenv()

# Get the database URL from environment variables
#ntu
#DATABASE_URL = os.getenv("DB_URL")
#local
DATABASE_URL = os.getenv("DB_URL_LOCAL")
# DATABASE_URL = "mssql+pyodbc://sa:ILOVEFYP123!@localhost:1433/FYP?driver=ODBC+Driver+17+for+SQL+Server"
print(DATABASE_URL, "Trying...")
# Create engine for MSSQL database
engine = create_engine(DATABASE_URL)

# Create all tables in the database
try:
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
except ProgrammingError as e:
    print(f"An error occurred: {e}")
