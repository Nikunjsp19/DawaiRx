"""MongoDB connection pool for efficient connection reuse"""

from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
import logging
import threading

from src.persistence.config import MONGO_URI, MONGO_DB

logger = logging.getLogger(__name__)

# Global connection pool
_client: Optional[MongoClient] = None
_db: Optional[Database] = None
_lock = threading.Lock()


def get_mongo_client() -> MongoClient:
    """Get or create MongoDB client (singleton pattern with connection pooling)"""
    global _client
    
    if _client is not None:
        # Quick health check
        try:
            _client.server_info()
            return _client
        except Exception:
            logger.warning("Connection dead, reconnecting...")
            _client = None
    
    with _lock:
        if _client is None:
            try:
                logger.info(f"🔌 Connecting to MongoDB...")
                
                # Connection options - optimized for reliability
                connect_options = {
                    "serverSelectionTimeoutMS": 10000,
                    "socketTimeoutMS": 20000,
                    "connectTimeoutMS": 10000,
                    "maxPoolSize": 50,
                    "minPoolSize": 1,
                    "retryWrites": True,
                }
                
                # For MongoDB Atlas, bypass SSL certificate issues
                if "mongodb+srv" in MONGO_URI:
                    connect_options["tlsAllowInvalidCertificates"] = True
                    connect_options["tls"] = True
                
                _client = MongoClient(MONGO_URI, **connect_options)
                
                # Test connection
                _client.server_info()
                
                logger.info(f"✅ MongoDB connected: {MONGO_DB}")
                return _client
                
            except Exception as e:
                logger.error(f"❌ MongoDB connection failed: {e}")
                _client = None
                raise
    
    return _client


def get_database() -> Database:
    """Get database instance (reuses connection pool)"""
    global _db
    
    if _db is None:
        with _lock:
            if _db is None:
                client = get_mongo_client()
                _db = client[MONGO_DB]
    
    return _db


def close_connections():
    """Close all MongoDB connections (for cleanup)"""
    global _client, _db
    
    with _lock:
        if _client:
            try:
                _client.close()
            except Exception:
                pass
            _client = None
            _db = None
