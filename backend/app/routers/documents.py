from typing import Optional
from datetime import date, datetime
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import DocumentType, UserRole
from app.schemas.documents import DocumentResponse
from app.services.document_service import DocumentService
from app.deps import require_role, UserCtx


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.technician, UserRole.admin, UserRole.manager))]
)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    doc_type: DocumentType = Form(...),
    effective_date: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: UserCtx = Depends(require_role(UserRole.technician, UserRole.admin, UserRole.manager))
):
    if not current_user.plant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be associated with a plant to upload documents"
        )
    
    parsed_date = None
    if effective_date:
        try:
            parsed_date = date.fromisoformat(effective_date)
        except ValueError:
            # Try parsing datetime then converting to date
            try:
                parsed_date = datetime.fromisoformat(effective_date).date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid effective_date format. Must be YYYY-MM-DD"
                )

    service = DocumentService(db)
    doc = await service.upload_document(
        file=file,
        title=title,
        doc_type=doc_type,
        plant_id=current_user.plant_id,
        uploader_id=current_user.id,
        effective_date=parsed_date
    )
    return doc
