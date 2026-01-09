"""Test MongoDB connection"""

import pytest
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from src.persistence.config import MONGO_URI, MONGO_DB


@pytest.mark.integration
def test_mongodb_connection():
    """Test that MongoDB is accessible."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        db = client[MONGO_DB]
        # Verify we can access the database
        assert db.name == MONGO_DB
        client.close()
    except ConnectionFailure:
        pytest.skip("MongoDB not available - start with: make docker-up")


@pytest.mark.integration
def test_mongodb_write_access():
    """Test that we can write to MongoDB."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[MONGO_DB]
        test_collection = db["_test_write"]
        
        # Insert test document
        result = test_collection.insert_one({"test": "write_access"})
        assert result.inserted_id is not None
        
        # Clean up
        test_collection.delete_one({"_id": result.inserted_id})
        client.close()
    except ConnectionFailure:
        pytest.skip("MongoDB not available - start with: make docker-up")

