"""Authentication middleware for FastAPI"""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from src.auth.utils import decode_access_token
from src.auth.user_store import UserStore

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract and validate user_id from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


def get_user_store() -> UserStore:
    """Dependency to get user store instance"""
    return UserStore()

