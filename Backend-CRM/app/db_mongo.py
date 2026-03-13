"""
MongoDB database connection and client setup.
This module handles MongoDB connections for conversation, message, and thread data.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# MongoDB client singleton
_mongo_client: AsyncIOMotorClient = None
_mongo_db = None


async def get_mongo_client() -> AsyncIOMotorClient:
    """Get or create MongoDB client singleton. Lazy initialization - only connects when needed."""
    global _mongo_client
    if _mongo_client is None:
        logger.info(f"[MONGO] Connecting to MongoDB at {settings.mongodb_uri}")
        # Add connection timeout and server selection timeout to prevent hanging
        _mongo_client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=15000,  # 15 seconds - more time for DNS resolution
            connectTimeoutMS=10000,  # 10 second connection timeout
            socketTimeoutMS=30000,  # 30 second socket timeout
            maxPoolSize=10,  # Limit connection pool
            minPoolSize=1
        )
        # Test connection with timeout - but don't block if it fails
        try:
            import asyncio
            await asyncio.wait_for(_mongo_client.admin.command('ping'), timeout=15.0)
            logger.info("[MONGO] MongoDB connection successful")
        except asyncio.TimeoutError:
            logger.warning("[MONGO] MongoDB connection timed out - will retry on use")
            # Keep client but mark as potentially unavailable
        except Exception as e:
            logger.warning(f"[MONGO] MongoDB connection failed: {e} - will retry on use")
            # Don't raise - allow app to continue
    return _mongo_client


async def get_mongo_db():
    """Get MongoDB database instance."""
    global _mongo_db
    if _mongo_db is None:
        client = await get_mongo_client()
        _mongo_db = client[settings.mongodb_database]
    return _mongo_db


async def close_mongo_client():
    """Close MongoDB client connection."""
    global _mongo_client, _mongo_db
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
        logger.info("[MONGO] MongoDB connection closed")

