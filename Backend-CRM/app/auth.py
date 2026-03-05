"""
Authentication utilities for JWT tokens and password hashing.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app import crud
from app.config import settings

# OAuth2 schemes for token extraction
# - oauth2_scheme: strict, errors if no/invalid token (used for required-auth endpoints)
# - oauth2_optional_scheme: does NOT auto-error, lets us treat auth as optional
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
oauth2_optional_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

# JWT settings
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        # Ensure password is bytes
        password_bytes = plain_password.encode('utf-8')
        # Truncate to 72 bytes if necessary (bcrypt limit)
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        # Verify password
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password. Bcrypt has a 72 byte limit, so we truncate if necessary."""
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    # Bcrypt has a 72 byte limit, truncate if password is too long
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await crud.get_user(db, user_id)
    if user is None:
        raise credentials_exception
    
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "is_privileged": user.is_privileged == 'true'
    }


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_optional_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[dict]:
    """
    Get the current user if authenticated, otherwise return None.
    
    Uses an OAuth2 scheme with auto_error=False so that endpoints depending
    on this function do NOT automatically return 401 when no token is provided.
    """
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        # If token is invalid/expired, treat as anonymous instead of raising.
        return None

