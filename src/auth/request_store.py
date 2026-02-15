"""Registration request store for MongoDB"""

from typing import Optional, List
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, DuplicateKeyError
from datetime import datetime
import logging

from src.persistence.connection_pool import get_database
from src.auth.models import RegistrationRequest, RegistrationRequestDocument

logger = logging.getLogger(__name__)


class RegistrationRequestStore:
    """Store for managing registration requests in MongoDB"""
    
    def __init__(self):
        """Initialize registration request store (uses shared connection pool)"""
        # Don't connect immediately - lazy initialization
        self._db = None
        self._requests_collection = None
    
    @property
    def db(self):
        """Lazy database access - only connects when needed"""
        if self._db is None:
            self._db = get_database()
        return self._db
    
    @property
    def requests_collection(self) -> Collection:
        """Lazy collection access - only connects when needed"""
        if self._requests_collection is None:
            self._requests_collection = self.db["registration_requests"]
            # Create indexes - only when first accessed
            try:
                self._requests_collection.create_index("user_id")
                self._requests_collection.create_index("status")
                self._requests_collection.create_index("requested_at")
            except Exception as e:
                logger.debug(f"Indexes may already exist: {e}")
        return self._requests_collection
    
    def create_request(self, request_data: RegistrationRequest) -> RegistrationRequestDocument:
        """Create a new registration request"""
        try:
            # Check if request already exists for this user_id
            existing = self.requests_collection.find_one({"user_id": request_data.user_id})
            if existing:
                existing_doc = RegistrationRequestDocument(**existing)
                if existing_doc.status == "pending":
                    raise ValueError(f"A pending registration request already exists for '{request_data.user_id}'")
                elif existing_doc.status == "approved":
                    raise ValueError(f"Registration request for '{request_data.user_id}' has already been approved. You can now register.")
                # If rejected, allow new request
            
            # Check if user already exists
            from src.auth.user_store import UserStore
            user_store = UserStore()
            if user_store.get_user_by_id(request_data.user_id):
                raise ValueError(f"User '{request_data.user_id}' already exists. Please login instead.")
            
            # Create request document
            now = datetime.utcnow()
            request_doc = {
                "user_id": request_data.user_id,
                "email": request_data.email,
                "reason": request_data.reason,
                "company": request_data.company,
                "status": "pending",
                "requested_at": now,
                "reviewed_at": None,
                "reviewed_by": None,
                "admin_notes": None
            }
            
            result = self.requests_collection.insert_one(request_doc)
            request_doc["_id"] = result.inserted_id
            
            return RegistrationRequestDocument(**request_doc)
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating registration request: {e}")
            raise
    
    def get_request_by_user_id(self, user_id: str) -> Optional[RegistrationRequestDocument]:
        """Get registration request by user_id"""
        try:
            request_doc = self.requests_collection.find_one(
                {"user_id": user_id},
                sort=[("requested_at", -1)]  # Get most recent
            )
            if request_doc:
                return RegistrationRequestDocument(**request_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting registration request: {e}")
            return None
    
    def get_pending_requests(self) -> List[RegistrationRequestDocument]:
        """Get all pending registration requests"""
        try:
            requests = self.requests_collection.find(
                {"status": "pending"}
            ).sort("requested_at", 1)  # Oldest first
            
            return [RegistrationRequestDocument(**req) for req in requests]
        except Exception as e:
            logger.error(f"Error getting pending requests: {e}")
            return []
    
    def get_all_requests(self, limit: int = 100, skip: int = 0) -> List[RegistrationRequestDocument]:
        """Get all registration requests (for admin) with optional pagination."""
        try:
            cursor = self.requests_collection.find().sort("requested_at", -1).skip(skip).limit(limit)
            return [RegistrationRequestDocument(**req) for req in cursor]
        except Exception as e:
            logger.error(f"Error getting all requests: {e}")
            return []

    def count_all_requests(self) -> int:
        """Total count of all registration requests."""
        try:
            return self.requests_collection.count_documents({})
        except Exception as e:
            logger.error(f"Error counting requests: {e}")
            return 0

    def get_requests_by_status(self, status: str, limit: int = 100, skip: int = 0) -> List[RegistrationRequestDocument]:
        """Get registration requests by status with optional pagination."""
        try:
            if status not in ["pending", "approved", "rejected"]:
                logger.warning(f"Invalid status filter: {status}")
                return []
            cursor = self.requests_collection.find({"status": status}).sort("requested_at", -1).skip(skip).limit(limit)
            return [RegistrationRequestDocument(**req) for req in cursor]
        except Exception as e:
            logger.error(f"Error getting requests by status: {e}")
            return []

    def count_requests_by_status(self, status: str) -> int:
        """Total count of requests for a given status."""
        try:
            return self.requests_collection.count_documents({"status": status})
        except Exception as e:
            logger.error(f"Error counting requests by status: {e}")
            return 0
    
    def approve_request(self, user_id: str, admin_user_id: str, admin_notes: Optional[str] = None) -> bool:
        """Approve a registration request"""
        try:
            now = datetime.utcnow()
            result = self.requests_collection.update_one(
                {"user_id": user_id, "status": "pending"},
                {
                    "$set": {
                        "status": "approved",
                        "reviewed_at": now,
                        "reviewed_by": admin_user_id,
                        "admin_notes": admin_notes
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error approving request: {e}")
            return False
    
    def reject_request(self, user_id: str, admin_user_id: str, admin_notes: Optional[str] = None) -> bool:
        """Reject a registration request"""
        try:
            now = datetime.utcnow()
            result = self.requests_collection.update_one(
                {"user_id": user_id, "status": "pending"},
                {
                    "$set": {
                        "status": "rejected",
                        "reviewed_at": now,
                        "reviewed_by": admin_user_id,
                        "admin_notes": admin_notes
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error rejecting request: {e}")
            return False
    
    def is_approved(self, user_id: str) -> bool:
        """Check if a user_id has an approved registration request"""
        request = self.get_request_by_user_id(user_id)
        return request is not None and request.status == "approved"
