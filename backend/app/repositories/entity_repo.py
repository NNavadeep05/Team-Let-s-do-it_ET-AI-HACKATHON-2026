from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Entity, EntityMention, EntityType


class EntityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, entity_id: UUID) -> Optional[Entity]:
        """Fetch entity by ID."""
        return await self.db.get(Entity, entity_id)

    async def find_by_name_and_type(
        self,
        plant_id: UUID,
        name: str,
        entity_type: EntityType
    ) -> Optional[Entity]:
        """Find entity by exact canonical name and type."""
        stmt = select(Entity).where(
            Entity.plant_id == plant_id,
            Entity.canonical_name == name,
            Entity.entity_type == entity_type
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_trigram_match(
        self,
        plant_id: UUID,
        name: str,
        entity_type: EntityType,
        threshold: float = 0.82
    ) -> Optional[Tuple[Entity, float]]:
        """
        Find near-duplicate entity in the plant using pg_trgm similarity.
        Falls back to a python-level difflib check on SQLite.
        """
        # Check if running on SQLite (testing)
        dialect_name = self.db.bind.dialect.name
        if dialect_name == "sqlite":
            # SQLite fallback: fetch all entities of that type and check using difflib
            stmt = select(Entity).where(
                Entity.plant_id == plant_id,
                Entity.entity_type == entity_type
            )
            res = await self.db.execute(stmt)
            entities = res.scalars().all()
            
            import difflib
            best_match = None
            best_score = 0.0
            
            for ent in entities:
                # Calculate sequence matcher ratio
                score = difflib.SequenceMatcher(None, ent.canonical_name.lower(), name.lower()).ratio()
                if score >= threshold and score > best_score:
                    best_score = score
                    best_match = ent
                    
            if best_match:
                return best_match, best_score
            return None

        # Production Postgres query using pg_trgm similarity()
        similarity_col = func.similarity(Entity.canonical_name, name).label("similarity")
        stmt = (
            select(Entity, similarity_col)
            .where(
                Entity.plant_id == plant_id,
                Entity.entity_type == entity_type,
                similarity_col >= threshold
            )
            .order_by(text("similarity DESC"))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        row = result.first()
        if row:
            return row[0], float(row[1])
        return None

    async def create(
        self,
        canonical_name: str,
        entity_type: EntityType,
        plant_id: Optional[UUID] = None,
        asset_id: Optional[UUID] = None,
        neo4j_node_id: Optional[str] = None,
        attributes: Optional[dict] = None
    ) -> Entity:
        """Create a new canonical entity."""
        entity = Entity(
            canonical_name=canonical_name,
            entity_type=entity_type,
            plant_id=plant_id,
            asset_id=asset_id,
            neo4j_node_id=neo4j_node_id,
            attributes=attributes or {}
        )
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def set_neo4j_id(self, entity_id: UUID, nid: str) -> Optional[Entity]:
        """Associate the Neo4j node ID with the Postgres record."""
        entity = await self.get(entity_id)
        if entity:
            entity.neo4j_node_id = nid
            await self.db.flush()
        return entity

    async def create_mention(
        self,
        entity_id: UUID,
        doc_id: UUID,
        chunk_id: Optional[UUID] = None,
        page_number: Optional[int] = None,
        surface_text: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> EntityMention:
        """Create a mention record linking the entity to a specific document chunk."""
        mention = EntityMention(
            entity_id=entity_id,
            document_id=doc_id,
            chunk_id=chunk_id,
            page_number=page_number,
            surface_text=surface_text,
            confidence=confidence
        )
        self.db.add(mention)
        await self.db.flush()
        return mention
