"""
IngestionVideo Service - Video Processing Microservice
Extracts frames from uploaded videos for defect detection
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.database.connection import database
from app.storage.minio_client import storage
from app.api import video_routes

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting IngestionVideo Service...")
    await database.connect()
    await storage.connect()
    logger.info("✅ IngestionVideo Service ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down IngestionVideo Service...")
    await database.disconnect()
    await storage.disconnect()

app = FastAPI(
    title="IngestionVideo Service",
    description="Video processing and frame extraction for RoadSense",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(video_routes.router, prefix="/api/v1/video", tags=["Video"])

@app.get("/")
async def root():
    return {
        "service": "IngestionVideo",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
