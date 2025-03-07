import os
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError
from app.database import Base
from dotenv import load_dotenv
from app.models import privacy_level_setting_model,role_model,user_model
from urllib.parse import quote_plus

# Load environment variables from .env file
load_dotenv()

# Get the database URL from environment variables
#ntu
#DATABASE_URL = os.getenv("DB_URL")
#local
#DATABASE_URL = os.getenv("DB_URL_LOCAL")

username = os.getenv("DB_USERNAME_DEV")
password = os.getenv("DB_PASSWORD_DEV") # Contains `@`, needs encoding
server = os.getenv("DB_SERVER_DEV")
database = os.getenv("DB_DATABASE_DEV")
driver = "ODBC+Driver+17+for+SQL+Server"

encoded_password = quote_plus(password)  # Encode special characters

DATABASE_URL = (
    f"mssql+pyodbc://{username}:{encoded_password}@{server}:1433/{database}"
    f"?TrustServerCertificate=yes&driver={driver}"
)

print(DATABASE_URL, "Trying...")
# Create engine for MSSQL database
engine = create_engine(DATABASE_URL)

# Create all tables in the database
try:
    with engine.connect() as connection:
        Base.metadata.create_all(bind=engine)
        print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
    