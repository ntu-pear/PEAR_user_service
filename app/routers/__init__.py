from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from ..crud import session_crud as User_Session
from ..database import get_db  # Your database session function
from contextlib import asynccontextmanager

app = FastAPI()

# Initialize scheduler
scheduler = BackgroundScheduler()

# Define the task to run periodically (every 5 minutes)
def delete_expired_sessions_task():
    # Fetch DB session (handle session lifecycle properly)
    db = next(get_db())  
    User_Session.delete_sessions(db)
    print(f"Expired sessions cleaned at {datetime.now()}")

# Schedule the task to run every 5 minutes
scheduler.add_job(delete_expired_sessions_task, 'interval', minutes=2)

# Lifespan context manager to manage startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the scheduler during the startup
    if not scheduler.running:
        scheduler.start()
    yield
    # Shutdown the scheduler during the shutdown
    scheduler.shutdown()

# Pass lifespan handler to FastAPI
app = FastAPI(lifespan=lifespan)