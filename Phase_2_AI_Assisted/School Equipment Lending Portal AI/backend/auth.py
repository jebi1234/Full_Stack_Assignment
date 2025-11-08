# File: backend/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import crud, models, schemas, database
from sqlalchemy.orm import Session

# --- CONFIGURATION ---

# 1. Password Hashing (we already had this in crud.py, moving it here)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. JWT Settings
#    Run this in your terminal to get a random key:
#    openssl rand -hex 32
SECRET_KEY = "8146f8c693b0ac9364d6c17e1f7bcd1022c818c069ac9baf223a4b966360070d" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 3. OAuth2 Scheme
# This tells FastAPI what the "login" endpoint will be
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# --- UTILITY FUNCTIONS ---

def verify_password(plain_password, hashed_password):
    """Checks if the plain password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hashes a plain password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a new JWT Access Token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- AUTHENTICATION & AUTHORIZATION ---

def authenticate_user(db: Session, username: str, password: str):
    """
    Finds a user in the DB and verifies their password.
    Returns the user object if successful, otherwise None.
    """
    user = crud.get_user_by_username(db, username=username)
    if not user:
        return None  # User doesn't exist
    if not verify_password(password, user.hashed_password):
        return None  # Incorrect password
    
    return user # Authentication successful

def get_current_user(db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    """
    Dependency to get the current user from a token.
    This will be used to protect our endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
# File: backend/auth.py
# --- Add this function to the bottom ---

...

def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    """
    Dependency that checks if the current user is an admin.
    If not, it raises a 403 Forbidden error.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted: Requires admin role"
        )
    return current_user