from fastapi import FastAPI
from .database import engine, Base
from .routers import user_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# middleware to connect to the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your Next.js app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(user_router.router, prefix="/api/v1", tags=["users"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Patient API hello"} 