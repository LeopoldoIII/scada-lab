"""Authentication route endpoints for user login and token introspection."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import LoginRequest, TokenResponse, UserResponse
from app.core.auth import create_access_token, get_current_user, verify_password
from app.core.database import User

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# In-memory session db dependency provider (injected in main.py)
_db_factory = None


def set_db_factory(factory) -> None:
    global _db_factory
    _db_factory = factory


def get_db():
    if _db_factory is None:
        raise RuntimeError("Database factory not initialized")
    session = _db_factory()
    try:
        yield session
    finally:
        session.close()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticates operator credentials and returns a signed JWT bearer token."""
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": user.username, "role": user.role, "user_id": user.id}
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=user.username,
        role=user.role,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user_claims: dict = Depends(get_current_user)) -> UserResponse:
    """Returns claims of the currently authenticated operator session."""
    return UserResponse(
        id=user_claims.get("user_id", 0),
        username=user_claims.get("sub", "unknown"),
        role=user_claims.get("role", "VIEWER"),
    )

