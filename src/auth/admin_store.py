"""Admin store - admins are stored in MongoDB (admins collection)"""

from pymongo.collection import Collection
import logging

from src.persistence.connection_pool import get_database

logger = logging.getLogger(__name__)


class AdminStore:
    """Store for checking admin status - admins stored in MongoDB (admins collection)"""

    def __init__(self):
        self._db = None
        self._admins_collection = None

    @property
    def db(self):
        if self._db is None:
            self._db = get_database()
        return self._db

    @property
    def admins_collection(self) -> Collection:
        if self._admins_collection is None:
            self._admins_collection = self.db["admins"]
            try:
                self._admins_collection.create_index("user_id", unique=True)
            except Exception as e:
                logger.debug(f"Index may already exist: {e}")
        return self._admins_collection

    def is_admin(self, user_id: str) -> bool:
        """Check if user_id is in the admins collection"""
        try:
            doc = self.admins_collection.find_one({"user_id": user_id})
            return doc is not None
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False

    def list_admin_user_ids(self):
        """Return set of all user_ids that are admins (for filtering user lists)."""
        try:
            cursor = self.admins_collection.find({}, {"user_id": 1})
            return {doc.get("user_id") for doc in cursor if doc.get("user_id")}
        except Exception as e:
            logger.error(f"Error listing admin user ids: {e}")
            return set()
