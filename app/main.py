from fastapi import FastAPI
from .database import engine, Base
from .routers import admin_router,user_auth_router, user_router,role_router,privacy_level_setting_router,email_router,verification_router
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
# import rate limiter
from .rate_limiter import TokenBucket, rate_limit
from fastapi.staticfiles import StaticFiles

app = FastAPI()
load_dotenv()
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    os.getenv("WEB_FE_ORIGIN"),
    # Add other origins if needed
]


# middleware to connect to the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Add your Next.js app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


global_bucket = TokenBucket(rate=0, capacity=0)

@app.get("/test-rate-limit")
@rate_limit(global_bucket, tokens_required=1)
async def test_rate_limit():
    return {"message": "This should be rate limited"}

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(admin_router.router, prefix="/api/v1", tags=["admin"])
app.include_router(user_router.router, prefix="/api/v1", tags=["users"])
app.include_router(role_router.router, prefix="/api/v1", tags=["role"])
app.include_router(privacy_level_setting_router.router, prefix="/api/v1", tags=["privacy_level"])
app.include_router(user_auth_router.router, prefix="/api/v1", tags=["auth"])
app.include_router(email_router.router, prefix="/api/v1", tags=["email"])
app.include_router(verification_router.router, prefix="/api/v1", tags=["2FA"])
@app.get("/")
def read_root():
    return {"message": "Welcome to the User API hello"} 
