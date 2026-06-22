from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import RCAReport


class RCAReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, rca_id: UUID) -> Optional[RCAReport]:
        """Fetch RCA report by ID."""
        return await self.db.get(RCAReport, rca_id)

    async def get_by_incident(self, incident_id: UUID) -> Optional[RCAReport]:
        """Fetch RCA report associated with an incident."""
        stmt = select(RCAReport).where(RCAReport.incident_id == incident_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        incident_id: UUID,
        hypotheses: list,
        root_cause: str,
        confidence: float,
        citations: list,
        graph_path: Optional[dict] = None,
        generated_by: str = "rca_agent",
        reviewed_by: Optional[UUID] = None
    ) -> RCAReport:
        """Create a new RCA report."""
        report = RCAReport(
            incident_id=incident_id,
            hypotheses=hypotheses,
            root_cause=root_cause,
            confidence=confidence,
            citations=citations,
            graph_path=graph_path,
            generated_by=generated_by,
            reviewed_by=reviewed_by
        )
        self.db.add(report)
        await self.db.flush()
        return report
