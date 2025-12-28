# Import FastAPI core components for building the REST API
from fastapi import FastAPI, UploadFile, File, HTTPException, status
# Import CORS middleware for cross-origin requests
from fastapi.middleware.cors import CORSMiddleware
# Import JSON response handler
from fastapi.responses import JSONResponse
# Import type hints for better code documentation
from typing import List, Optional
# Import uvicorn ASGI server
import uvicorn
# Import os module for environment variables and file operations
import os
# Import asynccontextmanager for application lifecycle management
from contextlib import asynccontextmanager

# Import detection and models_info API routers
from app.api import detection, models_info
# Import database initialization and cleanup functions
from app.database.connection import init_db, close_db
# Import application configuration settings
from app.config import settings
# Import ML detector instance
from app.models.detector import detector
# Import MinIO storage client
from app.storage.minio_client import storage

# Lifespan context manager for startup/shutdown events
# Define async context manager for app lifecycle
@asynccontextmanager
# Define lifespan function with FastAPI app parameter
async def lifespan(app: FastAPI):
    # Startup section - executed when service starts
    # Print startup message
    print("🚀 Starting Detection Service...")
    # Display current environment (development/production)
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    # Display database host connection
    print(f"🗄️  Database: {settings.POSTGRES_HOST}")
    # Display MinIO storage endpoint
    print(f"💾 MinIO: {settings.MINIO_ENDPOINT}")
    
    # Initialize database connection and create tables if needed
    await init_db()
    
    # Load ML models section
    # Print model loading message
    print("🤖 Loading ML models...")
    # Load YOLO and other detection models into memory
    await detector.load_models()
    # Confirm models loaded successfully
    print("✅ ML models loaded successfully!")
    
    # Connect to MinIO object storage
    await storage.connect()
    # Confirm MinIO connection established
    print("✅ MinIO storage connected!")
    
    # Print final startup success message
    print("✅ Detection Service started successfully!")
    
    # Yield control to FastAPI - app runs here
    yield
    
    # Shutdown section - executed when service stops
    # Print shutdown message
    print("🛑 Shutting down Detection Service...")
    # Close all database connections
    await close_db()
    # Print shutdown complete message
    # Print shutdown complete message
    print("✅ Detection Service stopped")

# Create FastAPI application instance
app = FastAPI(
    # Set service title for API documentation
    title="RoadSense Detection Service",
    # Set service description
    description="ML/DL service for road defect detection using YOLOv8 and Mask R-CNN",
    # Set API version
    version="1.0.0",
    # Attach lifespan context manager
    lifespan=lifespan
)

# CORS middleware configuration
# Add CORS middleware to handle cross-origin requests
app.add_middleware(
    # Use CORSMiddleware class
    CORSMiddleware,
    # Allow requests from any origin (configure for production)
    allow_origins=["*"],  # Configure appropriately for production
    # Allow credentials in requests
    allow_credentials=True,
    # Allow all HTTP methods
    allow_methods=["*"],
    # Allow all headers
    allow_headers=["*"],
)

# Include routers section
# Include detection router with prefix and tag
app.include_router(detection.router, prefix="/api/v1/detection", tags=["Detection"])
# Include models info router with prefix and tag
app.include_router(models_info.router, prefix="/api/v1/models", tags=["Models"])

# Health check endpoint for monitoring
@app.get("/health", tags=["Health"])
# Async function for health check
async def health_check():
    # """Health check endpoint"""
    """Health check endpoint for service monitoring and status verification"""
    # Return health status dictionary
    return {
        # Service status indicator
        "status": "healthy",
        # Service name
        "service": "detection-fissures",
        # Service version number
        "version": "1.0.0"
    }

# Root endpoint providing service information
@app.get("/", tags=["Root"])
# Async function for root endpoint
async def root():
    # """Root endpoint with service information"""
    """Root endpoint providing service metadata and navigation links"""
    # Return service information dictionary
    return {
        # Service name
        "service": "RoadSense Detection Service",
        # Service version
        "version": "1.0.0",
        # Link to API documentation
        "docs": "/docs",
        # Link to health check endpoint
        "health": "/health"
    }

# Main entry point when running directly
if __name__ == "__main__":
    # Run uvicorn ASGI server
    uvicorn.run(
        # Module and app instance path
        "main:app",
        # Listen on all network interfaces
        host="0.0.0.0",
        # Port number for the service
        port=8001,
        # Enable auto-reload in development, disable in production
        reload=True if settings.ENVIRONMENT == "development" else False
    )
