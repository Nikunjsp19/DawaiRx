#!/usr/bin/env python3
"""Reset user password in MongoDB"""

from src.auth.user_store import UserStore
from src.auth.utils import hash_password

USER_ID = "nikunjpatel19081999@gmail.com"
NEW_PASSWORD = "Niks@1908"

def reset_password():
    """Reset user password"""
    user_store = UserStore()
    
    # Check if user exists
    user = user_store.get_user_by_id(USER_ID)
    if user:
        print(f"✅ User found: {USER_ID}")
        # Update password
        from src.persistence.connection_pool import get_database
        db = get_database()
        users_collection = db["users"]
        
        password_hash = hash_password(NEW_PASSWORD)
        result = users_collection.update_one(
            {"user_id": USER_ID},
            {"$set": {"password_hash": password_hash}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Password updated successfully")
        else:
            print(f"⚠️ Password was not updated (may be the same)")
    else:
        print(f"⚠️ User not found, creating new user...")
        from src.auth.models import UserCreate
        user_data = UserCreate(
            user_id=USER_ID,
            email=USER_ID,
            password=NEW_PASSWORD
        )
        user = user_store.create_user(user_data)
        print(f"✅ User created: {USER_ID}")

if __name__ == "__main__":
    reset_password()

