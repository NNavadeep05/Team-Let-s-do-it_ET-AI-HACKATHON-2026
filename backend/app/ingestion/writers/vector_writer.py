import uuid
import logging
import datetime
from typing import List, Dict, Any, Tuple
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, SparseVector
from app.config import settings
from app.llm.embeddings import embeddings_service
from app.llm.sparse import sparse_service
from app.ingestion.stage2_route import ProseBlock
from app.ingestion.stage3_entities import ExtractedEntity
from app.db.models import Entity

logger = logging.getLogger(__name__)

# Lazy initialization of Qdrant client
_qdrant_client = None


def get_qdrant() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    return _qdrant_client


class VectorWriter:
    def __init__(self):
        self.namespace = uuid.NAMESPACE_DNS

    async def upsert_chunks(
        self,
        doc_id: UUID,
        doc_type: str,
        plant_id: UUID,
        effective_date: Any,
        prose_blocks: List[ProseBlock],
        chunk_uuids: List[UUID],
        resolved_pairs: List[Tuple[ExtractedEntity, Entity]]
    ) -> None:
        if not prose_blocks:
            return

        texts = [b.text for b in prose_blocks]
        
        # 1. Embed dense vectors
        dense_vectors = await embeddings_service.embed(texts)
        
        # 2. Sparse encode
        sparse_vectors = sparse_service.encode(texts)
        
        # Recency timestamp
        recency_ts = 0
        if effective_date:
            if isinstance(effective_date, (datetime.date, datetime.datetime)):
                recency_ts = int(datetime.datetime.combine(effective_date, datetime.time.min).timestamp())
            elif isinstance(effective_date, str):
                try:
                    recency_ts = int(datetime.datetime.fromisoformat(effective_date).timestamp())
                except ValueError:
                    pass

        # 3. Match asset tags and entity IDs per chunk
        chunk_asset_tags: Dict[int, List[str]] = {}
        chunk_entity_ids: Dict[int, List[str]] = {}
        
        for ext_ent, db_ent in resolved_pairs:
            idx = ext_ent.source_chunk_index
            if idx not in chunk_entity_ids:
                chunk_entity_ids[idx] = []
            chunk_entity_ids[idx].append(str(db_ent.id))
            
            if db_ent.entity_type.value == "asset":
                if idx not in chunk_asset_tags:
                    chunk_asset_tags[idx] = []
                chunk_asset_tags[idx].append(db_ent.canonical_name)

        # 4. Build Qdrant PointStruct list
        points = []
        for idx, (block, cuuid, dense, sparse) in enumerate(zip(
            prose_blocks, chunk_uuids, dense_vectors, sparse_vectors
        )):
            payload = {
                "document_id": str(doc_id),
                "document_type": doc_type,
                "plant_id": str(plant_id),
                "page_number": block.page_number,
                "asset_tags": chunk_asset_tags.get(idx, []),
                "entity_ids": chunk_entity_ids.get(idx, []),
                "section_path": block.section_path or "",
                "recency_ts": recency_ts,
                "confidence": 1.0,
                "text": block.text
            }
            
            points.append(PointStruct(
                id=str(cuuid),
                vector={
                    "dense": dense,
                    "sparse": SparseVector(
                        indices=sparse["indices"],
                        values=sparse["values"]
                    )
                },
                payload=payload
            ))

        try:
            client = get_qdrant()
            client.upsert("neuron_chunks", points)
            logger.info(f"Successfully upserted {len(points)} chunk vectors to Qdrant")
        except Exception as e:
            logger.warning(f"Failed to upsert chunk vectors to Qdrant: {e}")

    async def upsert_entities(
        self,
        plant_id: UUID,
        resolved_pairs: List[Tuple[ExtractedEntity, Entity]]
    ) -> None:
        if not resolved_pairs:
            return
            
        # Group unique canonical entities
        unique_entities = {}
        for _, db_ent in resolved_pairs:
            unique_entities[db_ent.id] = db_ent
            
        points = []
        for ent_id, db_ent in unique_entities.items():
            # Build entity description
            desc = f"Name: {db_ent.canonical_name}, Type: {db_ent.entity_type.value}"
            if db_ent.attributes:
                desc += f", Attributes: {db_ent.attributes}"
                
            # Embed description
            vectors = await embeddings_service.embed([desc])
            if not vectors:
                continue
                
            payload = {
                "entity_id": str(ent_id),
                "entity_type": db_ent.entity_type.value,
                "plant_id": str(plant_id),
                "name": db_ent.canonical_name,
                "description": desc
            }
            
            points.append(PointStruct(
                id=str(ent_id),
                vector={"dense": vectors[0]},
                payload=payload
            ))
            
        try:
            client = get_qdrant()
            client.upsert("neuron_entities", points)
            logger.info(f"Successfully upserted {len(points)} entity vectors to Qdrant")
        except Exception as e:
            logger.warning(f"Failed to upsert entity vectors to Qdrant: {e}")
