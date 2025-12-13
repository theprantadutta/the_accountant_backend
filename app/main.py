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

    missing_files = []

    # Check .env file
    if not os.path.exists(".env"):
        missing_files.append((".env", "Environment configuration file"))
        print("[ERROR] Missing: .env")
    else:
        print("[OK] Found: .env")

    # Check Firebase credentials (required for Google Sign-In)
    firebase_creds_path = settings.FCM_CREDENTIALS_PATH
    if not os.path.exists(firebase_creds_path):
        missing_files.append((firebase_creds_path, "Firebase Admin SDK credentials (required for Google Sign-In)"))
        print(f"[ERROR] Missing: {firebase_creds_path}")
    else:
        print(f"[OK] Found: {firebase_creds_path}")

    # Exit if any required files are missing
    if missing_files:
        print("\n" + "=" * 70, file=sys.stderr)
        print("[FATAL] CONFIGURATION ERROR: Required files are missing!", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        for file_path, description in missing_files:
            print(f"  - {file_path}: {description}", file=sys.stderr)
        print("\nPlease ensure all required files exist:", file=sys.stderr)
        print("  1. Copy .env.example to .env and configure it", file=sys.stderr)
        print("  2. Download firebase-admin-sdk.json from Firebase Console:", file=sys.stderr)
        print("     Project Settings > Service Accounts > Generate new private key", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
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
