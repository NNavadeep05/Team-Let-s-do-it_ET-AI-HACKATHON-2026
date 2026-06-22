from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Incident, Severity


class IncidentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, incident_id: UUID) -> Optional[Incident]:
        """Fetch incident by ID."""
        return await self.db.get(Incident, incident_id)

    async def list(self, plant_id: Optional[UUID] = None) -> List[Incident]:
        """List incidents with optional plant filter."""
        stmt = select(Incident)
        if plant_id:
            # Join with Asset to filter by plant_id
            from app.db.models import Asset
            stmt = stmt.join(Asset).where(Asset.plant_id == plant_id)
        stmt = stmt.order_by(Incident.occurred_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        asset_id: UUID,
        description: str,
        severity: Severity = Severity.medium,
        occurred_at: Optional[datetime] = None,
        incident_number: Optional[str] = None,
        document_id: Optional[UUID] = None
    ) -> Incident:
        """Create a new incident."""
        incident = Incident(
            asset_id=asset_id,
            description=description,
            severity=severity,
            occurred_at=occurred_at or datetime.utcnow(),
            incident_number=incident_number,
            document_id=document_id
        )
        self.db.add(incident)
        await self.db.flush()
        return incident

    async def set_rca_id(self, incident_id: UUID, rca_id: UUID) -> Optional[Incident]:
        """Set or update the associated RCA report ID."""
        incident = await self.get(incident_id)
        if incident:
            incident.rca_id = rca_id
            await self.db.flush()
        return incident
