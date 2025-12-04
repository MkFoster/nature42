"""
Main FastAPI application for Nature42.

This module initializes the FastAPI app, configures middleware,
and sets up all routes including static file serving.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv

from backend.api.command import router as command_router
from backend.api.state import router as state_router

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
    
    Returns:
        JSON response with status
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "nature42",
            "version": "0.1.0"
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
