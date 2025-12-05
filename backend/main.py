"""
Main FastAPI application for Nature42.

This module initializes the FastAPI app, configures middleware,
and sets up all routes including static file serving.

Implements Requirements 11.3, 11.4: Comprehensive error handling
"""

import os
import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv

from backend.api.command import router as command_router
from backend.api.state import router as state_router
from backend.api.share import router as share_router
from backend.utils.error_handling import (
    Nature42Error,
    format_error_response,
    logger
)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Nature42",
    description="AI-powered text adventure game",
    version="0.1.0"
)

# Include routers
app.include_router(command_router)
app.include_router(state_router)
app.include_router(share_router)


# Global Exception Handlers

@app.exception_handler(Nature42Error)
async def nature42_error_handler(request: Request, exc: Nature42Error):
    """
    Handle custom Nature42 errors with user-friendly messages.
    
    Implements Requirement 11.4: User-friendly error messages
    """
    logger.error(f"Nature42Error in {request.url.path}: {exc.message}")
    
    error_response = format_error_response(exc, user_friendly=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions with consistent formatting.
    """
    logger.warning(f"HTTP {exc.status_code} in {request.url.path}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_type": "HTTPException",
            "message": exc.detail
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors with helpful messages.
    """
    logger.warning(f"Validation error in {request.url.path}: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_type": "ValidationError",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unexpected exceptions.
    
    Implements Requirement 11.4: Graceful error handling
    """
    logger.error(f"Unexpected error in {request.url.path}: {type(exc).__name__}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_type": type(exc).__name__,
            "message": "An unexpected error occurred. Please try again."
        }
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Serve the main game page."""
    return FileResponse("static/index.html")


@app.get("/privacy")
async def privacy():
    """Serve the privacy policy page."""
    return FileResponse("static/privacy.html")


@app.get("/terms")
async def terms():
    """Serve the user agreement page."""
    return FileResponse("static/terms.html")


@app.get("/about")
async def about():
    """Serve the about page."""
    return FileResponse("static/about.html")


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint for AWS App Runner.
    
    Implements Requirement 11.3: Check Strands SDK availability
    
    Returns:
        JSON response with status including Strands health
    """
    from backend.utils.error_handling import check_strands_health
    
    # Check Strands health
    strands_health = await check_strands_health()
    
    # Overall health is healthy only if Strands is healthy
    overall_healthy = strands_health.get("healthy", False)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "healthy" if overall_healthy else "degraded",
            "service": "nature42",
            "version": "0.1.0",
            "dependencies": {
                "strands": strands_health
            }
        }
    )


@app.get("/api/info")
async def info():
    """
    Get API information.
    
    Returns:
        JSON response with API details
    """
    return JSONResponse(
        content={
            "name": "Nature42 API",
            "version": "0.1.0",
            "description": "AI-powered text adventure game backend",
            "endpoints": {
                "health": "/api/health",
                "command": "/api/command (POST)",
                "state": "/api/state (GET/POST/DELETE)"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
