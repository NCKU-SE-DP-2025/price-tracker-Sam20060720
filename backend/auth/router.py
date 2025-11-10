# External imports
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from passlib.context import CryptContext
from pydantic import BaseModel

# Internal imports
from database import get_db
from auth.dependencies import get_current_user, set_auth_service
from auth.models import User
from auth.service import AuthService
from config import JWT_SECRET

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# Global variables for auth service (will be set in main.py)
_auth_service: AuthService = None
_pwd_context: CryptContext = None


def set_auth_dependencies(auth_service: AuthService, pwd_context: CryptContext):
    """Set auth service and pwd context (called from main.py)"""
    global _auth_service, _pwd_context
    _auth_service = auth_service
    _pwd_context = pwd_context
    set_auth_service(auth_service)


class UserAuthSchema(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint"""
    user = _auth_service.verify_user_password(db, form_data.username, form_data.password)
    access_token = _auth_service.create_access_token(
        data={"sub": str(user.username)}, expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
def create_user(user: UserAuthSchema, db: Session = Depends(get_db)):
    """Create new user"""
    hashed_password = _pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/me")
def read_users_me(user=Depends(get_current_user)):
    """Get current user information"""
    return {"username": user.username}
