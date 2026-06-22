import logging
from typing import List, Tuple, Dict
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Entity, EntityType
from app.llm.gateway import llm_gateway
from app.ingestion.stage2_route import RoutedBlocks
from app.ingestion.stage3_entities import ExtractedEntity

logger = logging.getLogger(__name__)


class ExtractedRelationship(BaseModel):
    source_entity: str
    target_entity: str
    type: str
    attributes: dict = Field(default_factory=dict)
    source_chunk_index: int
    confidence: float


class ExtractedRelationshipsList(BaseModel):
    relationships: List[ExtractedRelationship] = Field(default_factory=list)


def deterministic_extract_relationships(
    resolved_pairs: List[Tuple[ExtractedEntity, Entity]]
) -> List[ExtractedRelationship]:
    relationships = []
    
    # Group entities by chunk index
    chunk_ents: Dict[int, List[Tuple[ExtractedEntity, Entity]]] = {}
    for ext_ent, db_ent in resolved_pairs:
        idx = ext_ent.source_chunk_index
        if idx not in chunk_ents:
            chunk_ents[idx] = []
        chunk_ents[idx].append((ext_ent, db_ent))
        
    for idx, ents in chunk_ents.items():
        # Look for Asset, Measurement, Lubricant, FailureMode in the same chunk
        assets = [e for e in ents if e[1].entity_type == EntityType.asset]
        measurements = [e for e in ents if e[1].entity_type == EntityType.measurement]
        lubricants = [e for e in ents if e[1].entity_type == EntityType.lubricant]
        failure_modes = [e for e in ents if e[1].entity_type == EntityType.failure_mode]
        
        for asset_pair in assets:
            asset_ent = asset_pair[1]
            
            # Asset HAS_SPEC Measurement
            for meas_pair in measurements:
                meas_ent = meas_pair[1]
                relationships.append(ExtractedRelationship(
                    source_entity=asset_ent.canonical_name,
                    target_entity=meas_ent.canonical_name,
                    type="HAS_SPEC",
                    source_chunk_index=idx,
                    confidence=1.0
                ))
                
            # Asset USES_LUBRICANT Lubricant
            for lub_pair in lubricants:
                lub_ent = lub_pair[1]
                relationships.append(ExtractedRelationship(
                    source_entity=asset_ent.canonical_name,
                    target_entity=lub_ent.canonical_name,
                    type="USES_LUBRICANT",
                    source_chunk_index=idx,
                    confidence=1.0
                ))
                
            # Asset HAS_FAILURE_MODE FailureMode
            for fm_pair in failure_modes:
                fm_ent = fm_pair[1]
                relationships.append(ExtractedRelationship(
                    source_entity=asset_ent.canonical_name,
                    target_entity=fm_ent.canonical_name,
                    type="HAS_FAILURE_MODE",
                    source_chunk_index=idx,
                    confidence=1.0
                ))
                
    return relationships


async def stage4_relationships(
    db: AsyncSession,
    doc_id: UUID,
    blocks: RoutedBlocks,
    resolved_pairs: List[Tuple[ExtractedEntity, Entity]],
    job
) -> List[ExtractedRelationship]:
    # Group entities by chunk index
    chunk_ents: Dict[int, List[Tuple[ExtractedEntity, Entity]]] = {}
    for ext_ent, db_ent in resolved_pairs:
        idx = ext_ent.source_chunk_index
        if idx not in chunk_ents:
            chunk_ents[idx] = []
        chunk_ents[idx].append((ext_ent, db_ent))

    system_instruction = (
        "You are NEURON IQ, an industrial knowledge intelligence engine for plant operations.\n"
        "Rules you never break:\n"
        "1. Ground every factual claim in provided sources or graph facts. If evidence is\n"
        "   absent or insufficient, say so explicitly — never invent values, tags, dates, or specs.\n"
        "2. When you state a measurement/spec, include its unit and cite the source. If sources\n"
        "   disagree, surface the conflict rather than picking one silently.\n"
        "3. Be precise and terse. Engineers read this. No filler, no hedging beyond stated confidence.\n"
        "4. Respect the user's role and plant scope; never reference assets outside their plant.\n"
        "Output strictly in the requested schema when one is provided."
    )
    
    extracted_rels: List[ExtractedRelationship] = []
    
    # Try calling LLM for chunks with >= 2 entities
    for idx, block in enumerate(blocks.prose):
        ents_in_chunk = chunk_ents.get(idx, [])
        if len(ents_in_chunk) < 2:
            continue
            
        entities_prompt_str = "\n".join(
            f"- ID: {db_ent.id}, Name: '{db_ent.canonical_name}', Type: {db_ent.entity_type.value}"
            for _, db_ent in ents_in_chunk
        )
        
        user_prompt = (
            "Given the ENTITIES (with ids) and the TEXT they appear in, extract directed relationships.\n"
            "Allowed types: PART_OF, INSTANCE_OF, CONNECTED_TO, INSTRUMENTED_BY, GOVERNS, SPECIFIES,\n"
            "HAS_SPEC, RECORDED_VALUE, PERFORMED_ON, FOLLOWS, REQUIRES_SPARE, USES_LUBRICANT,\n"
            "OCCURRED_ON, HAS_FAILURE_MODE, CAUSED_BY, MANIFESTS_AS, ASSOCIATED_WITH, MITIGATES,\n"
            "REQUIRES, APPLIES_TO, SATISFIES, HAS_EXPERTISE_ON, AUTHORED, ABOUT, DERIVED_FROM.\n"
            "Only assert a relationship explicitly supported by the text. Set confidence 0..1.\n\n"
            f"ENTITIES:\n{entities_prompt_str}\n\n"
            f"TEXT:\n{block.text}\n\n"
            "Return: [{source_entity, target_entity, type, attributes, source_chunk_index, confidence}]"
        )
        
        llm_failed = False
        try:
            res = await llm_gateway.generate(
                system=system_instruction,
                user=user_prompt,
                response_schema=ExtractedRelationshipsList
            )
            if res and hasattr(res, "relationships"):
                for rel in res.relationships:
                    rel.source_chunk_index = idx
                    extracted_rels.append(rel)
            else:
                llm_failed = True
        except Exception as e:
            logger.warning(f"Gemini relationship extraction failed: {e}. Falling back to deterministic logic.")
            llm_failed = True
            
        if llm_failed:
            if job:
                job.error = "llm_enrichment_pending"
                
    # Always include deterministic relationships to ensure safety and completeness
    det_rels = deterministic_extract_relationships(resolved_pairs)
    
    # Merge and dedup extracted_rels and det_rels
    seen = set()
    final_rels = []
    
    for r in (extracted_rels + det_rels):
        key = (r.source_entity.strip().lower(), r.target_entity.strip().lower(), r.type.strip().upper())
        if key not in seen:
            seen.add(key)
            final_rels.append(r)
            
    return final_rels
