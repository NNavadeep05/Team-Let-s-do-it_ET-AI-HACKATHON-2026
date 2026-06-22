import os
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, SparseVectorParams, SparseIndexParams,
    PayloadSchemaType,
)

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")


def init_qdrant():
    print(f"Initializing Qdrant collections at {QDRANT_URL}...")
    client = QdrantClient(url=QDRANT_URL)

    # 3.1 Document chunks (primary retrieval)
    print("Recreating collection: 'neuron_chunks'")
    client.recreate_collection(
        collection_name="neuron_chunks",
        vectors_config={"dense": VectorParams(size=3072, distance=Distance.COSINE)},
        sparse_vectors_config={"sparse": SparseVectorParams(index=SparseIndexParams())},
    )

    # Payload schema (indexed fields for fast filtering)
    print("Creating payload indices for 'neuron_chunks'")
    fields = {
        "document_id":   PayloadSchemaType.KEYWORD,
        "document_type": PayloadSchemaType.KEYWORD,
        "plant_id":      PayloadSchemaType.KEYWORD,
        "page_number":   PayloadSchemaType.INTEGER,
        "asset_tags":    PayloadSchemaType.KEYWORD,   # list of tags this chunk mentions
        "entity_ids":    PayloadSchemaType.KEYWORD,   # list of canonical entity ids
        "section_path":  PayloadSchemaType.TEXT,
        "recency_ts":    PayloadSchemaType.INTEGER,   # effective_date epoch, for recency boost
        "confidence":    PayloadSchemaType.FLOAT,
    }
    for field, ftype in fields.items():
        client.create_payload_index("neuron_chunks", field_name=field, field_schema=ftype)

    # 3.2 Entity descriptions (entity-level semantic lookup for graph augmentation)
    print("Recreating collection: 'neuron_entities'")
    client.recreate_collection(
        collection_name="neuron_entities",
        vectors_config={"dense": VectorParams(size=3072, distance=Distance.COSINE)},
    )
    
    print("Creating payload indices for 'neuron_entities'")
    entity_fields = {
        "entity_id":   PayloadSchemaType.KEYWORD,
        "entity_type": PayloadSchemaType.KEYWORD,
        "plant_id":    PayloadSchemaType.KEYWORD,
    }
    for field, ftype in entity_fields.items():
        client.create_payload_index("neuron_entities", field_name=field, field_schema=ftype)

    print("Qdrant initialization complete.")


if __name__ == "__main__":
    init_qdrant()
