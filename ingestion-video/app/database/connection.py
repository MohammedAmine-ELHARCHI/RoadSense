"""Database connection manager"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.engine = None
        self.async_session = None
    
    async def connect(self):
        """Connect to database"""
        logger.info(f"Connecting to database...")
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        logger.info("✅ Database connected")
    
    async def disconnect(self):
        """Disconnect from database"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database disconnected")
    
    def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.async_session:
            raise RuntimeError("Database not connected")
        return self.async_session()

database = Database()
