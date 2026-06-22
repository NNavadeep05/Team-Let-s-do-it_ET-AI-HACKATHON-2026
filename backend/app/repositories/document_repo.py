from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Document, DocumentType, DocumentStatus


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, doc_id: UUID) -> Optional[Document]:
        """Fetch a document by ID."""
        return await self.db.get(Document, doc_id)

    async def list(
        self,
        plant_id: Optional[UUID] = None,
        doc_type: Optional[DocumentType] = None,
        status: Optional[DocumentStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Document]:
        """List documents with optional filters and pagination."""
        stmt = select(Document)
        if plant_id:
            stmt = stmt.where(Document.plant_id == plant_id)
        if doc_type:
            stmt = stmt.where(Document.doc_type == doc_type)
        if status:
            stmt = stmt.where(Document.status == status)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        plant_id: Optional[UUID] = None,
        doc_type: Optional[DocumentType] = None,
        status: Optional[DocumentStatus] = None
    ) -> int:
        """Count total documents matching filters."""
        stmt = select(func.count(Document.id))
        if plant_id:
            stmt = stmt.where(Document.plant_id == plant_id)
        if doc_type:
            stmt = stmt.where(Document.doc_type == doc_type)
        if status:
            stmt = stmt.where(Document.status == status)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def create(
        self,
        title: str,
        doc_type: DocumentType,
        storage_key: str,
        mime_type: str,
        checksum_sha256: str,
        plant_id: Optional[UUID] = None,
        uploaded_by: Optional[UUID] = None,
        status: DocumentStatus = DocumentStatus.uploaded,
        effective_date: Optional[date] = None
    ) -> Document:
        """Create a new document."""
        doc = Document(
            title=title,
            doc_type=doc_type,
            storage_key=storage_key,
            mime_type=mime_type,
            checksum_sha256=checksum_sha256,
            plant_id=plant_id,
            uploaded_by=uploaded_by,
            status=status,
            effective_date=effective_date
        )
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def set_status(self, doc_id: UUID, status: DocumentStatus) -> Optional[Document]:
        """Update status of a document."""
        doc = await self.get(doc_id)
        if doc:
            doc.status = status
            if status == DocumentStatus.processed:
                doc.processed_at = datetime.utcnow()
            await self.db.flush()
        return doc

    async def set_page_count(self, doc_id: UUID, count: int) -> Optional[Document]:
        """Update page count of a document."""
        doc = await self.get(doc_id)
        if doc:
            doc.page_count = count
            await self.db.flush()
        return doc

    async def delete(self, doc_id: UUID) -> bool:
        """Delete a document by ID."""
        doc = await self.get(doc_id)
        if doc:
            await self.db.delete(doc)
            await self.db.flush()
            return True
        return False
