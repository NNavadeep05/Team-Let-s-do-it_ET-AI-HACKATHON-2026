import uuid
import logging
from typing import List, Tuple, Dict
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Document, Chunk, EntityMention
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.entity_repo import EntityRepository
from app.ingestion.stage2_route import RoutedBlocks
from app.ingestion.stage3_entities import ExtractedEntity
from app.ingestion.stage4_relationships import ExtractedRelationship
from app.ingestion.writers.graph_writer import GraphWriter
from app.ingestion.writers.vector_writer import VectorWriter

logger = logging.getLogger(__name__)


async def stage5_write(
    db: AsyncSession,
    doc_id: UUID,
    plant_id: UUID,
    blocks: RoutedBlocks,
    resolved_pairs: List[Tuple[ExtractedEntity, Any]], # List[Tuple[ExtractedEntity, Entity]]
    rels: List[ExtractedRelationship],
    job
) -> None:
    graph_writer = GraphWriter()
    vector_writer = VectorWriter()
    
    # 0. Fetch Document model from DB
    from app.repositories.document_repo import DocumentRepository
    doc_repo = DocumentRepository(db)
    doc = await doc_repo.get(doc_id)
    if not doc:
        raise ValueError(f"Document with ID {doc_id} not found")
        
    # 5a. Upsert Document in Neo4j
    await graph_writer.upsert_document(
        doc_id=doc.id,
        title=doc.title,
        doc_type=doc.doc_type.value,
        effective_date=doc.effective_date
    )
    
    # 5b. Generate chunk UUIDs (deterministic uuid5)
    NAMESPACE = uuid.NAMESPACE_DNS
    chunk_uuids = [
        uuid.uuid5(NAMESPACE, f"{doc_id}:{idx}")
        for idx in range(len(blocks.prose))
    ]
    
    # Upsert Chunks in Neo4j
    if blocks.prose:
        await graph_writer.upsert_chunks(doc.id, blocks.prose, chunk_uuids)
    
    # 5c. Write Chunks to Postgres
    chunk_repo = ChunkRepository(db)
    inserted_chunks = await chunk_repo.bulk_insert(doc.id, blocks.prose, chunk_uuids)
    
    # Create mapping from qdrant_point_id to Postgres Chunk.id
    chunk_id_map: Dict[UUID, UUID] = {
        c.qdrant_point_id: c.id
        for c in inserted_chunks
    }
    
    # 5d. Merge Entities in Neo4j and create mentions in Postgres
    entity_repo = EntityRepository(db)
    entity_map: Dict[str, Tuple[UUID, str]] = {} # name.lower() -> (id, type)
    
    for ext_ent, db_ent in resolved_pairs:
        # Save mapping for relationship resolution
        entity_map[db_ent.canonical_name.strip().lower()] = (db_ent.id, db_ent.entity_type.value)
        
        # Element ID / Neo4j ID is the string UUID
        nid = str(db_ent.id)
        await entity_repo.set_neo4j_id(db_ent.id, nid)
        
        # Link to specific chunk UUID if index is valid
        associated_chunks = []
        chunk_row_id = None
        if 0 <= ext_ent.source_chunk_index < len(chunk_uuids):
            cuuid = chunk_uuids[ext_ent.source_chunk_index]
            associated_chunks.append(cuuid)
            chunk_row_id = chunk_id_map.get(cuuid)
            
        # Write Entity node in Neo4j
        await graph_writer.merge_entity(
            entity_id=db_ent.id,
            name=db_ent.canonical_name,
            entity_type=db_ent.entity_type.value,
            plant_id=plant_id,
            document_id=doc.id,
            chunk_uuids=associated_chunks,
            confidence=ext_ent.confidence,
            attributes=db_ent.attributes
        )
        
        # Write EntityMention in Postgres
        await entity_repo.create_mention(
            entity_id=db_ent.id,
            doc_id=doc.id,
            chunk_id=chunk_row_id,
            page_number=ext_ent.source_chunk_index + 1 if chunk_row_id else 1,
            surface_text=ext_ent.surface_text,
            confidence=ext_ent.confidence
        )
        
    # 5e. Merge Relationships in Neo4j
    for r in rels:
        src_key = r.source_entity.strip().lower()
        tgt_key = r.target_entity.strip().lower()
        
        src_info = entity_map.get(src_key)
        tgt_info = entity_map.get(tgt_key)
        
        # Fallback search by substring or attribute if exact name not in map
        if not src_info:
            for name, info in entity_map.items():
                if src_key in name or name in src_key:
                    src_info = info
                    break
        if not tgt_info:
            for name, info in entity_map.items():
                if tgt_key in name or name in tgt_key:
                    tgt_info = info
                    break
                    
        if src_info and tgt_info:
            src_id, src_type = src_info
            tgt_id, tgt_type = tgt_info
            
            associated_chunks = []
            if 0 <= r.source_chunk_index < len(chunk_uuids):
                associated_chunks.append(chunk_uuids[r.source_chunk_index])
                
            await graph_writer.merge_relationship(
                src_id=src_id,
                src_type=src_type,
                tgt_id=tgt_id,
                tgt_type=tgt_type,
                rel_type=r.type,
                document_id=doc.id,
                chunk_uuids=associated_chunks,
                confidence=r.confidence
            )
            
    # 5f. Qdrant Write
    if blocks.prose:
        await vector_writer.upsert_chunks(
            doc_id=doc.id,
            doc_type=doc.doc_type.value,
            plant_id=plant_id,
            effective_date=doc.effective_date,
            prose_blocks=blocks.prose,
            chunk_uuids=chunk_uuids,
            resolved_pairs=resolved_pairs
        )
        
    await vector_writer.upsert_entities(plant_id, resolved_pairs)
    await db.flush()
