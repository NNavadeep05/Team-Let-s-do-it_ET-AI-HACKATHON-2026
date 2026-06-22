from typing import Optional
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict
from app.db.models import DocumentType, DocumentStatus


class DocumentBase(BaseModel):
    title: str
    doc_type: DocumentType
    effective_date: Optional[date] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: UUID
    status: DocumentStatus
    storage_key: str
    mime_type: str
    checksum_sha256: str
    page_count: Optional[int] = None
    plant_id: Optional[UUID] = None
    uploaded_by: Optional[UUID] = None
    version: int
    supersedes_id: Optional[UUID] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
