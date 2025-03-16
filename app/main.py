from fastapi import FastAPI, Request
from app.database import engine, Base
from app.routers import admin_router,user_auth_router,supervisor_router, user_router,role_router,email_router,verification_router
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
# import rate limiter
from .rate_limiter import TokenBucket, rate_limit, rate_limit_by_ip
from .routers.__init__ import scheduler, lifespan  # Import the scheduler and lifespan from your __init__.py

app = FastAPI(lifespan=lifespan)
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


global_bucket = TokenBucket(rate=1, capacity=2)

@app.get("/test-rate-limit")
@rate_limit(global_bucket, tokens_required=1)
async def test_rate_limit():
    next_token_in = 1 / global_bucket.rate  # Time in seconds until the next token
    return {
        "message": "Request successful. You are within the rate limit.",
        "tokens_available": global_bucket.tokens,
        "next_token_refill_in_seconds": round(next_token_in, 2)
    }
@app.get("/test-ip-rate-limit")
@rate_limit_by_ip(tokens_required=1)
async def test_ip_rate_limit(request: Request):
    client_ip = request.client.host
    
    return {
        "message": "Request successful.",
        "client_ip": client_ip,
    }
app.include_router(admin_router.router, prefix="/api/v1", tags=["admin"])
app.include_router(user_router.router, prefix="/api/v1", tags=["users"])
app.include_router(role_router.router, prefix="/api/v1", tags=["role"])
app.include_router(supervisor_router.router, prefix="/api/v1", tags=["supervisor"])
app.include_router(user_auth_router.router, prefix="/api/v1", tags=["authentication"])
app.include_router(email_router.router, prefix="/api/v1", tags=["email"])
app.include_router(verification_router.router, prefix="/api/v1", tags=["2FA"])
@app.get("/")
def read_root():
    return {"message": "Welcome to the User API hello"} 
