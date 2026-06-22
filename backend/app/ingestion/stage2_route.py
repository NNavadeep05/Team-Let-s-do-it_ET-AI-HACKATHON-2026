import io
import csv
import logging
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Document, DocumentType
from app.repositories.document_repo import DocumentRepository
from app.services.storage_service import storage_service
from app.ingestion.stage1_parse import PageText

logger = logging.getLogger(__name__)


@dataclass
class ProseBlock:
    page_number: int
    text: str
    image_key: Optional[str] = None
    section_path: Optional[str] = None


@dataclass
class TableBlock:
    page_number: int
    rows: List[List[str]]
    csv_key: str


@dataclass
class DiagramBlock:
    page_number: int
    image_key: str
    is_pid: bool = False


@dataclass
class RoutedBlocks:
    prose: List[ProseBlock] = field(default_factory=list)
    tables: List[TableBlock] = field(default_factory=list)
    diagrams: List[DiagramBlock] = field(default_factory=list)


async def save_table_csv(doc_id: UUID, page_num: int, table_idx: int, rows: List[List[str]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(rows)
    csv_data = output.getvalue().encode("utf-8")
    csv_key = f"extracted-assets/{doc_id}/page-{page_num:04d}-table-{table_idx}.csv"
    await storage_service.put(csv_key, csv_data, content_type="text/csv")
    return csv_key


def parse_markdown_blocks(content: str) -> RoutedBlocks:
    routed = RoutedBlocks()
    lines = content.splitlines()
    
    in_table = False
    table_rows = []
    
    prose_accumulator = []
    current_section = None
    
    def flush_prose():
        if prose_accumulator:
            text = "\n".join(prose_accumulator).strip()
            if text:
                routed.prose.append(ProseBlock(page_number=1, text=text, section_path=current_section))
            prose_accumulator.clear()
            
    for line in lines:
        stripped = line.strip()
        
        # Section Heading
        if stripped.startswith("#"):
            flush_prose()
            # Extract section path (e.g. heading text)
            current_section = stripped.lstrip("#").strip()
            prose_accumulator.append(line)
            continue
            
        # Table detection (starts/ends with | or has | divider)
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            # Filter out empty first/last elements if it starts/ends with |
            if line.startswith("|"):
                parts = parts[1:]
            if line.endswith("|"):
                parts = parts[:-1]
                
            # Skip divider lines like |---|---|
            if parts and all(all(c == '-' for c in p) for p in parts if p):
                continue
                
            if len(parts) >= 1:
                if not in_table:
                    flush_prose()
                    in_table = True
                table_rows.append(parts)
                continue
        else:
            if in_table:
                if len(table_rows) > 0:
                    routed.tables.append(TableBlock(page_number=1, rows=table_rows, csv_key=""))
                table_rows = []
                in_table = False
                
            prose_accumulator.append(line)
            
    # Flush remaining
    if in_table and len(table_rows) > 0:
        routed.tables.append(TableBlock(page_number=1, rows=table_rows, csv_key=""))
    flush_prose()
    
    return routed


async def stage2_route(db: AsyncSession, doc_id: UUID, pages: List[PageText]) -> RoutedBlocks:
    doc_repo = DocumentRepository(db)
    doc = await doc_repo.get(doc_id)
    if not doc:
        raise ValueError(f"Document with ID {doc_id} not found")

    blob = await storage_service.get(doc.storage_key)
    is_pdf = doc.mime_type == "application/pdf" or doc.title.lower().endswith(".pdf")
    
    if not is_pdf:
        # Parse Markdown/Text directly
        content = blob.decode("utf-8")
        routed = parse_markdown_blocks(content)
        
        # Save extracted tables as CSVs asynchronously
        for idx, tbl in enumerate(routed.tables):
            csv_key = await save_table_csv(doc_id, tbl.page_number, idx + 1, tbl.rows)
            tbl.csv_key = csv_key
            
        return routed
        
    # PDF routing
    import fitz
    import pdfplumber
    
    routed = RoutedBlocks()
    fitz_pdf = fitz.open(stream=blob, filetype="pdf")
    
    with pdfplumber.open(io.BytesIO(blob)) as pdf:
        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            p_text = pages[i]
            
            # 1. Extract tables via pdfplumber
            tables = page.find_tables()
            for t_idx, tbl in enumerate(tables):
                rows = tbl.extract()
                clean_rows = [[str(cell) if cell is not None else "" for cell in row] for row in rows]
                csv_key = await save_table_csv(doc_id, page_num, t_idx + 1, clean_rows)
                routed.tables.append(TableBlock(page_num, clean_rows, csv_key))
                
            # 2. Extract diagrams / P&IDs via fitz complexity drawings check
            fitz_page = fitz_pdf[i]
            drawings_count = len(fitz_page.get_drawings())
            has_large_image = False
            
            # Check for large image
            img_list = fitz_page.get_images()
            for img in img_list:
                # img[2] is width, img[3] is height
                if img[2] > 400 and img[3] > 400:
                    has_large_image = True
                    break
                    
            if drawings_count > 80 or has_large_image:
                routed.diagrams.append(
                    DiagramBlock(
                        page_number=page_num,
                        image_key=p_text.image_key or "",
                        is_pid=(doc.doc_type == DocumentType.pid)
                    )
                )
                
            # 3. Add prose block
            # In simple routing, page text is parsed as prose
            routed.prose.append(
                ProseBlock(
                    page_number=page_num,
                    text=p_text.text,
                    image_key=p_text.image_key
                )
            )
            
    return routed
