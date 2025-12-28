# Import the logging module for application logging
import logging
# Import asynccontextmanager for managing async application lifecycle
from contextlib import asynccontextmanager
# Import FastAPI framework for building the REST API
from fastapi import FastAPI
# Import CORS middleware to handle Cross-Origin Resource Sharing
from fastapi.middleware.cors import CORSMiddleware

# Import application settings from the core configuration module
from app.core.config import settings
# Import database connection module for managing database lifecycle
from app.database import connection
# Import the priority routes API endpoints
from app.api import priority_routes

# Configure the logging system for the application
logging.basicConfig(
    # Set log level to INFO to capture informational messages and above
    level=logging.INFO,
    # Define format string for log messages with timestamp, logger name, level and message
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Create a logger instance for this module
# Create a logger instance for this module
logger = logging.getLogger(__name__)


# Define async context manager decorator for application lifespan events
@asynccontextmanager
# Define lifespan function that handles startup and shutdown of the FastAPI app
async def lifespan(app: FastAPI):
    # """Lifespan context manager for startup and shutdown events."""
    """
    Manages the application lifecycle with async context manager.
    Handles startup tasks (database connection) and cleanup on shutdown.
    """
    # Startup section - executed when application starts
    # Log that the Priorisation Service is starting
    logger.info("🚀 Starting Priorisation Service...")
    # Establish connection to the database
    await connection.connect()
    # Log successful startup
    logger.info("✅ Priorisation Service ready!")
    
    # Yield control back to FastAPI - app runs here
    yield
    
    # Shutdown section - executed when application stops
    # Log shutdown message
    logger.info("Shutting down Priorisation Service...")
    # Close database connection and cleanup resources
    await connection.disconnect()


# Create the main FastAPI application instance
app = FastAPI(
    # Set service title from configuration settings
    title=settings.SERVICE_NAME,
    # Set API version from configuration settings
    version=settings.SERVICE_VERSION,
    # Attach the lifespan context manager for handling startup/shutdown
    lifespan=lifespan
)

# Add CORS (Cross-Origin Resource Sharing) middleware to the application
app.add_middleware(
    # Use the CORSMiddleware class
    CORSMiddleware,
    # Allow requests from any origin (use specific origins in production)
    allow_origins=["*"],
    # Allow cookies and authentication headers in cross-origin requests
    allow_credentials=True,
    # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],
    # Allow all HTTP headers in requests
    allow_headers=["*"],
)

# Include the priority routes router and mount it to the application
app.include_router(priority_routes.router, prefix="/api/v1/priority", tags=["priority"])


# Define root endpoint that returns basic service information
@app.get("/")
# Async function to handle root path requests
async def root():
    # Return a dictionary with service metadata
    return {
        # Service name from settings
        "service": settings.SERVICE_NAME,
        # Service version from settings
        "version": settings.SERVICE_VERSION,
        # Current status indicator
        "status": "running"
    }


# Define health check endpoint for monitoring service status
@app.get("/health")
# Async function to handle health check requests
async def health_check():
    # Return simple status indicating service is healthy
    return {"status": "healthy"}
