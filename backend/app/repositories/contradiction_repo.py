from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Contradiction, ContradictionKind, Severity


class ContradictionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, contradiction_id: UUID) -> Optional[Contradiction]:
        """Fetch a contradiction by ID."""
        return await self.db.get(Contradiction, contradiction_id)

    async def list(
        self,
        plant_id: Optional[UUID] = None,
        status: Optional[str] = None,
        severity: Optional[Severity] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Contradiction]:
        """List contradictions with optional filters."""
        stmt = select(Contradiction)
        if plant_id:
            from app.db.models import Asset
            stmt = stmt.join(Contradiction.asset).where(Asset.plant_id == plant_id)
        if status:
            stmt = stmt.where(Contradiction.status == status)
        if severity:
            stmt = stmt.where(Contradiction.severity == severity)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        asset_id: Optional[UUID],
        parameter: Optional[str],
        kind: ContradictionKind,
        claim_a: dict,
        claim_b: dict,
        extra_claims: Optional[list] = None,
        severity: Severity = Severity.high,
        status: str = "open"
    ) -> Contradiction:
        """Create a new contradiction."""
        contradiction = Contradiction(
            asset_id=asset_id,
            parameter=parameter,
            kind=kind,
            claim_a=claim_a,
            claim_b=claim_b,
            extra_claims=extra_claims or [],
            severity=severity,
            status=status,
            detected_at=datetime.utcnow()
        )
        self.db.add(contradiction)
        await self.db.flush()
        return contradiction

    async def resolve(self, contradiction_id: UUID, resolution: str, resolved_by: UUID) -> Optional[Contradiction]:
        """Resolve a contradiction."""
        contradiction = await self.get(contradiction_id)
        if contradiction:
            contradiction.status = "resolved"
            contradiction.resolution = resolution
            contradiction.resolved_by = resolved_by
            await self.db.flush()
        return contradiction
