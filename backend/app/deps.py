from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import BaseModel
from app.db.models import UserRole
from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from app.security import decode_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


class UserCtx(BaseModel):
    id: UUID
    role: UserRole
    plant_id: Optional[UUID] = None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db=Depends(get_db)
) -> UserCtx:
    """Dependency to retrieve and validate the currently logged-in user context."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_jwt(token)
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id_str is None or token_type != "access":
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    return UserCtx(id=user.id, role=user.role, plant_id=user.plant_id)


def require_role(*roles: UserRole):
    """RBAC dependency checking that the user role matches allowed roles (admin always bypasses)."""
    async def _guard(user: UserCtx = Depends(get_current_user)) -> UserCtx:
        if user.role == UserRole.admin or user.role in roles:
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: insufficient role permissions"
        )
    return _guard
