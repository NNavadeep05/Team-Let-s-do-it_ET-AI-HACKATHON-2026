from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Chunk


class ChunkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, chunk_id: UUID) -> Optional[Chunk]:
        """Fetch a chunk by ID."""
        return await self.db.get(Chunk, chunk_id)

    async def get_by_document(self, doc_id: UUID) -> List[Chunk]:
        """Fetch all chunks associated with a document."""
        stmt = select(Chunk).where(Chunk.document_id == doc_id).order_by(Chunk.chunk_index)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def bulk_insert(self, doc_id: UUID, prose_blocks: List[Any], points: List[Any]) -> List[Chunk]:
        """Bulk insert chunks corresponding to prose blocks and vector points."""
        chunks = []
        for idx, (block, point) in enumerate(zip(prose_blocks, points)):
            # Extract point ID (which could be a Qdrant PointStruct or a raw UUID)
            point_id = point
            if hasattr(point, "id"):
                point_id = point.id

            content = ""
            if hasattr(block, "text"):
                content = block.text
            elif hasattr(block, "content"):
                content = block.content
            elif isinstance(block, dict):
                content = block.get("text", block.get("content", ""))
            else:
                content = str(block)

            chunk = Chunk(
                document_id=doc_id,
                page_number=getattr(block, "page_number", block.get("page_number", None) if isinstance(block, dict) else None),
                chunk_index=idx,
                content=content,
                token_count=getattr(block, "token_count", block.get("token_count", None) if isinstance(block, dict) else None),
                section_path=getattr(block, "section_path", block.get("section_path", None) if isinstance(block, dict) else None),
                qdrant_point_id=UUID(str(point_id)) if not isinstance(point_id, UUID) else point_id,
                chunk_metadata=getattr(block, "metadata", block.get("metadata", {}) if isinstance(block, dict) else {})
            )
            self.db.add(chunk)
            chunks.append(chunk)
        await self.db.flush()
        return chunks


# For type hints
from typing import Any
