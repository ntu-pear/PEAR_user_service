import os
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Get the database URL from environment variables
DB_URL_LOCAL = os.getenv("DB_URL_LOCAL")
DB_DRIVER_DEV = os.getenv("DB_DRIVER_DEV")
DB_SERVER_DEV = os.getenv("DB_SERVER_DEV")
DB_DATABASE_DEV = os.getenv("DB_DATABASE_DEV")
DB_DATABASE_PORT = os.getenv("DB_DATABASE_PORT")
DB_USERNAME_DEV = os.getenv("DB_USERNAME_DEV")
DB_PASSWORD_DEV = os.getenv("DB_PASSWORD_DEV")

# Get the database URL from environment (DOCKER LOCAL)
DB_URL_LOCAL = os.getenv("DB_URL_LOCAL")
DB_DRIVER = os.getenv("DB_DRIVER")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_DATABASE_PORT = os.getenv("DB_DATABASE_PORT")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

##### Note that this connection is to the DEV environment ####
# COMMMENT out this section when doing local development
connection_url = sa.URL.create(
    "mssql+pyodbc",
    username=DB_USERNAME_DEV,
    password=DB_PASSWORD_DEV,
    host=DB_SERVER_DEV,
    port=DB_DATABASE_PORT,
    database=DB_DATABASE_DEV,
    query={"driver": DB_DRIVER_DEV, "TrustServerCertificate": "yes"},
)
###############################################################

########## LOCAL DOCKER DEVELOPMENT ##########
# connection_url = sa.URL.create(
#     "mssql+pyodbc",
#     username=DB_USERNAME,
#     password=DB_PASSWORD,
#     host=DB_SERVER,
#     port=DB_DATABASE_PORT,
#     database=DB_DATABASE,
#     query={"driver": DB_DRIVER, "TrustServerCertificate": "yes"},
# )
##############################################

print(connection_url)
engine = sa.create_engine(connection_url)
##############################################################
# print(DATABASE_URL)
# engine = create_engine(DATABASE_URL, connect_args={"timeout": 30})
# engine_dev = create_engine(DATABASE_URL_DEV, )  # Increase the timeout if necessary

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
