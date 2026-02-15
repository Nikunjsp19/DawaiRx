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
    disabled: bool = Field(default=False, description="If True, user cannot log in")
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


class RegistrationRequest(BaseModel):
    """Model for registration request"""
    user_id: str = Field(..., min_length=3, max_length=50, description="Desired username or user ID")
    email: Optional[str] = Field(None, description="User email")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for requesting access")
    company: Optional[str] = Field(None, max_length=100, description="Company or organization name")


class RegistrationRequestDocument(BaseModel):
    """Model for registration requests collection in MongoDB"""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()}
    )
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    user_id: str = Field(..., description="Desired username or user ID")
    email: Optional[str] = None
    reason: Optional[str] = None
    company: Optional[str] = None
    status: str = Field(default="pending", description="Request status: pending, approved, rejected")
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    admin_notes: Optional[str] = None


class RegistrationRequestResponse(BaseModel):
    """Response model for registration request"""
    request_id: str
    user_id: str
    email: Optional[str] = None
    status: str
    requested_at: datetime
    message: str

