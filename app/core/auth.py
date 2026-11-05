"""Authentication and Role-Based Access Control (RBAC) security module."""

import hashlib
import hmac
import os
import secrets
import time
from typing import Any
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.database import User

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "onenergy-insecure-scada-secret-key-32b")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

security_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Generates a secure PBKDF2-HMAC-SHA256 salted password hash."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}:{key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored salted hash."""
    try:
        salt, key_hex = hashed_password.split(":")
        expected_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return hmac.compare_digest(expected_key.hex(), key_hex)
    except Exception:
        return False


def create_access_token(data: dict[str, Any], expires_delta_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    """Encodes a JWT payload with expiration time."""
    to_encode = data.copy()
    expire_epoch = time.time() + (expires_delta_minutes * 60)
    to_encode.update({"exp": expire_epoch})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security_bearer),
) -> dict[str, Any]:
    """FastAPI dependency extracting authenticated user claims from Authorization header."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


def require_operator_role(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """FastAPI dependency enforcing OPERATOR role clearance for control operations."""
    role = user.get("role", "VIEWER")
    if role != "OPERATOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Role '{role}' lacks operator clearance for control actions",
        )
    return user

