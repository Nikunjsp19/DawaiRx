"""User models for authentication"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from bson import ObjectId


class UserDocument(BaseModel):
    """Model for users collection in MongoDB"""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()}
    )
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    user_id: str = Field(..., description="Unique user identifier (username or email)")
    email: Optional[str] = Field(None, description="User email")  # Changed from EmailStr to str
    password_hash: str = Field(..., description="Hashed password")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(BaseModel):
    """Model for creating a new user"""
    user_id: str = Field(..., min_length=3, max_length=50, description="Username or user ID")
    email: Optional[str] = None  # Changed from EmailStr to str to avoid validation issues
    password: str = Field(..., min_length=6, description="Plain text password")


class UserLogin(BaseModel):
    """Model for user login"""
    user_id: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """Response model for authentication token"""
    access_token: str
    token_type: str = "bearer"
    user_id: str


class UserUpdate(BaseModel):
    """Model for updating user settings"""
    email: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=6, description="New password (min 6 characters)")

