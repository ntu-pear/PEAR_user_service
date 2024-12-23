from app.database import engine, Base
from app.models import (
    privacy_level_setting_model,
    role_model,
    secret_question_model,
    user_model,
    user_role_model,
    user_secret_question_model
)

# Create all tables in the database using the engine
Base.metadata.create_all(bind=engine)

print("Tables created successfully in the DB_DATABASE_DEV database.")