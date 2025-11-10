
# External imports
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

# Internal imports
from auth.models import User

class AuthService:
    """Authentication and token-related operations."""

    def __init__(self, pwd_context: CryptContext, jwt_secret: str):
        self.pwd_context = pwd_context
        self.jwt_secret = jwt_secret

    def verify_password(self, password, hashed_password):
        return self.pwd_context.verify(password, hashed_password)

    def verify_user_password(self, db, username, password):
        user = db.query(User).filter(User.username == username).first()
        if not self.verify_password(password, user.hashed_password):
            return False
        return user

    def create_access_token(self, data, expires_delta=None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm="HS256")
        return encoded_jwt

    def authenticate_user_token(self, token, db):
        payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        return db.query(User).filter(User.username == payload.get("sub")).first()
