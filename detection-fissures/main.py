from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import uvicorn
import os
from contextlib import asynccontextmanager

from app.api import detection, models_info
from app.database.connection import init_db, close_db
from app.config import settings
from app.models.detector import detector
from app.storage.minio_client import storage

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Detection Service...")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🗄️  Database: {settings.POSTGRES_HOST}")
    print(f"💾 MinIO: {settings.MINIO_ENDPOINT}")
    
    # Initialize database
    await init_db()
    
    # Load ML models
    print("🤖 Loading ML models...")
    await detector.load_models()
    print("✅ ML models loaded successfully!")
    
    # Connect to MinIO
    await storage.connect()
    print("✅ MinIO storage connected!")
    
    print("✅ Detection Service started successfully!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Detection Service...")
    await close_db()
    print("✅ Detection Service stopped")

# Create FastAPI app
app = FastAPI(
    title="RoadSense Detection Service",
    description="ML/DL service for road defect detection using YOLOv8 and Mask R-CNN",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(detection.router, prefix="/api/v1/detection", tags=["Detection"])
app.include_router(models_info.router, prefix="/api/v1/models", tags=["Models"])

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "detection-fissures",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information"""
    return {
        "service": "RoadSense Detection Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True if settings.ENVIRONMENT == "development" else False
    )
