import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.database import connection
from app.api import export_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting ExportSIG Service...")
    
    # Create exports directory if it doesn't exist
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)
    
    await connection.connect()
    logger.info("✅ ExportSIG Service ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ExportSIG Service...")
    await connection.disconnect()


# Create FastAPI app
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount exports directory for file downloads
if os.path.exists(settings.EXPORT_DIR):
    app.mount("/exports", StaticFiles(directory=settings.EXPORT_DIR), name="exports")

# Include API routes
app.include_router(export_routes.router, prefix="/api/v1/export", tags=["export"])


@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
