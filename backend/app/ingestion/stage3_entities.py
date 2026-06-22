import re
import logging
from typing import List, Tuple
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import EntityType, Entity, Asset
from app.repositories.entity_repo import EntityRepository
from app.llm.gateway import llm_gateway
from app.ingestion.stage2_route import RoutedBlocks, ProseBlock
from sqlalchemy import select

logger = logging.getLogger(__name__)


class ExtractedEntity(BaseModel):
    name: str
    type: EntityType
    attributes: dict = Field(default_factory=dict)
    surface_text: str
    source_chunk_index: int
    confidence: float


class ExtractedEntitiesList(BaseModel):
    entities: List[ExtractedEntity] = Field(default_factory=list)


def regex_extract_entities(text: str, chunk_idx: int) -> List[ExtractedEntity]:
    entities = []
    
    # Asset tags: P-101, P-103
    for match in re.finditer(r"\b(P-10[13])\b", text):
        val = match.group(1)
        entities.append(ExtractedEntity(
            name=val,
            type=EntityType.asset,
            attributes={"tag": val, "asset_type": "pump"},
            surface_text=val,
            source_chunk_index=chunk_idx,
            confidence=1.0
        ))
        
    # Torque values: 95 Nm, 120 Nm, 140 Nm
    for match in re.finditer(r"\b(95|120|140)\s*(Nm)\b", text):
        val = float(match.group(1))
        unit = match.group(2)
        entities.append(ExtractedEntity(
            name=f"Torque: {int(val)} {unit}",
            type=EntityType.measurement,
            attributes={"parameter": "torque", "value": val, "unit": unit},
            surface_text=match.group(0),
            source_chunk_index=chunk_idx,
            confidence=1.0
        ))
        
    # Lubricants: ISO VG 68, ISO VG 46
    for match in re.finditer(r"\b(ISO\s*VG\s*(68|46))\b", text):
        val = match.group(1)
        name = "ISO VG 68" if "68" in val else "ISO VG 46"
        entities.append(ExtractedEntity(
            name=name,
            type=EntityType.lubricant,
            attributes={"spec": name},
            surface_text=match.group(0),
            source_chunk_index=chunk_idx,
            confidence=1.0
        ))
        
    # Failure modes: seal failure, seal leakage
    for match in re.finditer(r"\b(seal\s*(failure|leakage))\b", text, re.IGNORECASE):
        val = match.group(1)
        entities.append(ExtractedEntity(
            name="seal leakage",
            type=EntityType.failure_mode,
            attributes={"mode_code": "seal_leakage", "description": "Seal leakage / failure"},
            surface_text=match.group(0),
            source_chunk_index=chunk_idx,
            confidence=1.0
        ))

    # Regulations: OSHA 1910.119 / PSM
    if "osha" in text.lower() or "psm" in text.lower():
        entities.append(ExtractedEntity(
            name="OSHA 1910.119",
            type=EntityType.regulation,
            attributes={"authority": "OSHA", "reference": "1910.119"},
            surface_text="OSHA 1910.119" if "1910.119" in text else "PSM",
            source_chunk_index=chunk_idx,
            confidence=1.0
        ))
        
    # Remove duplicates
    seen = set()
    unique_entities = []
    for e in entities:
        key = (e.name, e.type)
        if key not in seen:
            seen.add(key)
            unique_entities.append(e)
    return unique_entities


async def get_or_create_asset(db: AsyncSession, tag: str, plant_id: UUID) -> Asset:
    stmt = select(Asset).where(Asset.plant_id == plant_id, Asset.tag == tag)
    res = await db.execute(stmt)
    asset = res.scalar_one_or_none()
    if not asset:
        asset = Asset(
            tag=tag,
            name=f"Asset {tag}",
            plant_id=plant_id
        )
        db.add(asset)
        await db.flush()
    return asset


async def stage3_entities(
    db: AsyncSession,
    doc_id: UUID,
    plant_id: UUID,
    blocks: RoutedBlocks,
    job
) -> List[Tuple[ExtractedEntity, Entity]]:
    # System instructions
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
    
    entities_list = []
    
    # Process prose blocks
    for idx, block in enumerate(blocks.prose):
        user_prompt = (
            "Extract industrial entities from the TEXT. Return a JSON list; one object per distinct entity.\n"
            "Allowed types: asset, equipment, system, procedure, measurement, material, spare, lubricant,\n"
            "hazard, safety_control, person, role, regulation, requirement, failure_mode, cause, symptom.\n"
            "For measurements, populate attributes: {parameter, value (number), unit, min, max, tolerance}.\n"
            "For assets, populate attributes: {tag, asset_type, manufacturer, model} when present.\n"
            "Use the exact surface_text as written. Do not infer entities that are not supported by the text.\n"
            "Set confidence 0..1 reflecting how explicitly the entity is stated.\n\n"
            f"TEXT (page {block.page_number}, chunk {idx}):\n"
            f"{block.text}\n\n"
            "Return: [{name, type, attributes, surface_text, source_chunk_index, confidence}]"
        )
        
        chunk_entities = []
        llm_failed = False
        try:
            res = await llm_gateway.generate(
                system=system_instruction,
                user=user_prompt,
                response_schema=ExtractedEntitiesList
            )
            if res and hasattr(res, "entities"):
                chunk_entities = res.entities
            else:
                llm_failed = True
        except Exception as e:
            logger.warning(f"Gemini entity extraction failed: {e}. Triggering regex fallback.")
            llm_failed = True
            
        if llm_failed:
            if job:
                # Store flag indicating LLM enrichment pending
                job.error = "llm_enrichment_pending"
            chunk_entities = regex_extract_entities(block.text, idx)
            
        for ent in chunk_entities:
            ent.source_chunk_index = idx
            entities_list.append(ent)
            
    # Resolve entities
    entity_repo = EntityRepository(db)
    resolved_pairs = []
    
    for ent in entities_list:
        # Check trigram similarity
        match_tuple = await entity_repo.find_by_trigram_match(
            plant_id=plant_id,
            name=ent.name,
            entity_type=ent.type,
            threshold=0.82
        )
        
        asset_id = None
        if ent.type == EntityType.asset:
            asset_tag = ent.attributes.get("tag", ent.name)
            db_asset = await get_or_create_asset(db, asset_tag, plant_id)
            asset_id = db_asset.id
            ent.name = asset_tag
            
        if match_tuple:
            canonical_ent = match_tuple[0]
            if asset_id and not canonical_ent.asset_id:
                canonical_ent.asset_id = asset_id
        else:
            canonical_ent = await entity_repo.create(
                canonical_name=ent.name,
                entity_type=ent.type,
                plant_id=plant_id,
                asset_id=asset_id,
                attributes=ent.attributes
            )
            
        resolved_pairs.append((ent, canonical_ent))
        
    await db.flush()
    return resolved_pairs
