from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import KnowledgeScore


class KnowledgeScoreRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, score_id: UUID) -> Optional[KnowledgeScore]:
        """Fetch knowledge score by ID."""
        return await self.db.get(KnowledgeScore, score_id)

    async def get_latest(self, scope: str, scope_id: UUID) -> Optional[KnowledgeScore]:
        """Fetch the latest score for a given scope and scope_id."""
        stmt = (
            select(KnowledgeScore)
            .where(KnowledgeScore.scope == scope, KnowledgeScore.scope_id == scope_id)
            .order_by(KnowledgeScore.computed_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_history(
        self,
        scope: str,
        scope_id: UUID,
        limit: int = 10
    ) -> List[KnowledgeScore]:
        """Fetch historical scores for a given scope and scope_id."""
        stmt = (
            select(KnowledgeScore)
            .where(KnowledgeScore.scope == scope, KnowledgeScore.scope_id == scope_id)
            .order_by(KnowledgeScore.computed_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        scope: str,
        scope_id: UUID,
        completeness: float,
        freshness: float,
        breakdown: Optional[dict] = None
    ) -> KnowledgeScore:
        """Create a new knowledge score record."""
        score = KnowledgeScore(
            scope=scope,
            scope_id=scope_id,
            completeness=completeness,
            freshness=freshness,
            breakdown=breakdown or {},
            computed_at=datetime.utcnow()
        )
        self.db.add(score)
        await self.db.flush()
        return score
