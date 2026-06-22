import io
import logging
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Document, DocumentPage, DocumentStatus
from app.repositories.document_repo import DocumentRepository
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)


@dataclass
class PageText:
    page_number: int
    text: str
    image_key: Optional[str] = None
    ocr_confidence: Optional[float] = None


async def stage1_parse_ocr(db: AsyncSession, doc_id: UUID) -> List[PageText]:
    doc_repo = DocumentRepository(db)
    doc = await doc_repo.get(doc_id)
    if not doc:
        raise ValueError(f"Document with ID {doc_id} not found")

    # Fetch document blob from MinIO
    blob = await storage_service.get(doc.storage_key)
    
    pages: List[PageText] = []

    # Check document mime type or title extension
    is_pdf = doc.mime_type == "application/pdf" or doc.title.lower().endswith(".pdf")
    
    if is_pdf:
        import fitz
        pdf = fitz.open(stream=blob, filetype="pdf")
        
        for i, page in enumerate(pdf):
            page_num = i + 1
            text = page.get_text("text")
            
            # Render page to PNG
            pix = page.get_pixmap(dpi=200)
            png = pix.tobytes("png")
            img_key = f"page-images/{doc_id}/page-{page_num:04d}.png"
            
            # Upload page image to MinIO
            await storage_service.put(img_key, png, content_type="image/png")
            
            conf = None
            if len(text.strip()) < 40:
                # Scanned or low-text page, try OCR fallback
                try:
                    import pytesseract
                    # Convert to PIL Image
                    img = Image.open(io.BytesIO(png))
                    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                    
                    # Extract words
                    words = [w for w, c in zip(ocr_data["text"], ocr_data["conf"]) if w.strip()]
                    text = " ".join(words)
                    
                    confs = [float(c) for c in ocr_data["conf"] if c >= 0]
                    if confs:
                        conf = sum(confs) / len(confs) / 100.0
                except Exception as e:
                    logger.warning(f"OCR failed or tesseract not installed: {e}")
                    conf = 0.0

            # Save page to DB
            stmt = select(DocumentPage).where(
                DocumentPage.document_id == doc_id,
                DocumentPage.page_number == page_num
            )
            res = await db.execute(stmt)
            db_page = res.scalar_one_or_none()
            if not db_page:
                db_page = DocumentPage(
                    document_id=doc_id,
                    page_number=page_num,
                    image_key=img_key,
                    raw_text=text,
                    ocr_confidence=conf
                )
                db.add(db_page)
            else:
                db_page.image_key = img_key
                db_page.raw_text = text
                db_page.ocr_confidence = conf
                
            pages.append(PageText(page_num, text, img_key, conf))
            
        await doc_repo.set_page_count(doc_id, len(pdf))
        
    else:
        # Markdown or Text
        content = blob.decode("utf-8")
        
        # Save page 1 in DB
        stmt = select(DocumentPage).where(
            DocumentPage.document_id == doc_id,
            DocumentPage.page_number == 1
        )
        res = await db.execute(stmt)
        db_page = res.scalar_one_or_none()
        if not db_page:
            db_page = DocumentPage(
                document_id=doc_id,
                page_number=1,
                raw_text=content
            )
            db.add(db_page)
        else:
            db_page.raw_text = content
            
        pages.append(PageText(1, content))
        await doc_repo.set_page_count(doc_id, 1)

    await db.flush()
    return pages
