# Import logging module for database connection logging
import logging
# Import SQLAlchemy async components for asynchronous database operations
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
# Import text function for raw SQL execution
from sqlalchemy import text
# Import application settings
from app.core.config import settings

# Create logger instance for this module
logger = logging.getLogger(__name__)

# Create async database engine with connection pooling
engine = create_async_engine(
    # Database URL from settings (e.g., postgresql+asyncpg://user:pass@host/db)
    settings.DATABASE_URL,
    # Disable SQL query echoing to console (set True for debugging)
    echo=False,
    # Enable connection health checks before using from pool
    pool_pre_ping=True,
    # Number of connections to keep open in the pool
    pool_size=5,
    # Maximum number of connections that can be created beyond pool_size
    max_overflow=10
)

# Create async session factory for creating database sessions
AsyncSessionLocal = async_sessionmaker(
    # Use the engine created above
    engine,
    # Specify the async session class to use
    class_=AsyncSession,
    # Don't expire objects after commit (useful for accessing committed objects)
    expire_on_commit=False
)


# Async function to establish database connection on startup
async def connect():
    # """Connect to database"""
    """Establish connection to database and verify it's working"""
    # Log connection attempt
    logger.info("Connecting to database...")
    # Try-except block for connection error handling
    try:
        # Open a connection and execute a simple query to test
        async with engine.begin() as conn:
            # Execute simple SELECT 1 query to verify connection
            await conn.execute(text("SELECT 1"))
        # Log successful connection
        logger.info("✅ Database connected")
    # Catch any connection errors
    except Exception as e:
        # Log error details
        logger.error(f"Database connection failed: {e}")
        # Re-raise exception to prevent service from starting with bad DB
        raise


# Async function to close database connection on shutdown
async def disconnect():
    # """Disconnect from database"""
    """Close all database connections and cleanup resources"""
    # Dispose of the engine and close all connections
    await engine.dispose()
    # Log disconnection
    logger.info("Database disconnected")


# Dependency function that provides database sessions to route handlers
async def get_db():
    # """Dependency for getting database session"""
    """FastAPI dependency that yields a database session for each request"""
    # Create a new async session from the session factory
    async with AsyncSessionLocal() as session:
        # Try-finally block to ensure session cleanup
        try:
            # Yield session to the route handler
            yield session
        # Always execute finally block for cleanup
        finally:
            # Close the session after request completes
            await session.close()
