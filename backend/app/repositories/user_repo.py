from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, user_id: UUID) -> Optional[User]:
        """Fetch user by primary key ID."""
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by email address (case-insensitive due to CITEXT)."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
        role: UserRole,
        plant_id: Optional[UUID] = None
    ) -> User:
        """Create a new user and flush to DB to generate the ID."""
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            plant_id=plant_id
        )
        self.db.add(user)
        await self.db.flush()
        return user
