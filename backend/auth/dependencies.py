# External imports
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Internal imports
from database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

_auth_service = None


def set_auth_service(auth_service):
    """Set auth_service instance (called from main.py)"""
    global _auth_service
    _auth_service = auth_service


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    if _auth_service is None:
        raise ValueError("auth_service not initialized")
    return _auth_service.authenticate_user_token(token, db)

