"""
The Accountant Backend API - Main Application
"""
import logging
import os
import sys
import traceback
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.api.v1 import api_router
from app.database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Personal finance management backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    redirect_slashes=False
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that:
    - In DEBUG mode: returns detailed error info for development
    - In PRODUCTION mode: returns generic error message, logs details server-side
    """
    # Generate a unique error ID for tracking
    error_id = str(uuid.uuid4())[:8]

    # Always log the full error on the server
    logger.error(
        f"[ERROR_ID: {error_id}] Unhandled exception on {request.method} {request.url.path}",
        exc_info=True
    )

    if settings.DEBUG:
        # Development: return detailed error for debugging
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "error_id": error_id,
                "type": type(exc).__name__,
                "path": str(request.url.path),
                "traceback": traceback.format_exc()
            }
        )
    else:
        # Production: return generic error, hide internal details
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred. Please try again later.",
                "error_id": error_id
            }
        )


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("=" * 70)
    print("[STARTUP] Starting The Accountant API...")
    print("=" * 70)

    # Check for required configuration files
    print("[CHECK] Checking required configuration files...")

    required_files = {
        ".env": ".env file (contains database and API configuration)",
    }

    # Firebase credentials are optional for development
    if settings.FIREBASE_AUTH_ENABLED:
        required_files[settings.FCM_CREDENTIALS_PATH] = "Firebase Admin SDK credentials (required for Google Sign-In)"

    missing_files = []
    for file_path, description in required_files.items():
        if not os.path.exists(file_path):
            missing_files.append(f"  [WARNING] {file_path} - {description}")
            print(f"[WARNING] Missing: {file_path}")
        else:
            print(f"[OK] Found: {file_path}")

    if ".env" in [f for f, _ in required_files.items() if not os.path.exists(f)]:
        error_msg = "\n\n" + "="*70 + "\n"
        error_msg += "[ERROR] CONFIGURATION ERROR: .env file is missing!\n"
        error_msg += "="*70 + "\n\n"
        error_msg += "Please create a .env file based on .env.example\n"
        error_msg += "="*70 + "\n"

        print(error_msg, file=sys.stderr)
        sys.exit(1)

    print(f"[DATABASE] {settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}")
    print(f"[DEBUG] Debug mode: {settings.DEBUG}")

    # Initialize database tables
    try:
        init_db()
        print("[OK] Database initialized successfully")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        sys.exit(1)

    print("=" * 70)
    print(f"[API] Running at: http://{settings.HOST}:{settings.PORT}")
    print(f"[DOCS] API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"[DOCS] ReDoc: http://{settings.HOST}:{settings.PORT}/redoc")
    print("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("[SHUTDOWN] Shutting down The Accountant API...")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "the-accountant-api",
        "version": "1.0.0"
    }


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to The Accountant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "Firebase Auth + Google Sign-In",
            "Email/Password Authentication",
            "JWT Token Management",
            "Account Linking"
        ]
    }


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="The Accountant Backend API")
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload on file changes"
    )
    args = parser.parse_args()

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=not args.no_reload
    )
