import os
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, field_validator
import re

from database import get_db
import models.user as user_model

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Config — fail LOUDLY if JWT secret is not set
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )
if len(SECRET_KEY) < 32:
    raise RuntimeError(
        f"JWT_SECRET must be at least 32 characters (yours is {len(SECRET_KEY)}). "
        "Generate a strong one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "7"))

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Pre-computed dummy hash used to keep timing constant when user doesn't exist
# (prevents user-enumeration via response timing).
_DUMMY_PASSWORD_HASH = pwd_context.hash("not-a-real-password-just-for-timing")

# ---------------------------------------------------------------------------
# OAuth2 / JWT
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT with timezone-aware expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 50:
            raise ValueError("Username must be 50 characters or fewer")
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, underscore, dot, hyphen"
            )
        return v.lower()  # normalize for case-insensitive lookups

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password must be 128 characters or fewer")
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Current-user dependency
# ---------------------------------------------------------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> user_model.User:
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
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        raise credentials_exception

    user = db.query(user_model.User).filter(
        func.lower(user_model.User.username) == username.lower()
    ).first()

    if user is None:
        raise credentials_exception

    # Enforce account-disabled flag (if you've added is_active to User model)
    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    return user


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Normalize email (already lowercased username from validator)
    email = user.email.lower().strip()

    # Check if user already exists (case-insensitive)
    db_user = db.query(user_model.User).filter(
        (func.lower(user_model.User.username) == user.username) |
        (func.lower(user_model.User.email) == email)
    ).first()

    if db_user:
        # FIXED: generic error message — don't leak whether email/username exists
        logger.info(f"Registration attempt with existing identity: {user.username} / {email}")
        raise HTTPException(
            status_code=400,
            detail="Could not create account. Try a different username or email.",
        )

    # Hash password and create user
    hashed_password = pwd_context.hash(user.password)
    db_user = user_model.User(
        username=user.username,
        email=email,
        hashed_password=hashed_password,
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create account")

    logger.info(f"New user registered: {db_user.username}")

    # Create access token
    access_token = create_access_token(
        data={"sub": db_user.username},
        expires_delta=timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # Find user by email or username (case-insensitive)
    identifier = form_data.username.lower().strip()
    user = db.query(user_model.User).filter(
        (func.lower(user_model.User.email) == identifier) |
        (func.lower(user_model.User.username) == identifier)
    ).first()

    # FIXED: always run hash verify (even when user doesn't exist)
    # to prevent user-enumeration via response timing.
    if user:
        password_valid = pwd_context.verify(form_data.password, user.hashed_password)
    else:
        pwd_context.verify(form_data.password, _DUMMY_PASSWORD_HASH)
        password_valid = False

    if not user or not password_valid:
        logger.warning(f"Failed login attempt for: {identifier}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Enforce account-disabled flag (if present)
    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    logger.info(f"User logged in: {user.username}")

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: user_model.User = Depends(get_current_user)):
    """Returns the current authenticated user's profile."""
    return current_user