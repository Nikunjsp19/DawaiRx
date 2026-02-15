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
        # Quick health check (non-blocking, don't wait)
        try:
            _client.server_info()
            return _client
        except Exception:
            logger.warning("Connection dead, reconnecting...")
            _client = None
    
    with _lock:
        if _client is None:
            try:
                logger.info(f"🔌 Creating MongoDB client (lazy connection)...")
                
                # Connection options - optimized for instant startup
                # Set very short timeouts and don't connect immediately
                connect_options = {
                    "serverSelectionTimeoutMS": 5000,  # Fail fast if MongoDB unavailable
                    "socketTimeoutMS": 10000,
                    "connectTimeoutMS": 5000,
                    "maxPoolSize": 50,
                    "minPoolSize": 0,  # Don't create any connections on startup
                    "retryWrites": True,
                }
                
                # For MongoDB Atlas, bypass SSL certificate issues
                if "mongodb+srv" in MONGO_URI:
                    connect_options["tlsAllowInvalidCertificates"] = True
                    connect_options["tls"] = True
                
                _client = MongoClient(MONGO_URI, **connect_options)
                
                # Don't test connection - let it connect lazily on first actual operation
                logger.info(f"✅ MongoDB client created (will connect on first operation): {MONGO_DB}")
                return _client
                
            except Exception as e:
                logger.error(f"❌ MongoDB client creation failed: {e}")
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
