"""User store for MongoDB user management"""

from typing import Optional, List, Dict, Any
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
        # Don't connect immediately - lazy initialization
        self._db = None
        self._users_collection = None
    
    @property
    def db(self):
        """Lazy database access - only connects when needed"""
        if self._db is None:
            self._db = get_database()
        return self._db
    
    @property
    def users_collection(self) -> Collection:
        """Lazy collection access - only connects when needed"""
        if self._users_collection is None:
            self._users_collection = self.db["users"]
            # Create unique index on user_id (idempotent) - only when first accessed
            try:
                self._users_collection.create_index("user_id", unique=True)
            except Exception as e:
                logger.debug(f"Index may already exist: {e}")
        return self._users_collection
    
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
    
    def list_all_users(self) -> List[Dict[str, Any]]:
        """List all users (admin only). Returns list of { user_id, email, disabled } (no password)."""
        try:
            cursor = self.users_collection.find({}, {"user_id": 1, "email": 1, "disabled": 1, "_id": 0})
            return [
                {"user_id": doc.get("user_id") or "", "email": doc.get("email") or "", "disabled": doc.get("disabled", False)}
                for doc in cursor
            ]
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

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
        """Authenticate a user by user_id and password. Disabled users cannot log in."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        if getattr(user, "disabled", False):
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
            return None

    def set_user_disabled(self, user_id: str, disabled: bool) -> bool:
        """Set user disabled state (admin only). Returns True if updated."""
        try:
            from datetime import datetime
            result = self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"disabled": disabled, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0 or result.matched_count > 0
        except Exception as e:
            logger.error(f"Error setting user disabled: {e}")
            return False
            raise

