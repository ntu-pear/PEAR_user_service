import asyncio
import threading

from app.messaging.consumer_manager import create_user_consumer_manager
from fastapi import FastAPI, Request
from app.database import engine, Base
from app.routers import admin_router,user_auth_router,supervisor_router, doctor_router, user_router,role_router,email_router,verification_router, access_level_router, integrity_router, internal_router
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
# import rate limiter
from .rate_limiter import TokenBucket, rate_limit, rate_limit_by_ip
from .routers.__init__ import scheduler, lifespan  # Import the scheduler and lifespan from your __init__.py
from app.service.background_processor import get_processor
from contextlib import asynccontextmanager

import logging


load_dotenv()
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    f"http://{os.getenv('WEB_FE_ORIGIN')}",
    f"http://{os.getenv('WEB_FE_ORIGIN_STAGING')}"
    # Add other origins if needed
]
logger = logging.getLogger("uvicorn")

# Global consumer manager instance
consumer_manager = None
shutdown_event = threading.Event()


def start_consumers():
    """Start RabbitMQ consumers"""
    global consumer_manager
    
    # Check if messaging is enabled (can be controlled via environment variable)
    enable_messaging = os.getenv('ENABLE_MESSAGING', 'true').lower() == 'true'
    
    if not enable_messaging:
        logger.info("Drift consumer disabled via ENABLE_MESSAGING environment variable")
        return
    
    try:
        logger.info("Starting RabbitMQ drift consumer...")
        consumer_manager = create_user_consumer_manager()
        
        # Pass shutdown event to consumer manager
        consumer_manager.set_shutdown_event(shutdown_event)
        
        # Start all registered consumers
        consumer_manager.start_all_consumers()
        
        logger.info("Drift consumer started successfully")
        
        # Log consumer status
        status = consumer_manager.get_consumer_status()
        for name, state in status.items():
            logger.info(f"Consumer {name}: {state}")
            
    except Exception as e:
        logger.error(f"Failed to start drift consumer: {str(e)}", exc_info=True)
        # Don't fail the entire application if messaging fails
        logger.warning("Application will continue without drift consumer")


def stop_consumers():
    """Stop RabbitMQ consumers"""
    global consumer_manager
    
    if consumer_manager:
        try:
            logger.info("Stopping RabbitMQ drift consumer...")
            consumer_manager.stop_all_consumers()
            logger.info("Drift consumer stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping drift consumer: {str(e)}")
    else:
        logger.info("No drift consumer to stop")


@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    """
    Combined lifespan manager that handles both:
    1. Outbox processor
    2. Drift consumer
    """
    # Startup phase
    logger.info("=== Application Startup ===")
    
    # Start outbox processor
    logger.info("Starting outbox processor...")
    processor = get_processor()
    processor_task = asyncio.create_task(processor.start())
    logger.info("Outbox processor started")
    
    # Start drift consumer
    logger.info("Starting drift consumer...")
    await asyncio.get_event_loop().run_in_executor(None, start_consumers)
    
    try:
        # Application is now running - yield control
        logger.info("=== Application Running ===")
        yield
    finally:
        # Shutdown phase
        logger.info("=== Application Shutdown ===")
        
        # Stop drift consumer first
        logger.info("Stopping drift consumer...")
        shutdown_event.set()
        await asyncio.get_event_loop().run_in_executor(None, stop_consumers)
        logger.info("Drift consumer stopped")
        
        # Stop outbox processor
        logger.info("Stopping outbox processor...")
        await processor.stop()
        if not processor_task.done():
            processor_task.cancel()
            try:
                await processor_task
            except asyncio.CancelledError:
                pass
        logger.info("Outbox processor stopped")

app = FastAPI(
    title="NTU FYP PEAR USER SERVICE",
    description="This is the user service api docs",
    version="1.0.0",
    servers=[],  # This removes the servers dropdown in Swagger UI
    lifespan=combined_lifespan,  # Use combined lifespan manager
)

# middleware to connect to the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Add your Next.js app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




def init_db():
    Base.metadata.create_all(bind=engine)
if __name__ == "__main__":
    init_db()

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
app.include_router(supervisor_router.router, prefix="/api/v1", tags=["supervisor"])
app.include_router(doctor_router.router, prefix="/api/v1", tags=["doctor"])
app.include_router(user_router.router, prefix="/api/v1", tags=["users"])
app.include_router(role_router.router, prefix="/api/v1", tags=["role"])
app.include_router(user_auth_router.router, prefix="/api/v1", tags=["authentication"])
app.include_router(email_router.router, prefix="/api/v1", tags=["email"])
app.include_router(verification_router.router, prefix="/api/v1", tags=["2FA"])
app.include_router(access_level_router.router, prefix="/api/v1", tags=["2FA"])
app.include_router(integrity_router.router, prefix="/api/v1/integrity", tags=["Integrity"])
app.include_router(internal_router.router, prefix="/api/v1", tags=["internal"])
@app.get("/")
def read_root():
    return {"message": "Welcome to the User API hello"} 


@app.get("/health")
def health_check():
    """Health check endpoint that includes consumer status"""
    global consumer_manager
    
    health_status = {
        "status": "healthy",
        "database": "connected",
        "outbox_processor": "unknown",
        "drift_consumer": "unknown"
    }
    
    # Check outbox processor status
    try:
        processor = get_processor()
        if processor.is_running():
            health_status["outbox_processor"] = "running"
            health_status["outbox_stats"] = processor.get_stats()
        else:
            health_status["outbox_processor"] = "stopped"
    except Exception as e:
        health_status["outbox_processor"] = f"error: {str(e)}"
    
    # Check drift consumer status
    if consumer_manager:
        try:
            status = consumer_manager.get_consumer_status()
            if status:
                # Check if any consumer has errors
                has_errors = any(s.startswith("Error") for s in status.values())
                health_status["drift_consumer"] = "error" if has_errors else "running"
                health_status["consumer_details"] = status
            else:
                health_status["drift_consumer"] = "not_registered"
        except Exception as e:
            health_status["drift_consumer"] = f"error: {str(e)}"
    else:
        health_status["drift_consumer"] = "not_started"
    
    # Determine overall status
    if (health_status["drift_consumer"] == "error" or 
        health_status["outbox_processor"] == "error"):
        health_status["status"] = "degraded"
    
    return health_status