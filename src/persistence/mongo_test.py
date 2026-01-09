"""Test MongoDB connection"""

import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from src.persistence.config import MONGO_URI, MONGO_DB


def test_connection() -> bool:
    """Test MongoDB connection and return True if successful."""
    try:
        # For MongoDB Atlas (mongodb+srv), increase timeout
        timeout = 10000 if "mongodb+srv" in MONGO_URI else 5000
        connect_options = {"serverSelectionTimeoutMS": timeout}
        
        # Handle SSL certificate issues on macOS
        if "mongodb+srv" in MONGO_URI:
            try:
                client = MongoClient(MONGO_URI, **connect_options)
                client.server_info()
            except Exception as ssl_error:
                if "CERTIFICATE_VERIFY_FAILED" in str(ssl_error):
                    print("⚠️  SSL certificate verification failed, trying with tlsAllowInvalidCertificates...")
                    connect_options["tlsAllowInvalidCertificates"] = True
                    client = MongoClient(MONGO_URI, **connect_options)
                    client.server_info()
                else:
                    raise
        else:
            client = MongoClient(MONGO_URI, **connect_options)
            client.server_info()
        
        db = client[MONGO_DB]
        # Test write access
        test_collection = db["_connection_test"]
        test_collection.insert_one({"test": True})
        test_collection.delete_one({"test": True})
        client.close()
        
        # Mask password in display
        display_uri = MONGO_URI
        if "@" in display_uri:
            parts = display_uri.split("@")
            if len(parts) == 2:
                user_pass = parts[0].split("://")[-1]
                if ":" in user_pass:
                    user = user_pass.split(":")[0]
                    display_uri = display_uri.replace(f"{user}:", f"{user}:***")
        
        print(f"✅ MongoDB connection successful!")
        print(f"   URI: {display_uri}")
        print(f"   Database: {MONGO_DB}")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ MongoDB connection failed: {e}")
        print(f"   URI: {MONGO_URI.split('@')[0] if '@' in MONGO_URI else MONGO_URI}@***")
        print("\n💡 Troubleshooting:")
        if "mongodb+srv" in MONGO_URI:
            print("   - Check your internet connection")
            print("   - Verify MongoDB Atlas credentials")
            print("   - Ensure IP is whitelisted in MongoDB Atlas")
        else:
            print("   - Make sure MongoDB is running:")
            print("     make docker-up")
            print("     OR: docker-compose up -d")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

