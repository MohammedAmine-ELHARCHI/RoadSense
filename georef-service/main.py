import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import connection as database
from app.api import georef_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting GeoRef Service...")
    
    # Connect to database
    await database.connect()
    
    logger.info("✅ GeoRef Service ready!")
    yield
    
    # Cleanup
    await database.disconnect()
    logger.info("👋 GeoRef Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="RoadSense GeoRef Service",
    description="GPS Georeferencing and Spatial Analysis Service",
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

# Include routers
app.include_router(georef_routes.router, prefix="/api/v1/georef", tags=["georef"])


@app.get("/")
async def root():
    return {
        "service": "RoadSense GeoRef",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
