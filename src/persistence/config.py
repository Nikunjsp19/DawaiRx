"""MongoDB connection configuration"""

import os
from typing import Optional

# MongoDB connection - supports both local and cloud (MongoDB Atlas)
# Priority: MONGO_URI env var > individual settings > default cloud URL

# Check for full connection URI first (for MongoDB Atlas or custom setups)
# Fallback hardcoded URI for testing.
MONGO_URI: Optional[str] = os.getenv(
    "MONGO_URI",
    "mongodb+srv://user:user@temp.tzhzodo.mongodb.net/DawaiRx?retryWrites=true&w=majority",
)

if not MONGO_URI:
    # Check for individual settings (for local MongoDB)
    MONGO_HOST: Optional[str] = os.getenv("MONGO_HOST", None)
    
    if MONGO_HOST:
        # Build local connection string from individual settings
        MONGO_PORT: int = int(os.getenv("MONGO_PORT", "27017"))
        MONGO_USER: Optional[str] = os.getenv("MONGO_USER", None)
        MONGO_PASSWORD: Optional[str] = os.getenv("MONGO_PASSWORD", None)
        MONGO_DB: str = os.getenv("MONGO_DB", "dawai_rx")
        
        if MONGO_USER and MONGO_PASSWORD:
            MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"
        else:
            MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"
    else:
        # Default to cloud MongoDB Atlas connection
        MONGO_URI = "mongodb+srv://user:user@temp.tzhzodo.mongodb.net/DawaiRx?retryWrites=true&w=majority"

# Extract database name
# Try to get from env var, otherwise extract from URI, otherwise use default
MONGO_DB: str = os.getenv("MONGO_DB", None)
if not MONGO_DB:
    # Try to extract from URI
    if "/" in MONGO_URI:
        db_part = MONGO_URI.split("/")[-1].split("?")[0]
        if db_part and db_part not in ["", "admin"]:
            MONGO_DB = db_part
        else:
            MONGO_DB = "DawaiRx"
    else:
        MONGO_DB = "DawaiRx"
