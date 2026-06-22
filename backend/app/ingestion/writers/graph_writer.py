import logging
from uuid import UUID
from datetime import date
from typing import List, Dict, Any
from app.db.neo4j import neo4j_client

logger = logging.getLogger(__name__)

LABEL_MAP = {
    "asset": "Asset",
    "measurement": "Measurement",
    "lubricant": "Lubricant",
    "failure_mode": "FailureMode",
    "cause": "Cause",
    "symptom": "Symptom",
    "procedure": "Procedure",
    "regulation": "Regulation",
    "requirement": "ComplianceRequirement",
    "spare": "Spare",
    "material": "Material",
    "person": "Person",
    "role": "Role",
    "lesson": "LessonLearned",
    "tribal_note": "TribalNote"
}


class GraphWriter:
    async def upsert_document(self, doc_id: UUID, title: str, doc_type: str, effective_date: Optional[date] = None) -> None:
        query = """
        MERGE (d:Document {id: $id})
        ON CREATE SET d.title = $title, d.doc_type = $doc_type, d.effective_date = $effective_date, d.created_at = datetime()
        ON MATCH SET d.title = $title, d.doc_type = $doc_type, d.effective_date = $effective_date
        """
        params = {
            "id": str(doc_id),
            "title": title,
            "doc_type": doc_type,
            "effective_date": str(effective_date) if effective_date else None
        }
        await neo4j_client.run(query, params)

    async def upsert_chunks(self, doc_id: UUID, prose_blocks: List[Any], chunk_uuids: List[UUID]) -> None:
        for idx, (block, cuuid) in enumerate(zip(prose_blocks, chunk_uuids)):
            query = """
            MERGE (c:Chunk {id: $chunk_id})
            ON CREATE SET c.page_number = $page_number, c.chunk_index = $chunk_index, c.text = $text, c.section_path = $section_path, c.created_at = datetime()
            WITH c
            MATCH (d:Document {id: $document_id})
            MERGE (c)-[:FROM]->(d)
            """
            params = {
                "chunk_id": str(cuuid),
                "page_number": getattr(block, "page_number", 1),
                "chunk_index": idx,
                "text": getattr(block, "text", str(block)),
                "section_path": getattr(block, "section_path", None),
                "document_id": str(doc_id)
            }
            await neo4j_client.run(query, params)

    async def merge_entity(
        self,
        entity_id: UUID,
        name: str,
        entity_type: str,
        plant_id: UUID,
        document_id: UUID,
        chunk_uuids: List[UUID],
        confidence: float,
        attributes: Dict[str, Any]
    ) -> None:
        label = LABEL_MAP.get(entity_type.lower(), "Entity")
        
        # Build specific merge queries based on type
        if label == "Asset":
            query = """
            MERGE (e:Asset {plant_id: $plant_id, tag: $tag})
            ON CREATE SET e.id = $id, e.name = $name, e.created_at = datetime()
            SET e.source_document_ids = apoc.coll.toSet(coalesce(e.source_document_ids, []) + [$document_id]),
                e.confidence = $confidence,
                e.criticality = coalesce($criticality, e.criticality),
                e.asset_type = coalesce($asset_type, e.asset_type),
                e.manufacturer = coalesce($manufacturer, e.manufacturer),
                e.model = coalesce($model, e.model)
            """
            params = {
                "id": str(entity_id),
                "name": name,
                "plant_id": str(plant_id),
                "tag": attributes.get("tag", name),
                "criticality": attributes.get("criticality", "medium"),
                "asset_type": attributes.get("asset_type"),
                "manufacturer": attributes.get("manufacturer"),
                "model": attributes.get("model"),
                "document_id": str(document_id),
                "confidence": confidence
            }
        elif label == "Measurement":
            query = """
            MERGE (e:Measurement {parameter: $parameter, value: $value, unit: $unit})
            ON CREATE SET e.id = $id, e.name = $name, e.created_at = datetime()
            SET e.source_document_ids = apoc.coll.toSet(coalesce(e.source_document_ids, []) + [$document_id]),
                e.confidence = $confidence
            """
            params = {
                "id": str(entity_id),
                "name": name,
                "parameter": attributes.get("parameter", name),
                "value": float(attributes.get("value", 0.0)) if attributes.get("value") is not None else None,
                "unit": attributes.get("unit"),
                "document_id": str(document_id),
                "confidence": confidence
            }
        else:
            query = f"""
            MERGE (e:{label} {{name: $name}})
            ON CREATE SET e.id = $id, e.created_at = datetime()
            SET e.source_document_ids = apoc.coll.toSet(coalesce(e.source_document_ids, []) + [$document_id]),
                e.confidence = $confidence
            """
            params = {
                "id": str(entity_id),
                "name": name,
                "document_id": str(document_id),
                "confidence": confidence
            }
            
        await neo4j_client.run(query, params)
        
        # Link entity to document
        link_doc_query = f"""
        MATCH (e:{label} {{id: $id}}), (d:Document {{id: $document_id}})
        MERGE (e)-[:MENTIONED_IN]->(d)
        """
        await neo4j_client.run(link_doc_query, {"id": str(entity_id), "document_id": str(document_id)})
        
        # Link entity to chunks
        if chunk_uuids:
            chunk_ids_str = [str(cu) for cu in chunk_uuids]
            link_chunks_query = f"""
            MATCH (e:{label} {{id: $id}})
            UNWIND $chunk_ids AS cid
            MATCH (c:Chunk {{id: cid}})
            MERGE (e)-[:EVIDENCED_BY]->(c)
            """
            await neo4j_client.run(link_chunks_query, {"id": str(entity_id), "chunk_ids": chunk_ids_str})

    async def merge_relationship(
        self,
        src_id: UUID,
        src_type: str,
        tgt_id: UUID,
        tgt_type: str,
        rel_type: str,
        document_id: UUID,
        chunk_uuids: List[UUID],
        confidence: float
    ) -> None:
        src_label = LABEL_MAP.get(src_type.lower(), "Entity")
        tgt_label = LABEL_MAP.get(tgt_type.lower(), "Entity")
        
        # Standardize relationship type
        rel_type = rel_type.strip().upper()
        
        query = f"""
        MATCH (src:{src_label} {{id: $src_id}}), (tgt:{tgt_label} {{id: $tgt_id}})
        MERGE (src)-[r:{rel_type}]->(tgt)
        ON CREATE SET r.created_at = datetime()
        SET r.source_document_ids = apoc.coll.toSet(coalesce(r.source_document_ids, []) + [$document_id]),
            r.confidence = $confidence
        """
        params = {
            "src_id": str(src_id),
            "tgt_id": str(tgt_id),
            "document_id": str(document_id),
            "confidence": confidence
        }
        await neo4j_client.run(query, params)
        
        # Link relationship to chunks
        if chunk_uuids:
            chunk_ids_str = [str(cu) for cu in chunk_uuids]
            link_query = f"""
            MATCH (src:{src_label} {{id: $src_id}})-[r:{rel_type}]->(tgt:{tgt_label} {{id: $tgt_id}})
            UNWIND $chunk_ids AS cid
            MATCH (c:Chunk {{id: cid}})
            MERGE (r)-[:EVIDENCED_BY]->(c)
            """
            await neo4j_client.run(link_query, {
                "src_id": str(src_id),
                "tgt_id": str(tgt_id),
                "chunk_ids": chunk_ids_str
            })


# For type hints
from typing import Optional
