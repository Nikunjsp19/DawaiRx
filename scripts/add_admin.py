#!/usr/bin/env python3
"""Create admin user and add to MongoDB admins collection.
   Run from project root: python scripts/add_admin.py
   Or: python -m scripts.add_admin (from project root)
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.persistence.connection_pool import get_database
from src.auth.utils import hash_password

ADMIN_USER_ID = "Admin@DawaiRx.us"
ADMIN_PASSWORD = "Niks@1908"


def main():
    db = get_database()
    users = db["users"]
    admins = db["admins"]

    # 1. Ensure user exists in users collection (create if not)
    existing_user = users.find_one({"user_id": ADMIN_USER_ID})
    if not existing_user:
        password_hash = hash_password(ADMIN_PASSWORD)
        now = datetime.utcnow()
        users.insert_one({
            "user_id": ADMIN_USER_ID,
            "email": None,
            "password_hash": password_hash,
            "created_at": now,
            "updated_at": now,
        })
        print(f"Created user '{ADMIN_USER_ID}' in users collection.")
    else:
        print(f"User '{ADMIN_USER_ID}' already exists in users collection.")

    # 2. Add to admins collection if not already admin
    existing_admin = admins.find_one({"user_id": ADMIN_USER_ID})
    if existing_admin:
        print(f"Admin '{ADMIN_USER_ID}' already in admins collection.")
        return 0

    admins.insert_one({"user_id": ADMIN_USER_ID})
    print(f"Added '{ADMIN_USER_ID}' to admins collection.")
    print("Done. You can log in with User ID: Admin@DawaiRx.us and the given password.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
