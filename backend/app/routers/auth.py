from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from app.db.session import get_db
from app.deps import get_current_user, UserCtx
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, TokenRefreshRequest, UserResponse
from app.services.auth_service import AuthService
from app.security import create_access_token, create_refresh_token, decode_jwt

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db=Depends(get_db)):
    """Authenticate email and password, returning access/refresh tokens and user details."""
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    user = await auth_service.authenticate(req.email, req.password)

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh(req: TokenRefreshRequest, db=Depends(get_db)):
    """Verify refresh token and issue new access/refresh tokens."""
    try:
        payload = decode_jwt(req.refresh_token)
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id_str is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or non-existent user",
        )

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserCtx)
async def me(current_user: UserCtx = Depends(get_current_user)):
    """Return the authenticated user's context (role, plant_id, id)."""
    return current_user
