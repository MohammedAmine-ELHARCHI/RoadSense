from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import severity
from app.config import settings
from app.models import predictor

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Severity Scoring Service...")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    
    # Load ML model
    print("📦 Loading severity prediction model...")
    model_loaded = predictor.load_model()
    if model_loaded:
        print("✅ XGBoost model loaded successfully!")
    else:
        print("⚠️  No trained model found, using heuristic fallback")
    
    print("✅ Severity Service started successfully!")
    yield
    # Shutdown
    print("🛑 Shutting down Severity Service...")

app = FastAPI(
    title="RoadSense Severity Scoring Service",
    description="ML service for road defect severity scoring using XGBoost",
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
app.include_router(severity.router, prefix="/api/v1/severity", tags=["Severity"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "score-gravite",
        "version": "1.0.0"
    }

@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "RoadSense Severity Scoring Service",
        "version": "1.0.0",
        "docs": "/docs"
    }
