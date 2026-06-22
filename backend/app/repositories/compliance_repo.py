from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import ComplianceFinding, FindingStatus, Severity


class ComplianceFindingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, finding_id: UUID) -> Optional[ComplianceFinding]:
        """Fetch finding by ID."""
        return await self.db.get(ComplianceFinding, finding_id)

    async def list(
        self,
        plant_id: Optional[UUID] = None,
        status: Optional[FindingStatus] = None,
        severity: Optional[Severity] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[ComplianceFinding]:
        """List compliance findings with optional filters."""
        stmt = select(ComplianceFinding)
        if plant_id:
            from app.db.models import Asset
            stmt = stmt.join(ComplianceFinding.asset).where(Asset.plant_id == plant_id)
        if status:
            stmt = stmt.where(ComplianceFinding.status == status)
        if severity:
            stmt = stmt.where(ComplianceFinding.severity == severity)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        asset_id: Optional[UUID],
        document_id: Optional[UUID],
        regulation_ref: str,
        requirement: Optional[str],
        status: FindingStatus,
        severity: Severity = Severity.medium,
        description: Optional[str] = None,
        citations: Optional[list] = None,
        detected_by: str = "compliance_agent"
    ) -> ComplianceFinding:
        """Create a new compliance finding."""
        finding = ComplianceFinding(
            asset_id=asset_id,
            document_id=document_id,
            regulation_ref=regulation_ref,
            requirement=requirement,
            status=status,
            severity=severity,
            description=description,
            citations=citations or [],
            detected_by=detected_by,
            detected_at=datetime.utcnow()
        )
        self.db.add(finding)
        await self.db.flush()
        return finding

    async def update_status(self, finding_id: UUID, status: FindingStatus) -> Optional[ComplianceFinding]:
        """Update status of a compliance finding."""
        finding = await self.get(finding_id)
        if finding:
            finding.status = status
            if status == FindingStatus.compliant:
                finding.resolved_at = datetime.utcnow()
            else:
                finding.resolved_at = None
            await self.db.flush()
        return finding
