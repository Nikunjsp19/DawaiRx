"""User store for MongoDB user management"""

from typing import Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, DuplicateKeyError
import logging

from src.persistence.config import MONGO_URI, MONGO_DB
from src.auth.models import UserDocument, UserCreate
from src.auth.utils import hash_password, verify_password
from src.persistence.connection_pool import get_database

logger = logging.getLogger(__name__)


class UserStore:
    """Store for managing users in MongoDB (uses connection pool)"""
    
    def __init__(self, mongo_uri: Optional[str] = None, db_name: Optional[str] = None):
        """
        Initialize user store (uses shared connection pool).
        
        Args:
            mongo_uri: MongoDB connection URI (ignored - uses pool)
            db_name: Database name (ignored - uses pool)
        """
        # Use connection pool instead of creating new connections
        self.db = get_database()
        self.users_collection: Collection = self.db["users"]
        
        # Create unique index on user_id (idempotent)
        try:
            self.users_collection.create_index("user_id", unique=True)
        except Exception as e:
            logger.debug(f"Index may already exist: {e}")
    
    def close(self):
        """Close MongoDB connection (no-op with connection pool)"""
        # Don't close - connection pool manages connections
        pass
    
    def create_user(self, user_data: UserCreate) -> UserDocument:
        """Create a new user"""
        try:
            # Check if user already exists
            existing = self.users_collection.find_one({"user_id": user_data.user_id})
            if existing:
                raise ValueError(f"User with user_id '{user_data.user_id}' already exists")
            
            # Hash password
            password_hash = hash_password(user_data.password)
            
            # Create user document
            from datetime import datetime
            now = datetime.utcnow()
            user_doc = {
                "user_id": user_data.user_id,
                "email": user_data.email,
                "password_hash": password_hash,
                "created_at": now,
                "updated_at": now
            }
            
            result = self.users_collection.insert_one(user_doc)
            user_doc["_id"] = result.inserted_id
            
            return UserDocument(**user_doc)
        except DuplicateKeyError:
            raise ValueError(f"User with user_id '{user_data.user_id}' already exists")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_user_by_id(self, user_id: str) -> Optional[UserDocument]:
        """Get user by user_id"""
        try:
            user_doc = self.users_collection.find_one({"user_id": user_id})
            if user_doc:
                return UserDocument(**user_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def authenticate_user(self, user_id: str, password: str) -> Optional[UserDocument]:
        """Authenticate a user by user_id and password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        if verify_password(password, user.password_hash):
            return user
        return None
    
    def update_user(self, user_id: str, email: Optional[str] = None, new_password: Optional[str] = None) -> Optional[UserDocument]:
        """Update user email and/or password"""
        try:
            from datetime import datetime
            
            update_data = {"updated_at": datetime.utcnow()}
            
            if email is not None:
                update_data["email"] = email
            
            if new_password is not None:
                update_data["password_hash"] = hash_password(new_password)
            
            if not update_data:
                # Nothing to update
                return self.get_user_by_id(user_id)
            
            result = self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0 or result.matched_count > 0:
                return self.get_user_by_id(user_id)
            return None
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise

