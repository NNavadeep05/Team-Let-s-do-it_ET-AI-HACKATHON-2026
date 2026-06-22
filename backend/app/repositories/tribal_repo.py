from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import TribalKnowledge, CaptureType


class TribalKnowledgeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, note_id: UUID) -> Optional[TribalKnowledge]:
        """Fetch tribal knowledge by ID."""
        return await self.db.get(TribalKnowledge, note_id)

    async def list(
        self,
        asset_id: Optional[UUID] = None,
        verified: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[TribalKnowledge]:
        """List tribal knowledge notes with optional filters."""
        stmt = select(TribalKnowledge)
        if asset_id:
            stmt = stmt.where(TribalKnowledge.asset_id == asset_id)
        if verified is not None:
            stmt = stmt.where(TribalKnowledge.verified == verified)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        asset_id: Optional[UUID],
        author_id: Optional[UUID],
        capture_type: CaptureType,
        media_key: Optional[str] = None,
        transcript: Optional[str] = None,
        structured: Optional[dict] = None,
        verified: bool = False,
        neo4j_node_id: Optional[str] = None
    ) -> TribalKnowledge:
        """Create a new tribal knowledge note."""
        note = TribalKnowledge(
            asset_id=asset_id,
            author_id=author_id,
            capture_type=capture_type,
            media_key=media_key,
            transcript=transcript,
            structured=structured or {},
            verified=verified,
            neo4j_node_id=neo4j_node_id
        )
        self.db.add(note)
        await self.db.flush()
        return note

    async def verify(self, note_id: UUID, verified: bool = True, neo4j_node_id: Optional[str] = None) -> Optional[TribalKnowledge]:
        """Verify tribal knowledge note and optionally link the neo4j_node_id."""
        note = await self.get(note_id)
        if note:
            note.verified = verified
            if neo4j_node_id:
                note.neo4j_node_id = neo4j_node_id
            await self.db.flush()
        return note
