import hashlib
import uuid
from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Document, DocumentStatus, DocumentType
from app.repositories.document_repo import DocumentRepository
from app.repositories.job_repo import JobRepository
from app.services.storage_service import storage_service
from app.ingestion.tasks import ingest_document


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.job_repo = JobRepository(db)

    async def upload_document(
        self,
        file: UploadFile,
        title: str,
        doc_type: DocumentType,
        plant_id: UUID,
        uploader_id: UUID,
        effective_date: Optional[date] = None
    ) -> Document:
        # Read file content
        content = await file.read()
        
        # Calculate SHA256 checksum
        checksum = hashlib.sha256(content).hexdigest()
        
        # Generate storage key
        # Use simple forward slash for cloud storage prefix consistency
        file_uuid = uuid.uuid4().hex
        storage_key = f"documents/{plant_id}/{file_uuid}_{file.filename}"
        
        # Upload to MinIO via storage_service
        # Seek back file pointer in case it needs to be read again
        await file.seek(0)
        await storage_service.put(storage_key, content, content_type=file.content_type)
        
        # Create document row in database
        doc = await self.doc_repo.create(
            title=title,
            doc_type=doc_type,
            storage_key=storage_key,
            mime_type=file.content_type or "application/octet-stream",
            checksum_sha256=checksum,
            plant_id=plant_id,
            uploaded_by=uploader_id,
            status=DocumentStatus.uploaded,
            effective_date=effective_date
        )
        
        # Create IngestionJob row in database
        job = await self.job_repo.create_or_resume(doc.id)
        
        await self.db.commit()
        
        # Enqueue Celery task
        ingest_document.delay(str(doc.id))
        
        return doc
