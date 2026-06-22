from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import IngestionJob, IngestStage


class JobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, job_id: UUID) -> Optional[IngestionJob]:
        """Fetch a job by ID."""
        return await self.db.get(IngestionJob, job_id)

    async def get_by_document(self, doc_id: UUID) -> Optional[IngestionJob]:
        """Fetch job associated with a document."""
        stmt = select(IngestionJob).where(IngestionJob.document_id == doc_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_resume(self, doc_id: UUID, celery_task_id: Optional[str] = None) -> IngestionJob:
        """Create a new ingestion job or resume an existing one."""
        job = await self.get_by_document(doc_id)
        if not job:
            job = IngestionJob(
                document_id=doc_id,
                stage=IngestStage.parse_ocr,
                status="running",
                progress=0.000,
                celery_task_id=celery_task_id,
                started_at=datetime.utcnow()
            )
            self.db.add(job)
        else:
            job.status = "running"
            if celery_task_id:
                job.celery_task_id = celery_task_id
            job.started_at = datetime.utcnow()
            job.error = None
        await self.db.flush()
        return job

    async def update_progress(self, job_id: UUID, stage: IngestStage, progress: float) -> Optional[IngestionJob]:
        """Update job progress and stage."""
        job = await self.get(job_id)
        if job:
            job.stage = stage
            job.progress = progress
            await self.db.flush()
        return job

    async def finish(self, job_id: UUID) -> Optional[IngestionJob]:
        """Mark job as complete."""
        job = await self.get(job_id)
        if job:
            job.stage = IngestStage.done
            job.status = "done"
            job.progress = 1.000
            job.finished_at = datetime.utcnow()
            await self.db.flush()
        return job

    async def error(self, job_id: UUID, error_msg: str) -> Optional[IngestionJob]:
        """Mark job as failed with an error message."""
        job = await self.get(job_id)
        if job:
            job.status = "error"
            job.error = error_msg
            job.finished_at = datetime.utcnow()
            await self.db.flush()
        return job
