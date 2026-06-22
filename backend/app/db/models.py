import enum
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime, Numeric,
    ForeignKey, Table, UniqueConstraint, Index, Date, Enum, text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, CITEXT
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base

# ==========================================
# ENUMS
# ==========================================

class UserRole(str, enum.Enum):
    admin = "admin"
    technician = "technician"
    manager = "manager"
    compliance_officer = "compliance_officer"
    plant_head = "plant_head"


class DocumentType(str, enum.Enum):
    pid = "pid"
    sop = "sop"
    work_order = "work_order"
    inspection_report = "inspection_report"
    maintenance_log = "maintenance_log"
    regulatory = "regulatory"
    equipment_manual = "equipment_manual"
    email = "email"
    excel = "excel"
    incident_report = "incident_report"


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class IngestStage(str, enum.Enum):
    parse_ocr = "parse_ocr"
    extract_layout = "extract_layout"
    extract_entities = "extract_entities"
    resolve_entities = "resolve_entities"
    extract_relationships = "extract_relationships"
    write_stores = "write_stores"
    scoring = "scoring"
    done = "done"


class EntityType(str, enum.Enum):
    asset = "asset"
    equipment = "equipment"
    system = "system"
    procedure = "procedure"
    material = "material"
    spare = "spare"
    lubricant = "lubricant"
    hazard = "hazard"
    safety_control = "safety_control"
    person = "person"
    role = "role"
    regulation = "regulation"
    requirement = "requirement"
    measurement = "measurement"
    failure_mode = "failure_mode"
    cause = "cause"
    symptom = "symptom"
    lesson = "lesson"
    tribal_note = "tribal_note"


class Criticality(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class FindingStatus(str, enum.Enum):
    compliant = "compliant"
    gap = "gap"
    conflict = "conflict"
    expired = "expired"


class ContradictionKind(str, enum.Enum):
    spec_value = "spec_value"
    procedure_step = "procedure_step"
    schedule = "schedule"
    status = "status"
    safety_limit = "safety_limit"


class Severity(str, enum.Enum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class CaptureType(str, enum.Enum):
    voice = "voice"
    text = "text"
    email = "email"
    image = "image"


# ==========================================
# TABLES
# ==========================================

class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String)
    neo4j_node_id: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    users = relationship("User", back_populates="plant")
    assets = relationship("Asset", back_populates="plant")
    documents = relationship("Document", back_populates="plant")
    entities = relationship("Entity", back_populates="plant")


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.technician, nullable=False)
    plant_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("plants.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    plant = relationship("Plant", back_populates="users")
    uploaded_documents = relationship("Document", back_populates="uploader")
    reviewed_rcas = relationship("RCAReport", back_populates="reviewer")
    resolved_contradictions = relationship("Contradiction", back_populates="resolver")
    tribal_notes = relationship("TribalKnowledge", back_populates="author")
    chat_sessions = relationship("ChatSession", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("plant_id", "tag", name="uq_assets_plant_tag"),
        Index("ix_assets_tag", "tag"),
        Index("ix_assets_plant", "plant_id"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tag: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    asset_type: Mapped[Optional[str]] = mapped_column(String)
    iso14224_class: Mapped[Optional[str]] = mapped_column(String)
    plant_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("plants.id"))
    location: Mapped[Optional[str]] = mapped_column(String)
    criticality: Mapped[Criticality] = mapped_column(Enum(Criticality), default=Criticality.medium, nullable=False)
    manufacturer: Mapped[Optional[str]] = mapped_column(String)
    model: Mapped[Optional[str]] = mapped_column(String)
    install_date: Mapped[Optional[date]] = mapped_column(Date)
    neo4j_node_id: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    plant = relationship("Plant", back_populates="assets")
    entities = relationship("Entity", back_populates="asset")
    work_orders = relationship("WorkOrder", back_populates="asset")
    incidents = relationship("Incident", back_populates="asset")
    compliance_findings = relationship("ComplianceFinding", back_populates="asset")
    contradictions = relationship("Contradiction", back_populates="asset")
    tribal_notes = relationship("TribalKnowledge", back_populates="asset")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_type_status", "doc_type", "status"),
        Index("ix_documents_plant", "plant_id"),
        Index("ix_documents_effective", "effective_date"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    doc_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.uploaded, nullable=False)
    storage_key: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String, nullable=False)
    page_count: Mapped[Optional[int]] = mapped_column(Integer)
    plant_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("plants.id"))
    uploaded_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    supersedes_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("documents.id"))
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    plant = relationship("Plant", back_populates="documents")
    uploader = relationship("User", back_populates="uploaded_documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    jobs = relationship("IngestionJob", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    entity_mentions = relationship("EntityMention", back_populates="document", cascade="all, delete-orphan")
    work_orders = relationship("WorkOrder", back_populates="document")
    incidents = relationship("Incident", back_populates="document")
    compliance_findings = relationship("ComplianceFinding", back_populates="document")


class DocumentPage(Base):
    __tablename__ = "document_pages"
    __table_args__ = (
        UniqueConstraint("document_id", "page_number", name="uq_pages_document_page"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    image_key: Mapped[Optional[str]] = mapped_column(String)
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    ocr_confidence: Mapped[Optional[float]] = mapped_column(Numeric(4, 3))

    document = relationship("Document", back_populates="pages")


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    stage: Mapped[IngestStage] = mapped_column(Enum(IngestStage), default=IngestStage.parse_ocr, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    progress: Mapped[float] = mapped_column(Numeric(4, 3), default=0.000, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    document = relationship("Document", back_populates="jobs")


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_chunks_document_index"),
        Index("ix_chunks_document", "document_id"),
        Index("ix_chunks_fts", text("to_tsvector('english', content)"), postgres_using="gin"),
        Index("ix_chunks_meta", "metadata", postgres_using="gin"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer)
    section_path: Mapped[Optional[str]] = mapped_column(String)
    qdrant_point_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    metadata: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    document = relationship("Document", back_populates="chunks")
    mentions = relationship("EntityMention", back_populates="chunk")


class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = (
        Index("ix_entities_name_trgm", "canonical_name", postgres_using="gin", postgres_ops={"canonical_name": "gin_trgm_ops"}),
        Index("ix_entities_type", "entity_type"),
        Index("ix_entities_asset", "asset_id"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    canonical_name: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType), nullable=False)
    plant_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("plants.id"))
    asset_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("assets.id"))
    neo4j_node_id: Mapped[Optional[str]] = mapped_column(String)
    attributes: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    plant = relationship("Plant", back_populates="entities")
    asset = relationship("Asset", back_populates="entities")
    mentions = relationship("EntityMention", back_populates="entity", cascade="all, delete-orphan")


class EntityMention(Base):
    __tablename__ = "entity_mentions"
    __table_args__ = (
        Index("ix_mentions_entity", "entity_id"),
        Index("ix_mentions_document", "document_id"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    entity_id: Mapped[UUID] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("chunks.id"))
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    surface_text: Mapped[Optional[str]] = mapped_column(String)
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(4, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    entity = relationship("Entity", back_populates="mentions")
    document = relationship("Document", back_populates="entity_mentions")
    chunk = relationship("Chunk", back_populates="mentions")


class WorkOrder(Base):
    __tablename__ = "work_orders"
    __table_args__ = (
        UniqueConstraint("asset_id", "wo_number", name="uq_wo_asset_number"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    wo_number: Mapped[str] = mapped_column(String, nullable=False)
    asset_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("assets.id"))
    wo_type: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    performed_by: Mapped[Optional[str]] = mapped_column(String)
    performed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    document_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("documents.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    asset = relationship("Asset", back_populates="work_orders")
    document = relationship("Document", back_populates="work_orders")


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("ix_incidents_asset", "asset_id"),
        Index("ix_incidents_occurred", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    incident_number: Mapped[Optional[str]] = mapped_column(String)
    asset_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("assets.id"))
    severity: Mapped[Severity] = mapped_column(Enum(Severity), default=Severity.medium, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    document_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("documents.id"))
    rca_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("rca_reports.id", use_alter=True, name="fk_incident_rca"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    asset = relationship("Asset", back_populates="incidents")
    document = relationship("Document", back_populates="incidents")
    rca_report = relationship("RCAReport", foreign_keys=[rca_id], post_update=True)
    lessons = relationship("LessonLearned", back_populates="incident")


class RCAReport(Base):
    __tablename__ = "rca_reports"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    incident_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"))
    hypotheses: Mapped[dict] = mapped_column(JSONB, default=text("'[]'::jsonb"), nullable=False)
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(4, 3))
    citations: Mapped[dict] = mapped_column(JSONB, default=text("'[]'::jsonb"), nullable=False)
    graph_path: Mapped[Optional[dict]] = mapped_column(JSONB)
    generated_by: Mapped[str] = mapped_column(String, default="rca_agent", nullable=False)
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    reviewer = relationship("User", back_populates="reviewed_rcas")


class ComplianceFinding(Base):
    __tablename__ = "compliance_findings"
    __table_args__ = (
        Index("ix_findings_status", "status", "severity"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    asset_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("assets.id"))
    document_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("documents.id"))
    regulation_ref: Mapped[str] = mapped_column(String, nullable=False)
    requirement: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[FindingStatus] = mapped_column(Enum(FindingStatus), nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), default=Severity.medium, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    citations: Mapped[dict] = mapped_column(JSONB, default=text("'[]'::jsonb"), nullable=False)
    detected_by: Mapped[str] = mapped_column(String, default="compliance_agent", nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    asset = relationship("Asset", back_populates="compliance_findings")
    document = relationship("Document", back_populates="compliance_findings")


class Contradiction(Base):
    __tablename__ = "contradictions"
    __table_args__ = (
        Index("ix_contradictions_status_sev", "status", "severity"),
        Index("ix_contradictions_asset", "asset_id"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    asset_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("assets.id"))
    parameter: Mapped[Optional[str]] = mapped_column(String)
    kind: Mapped[ContradictionKind] = mapped_column(Enum(ContradictionKind), nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), default=Severity.high, nullable=False)
    claim_a: Mapped[dict] = mapped_column(JSONB, nullable=False)
    claim_b: Mapped[dict] = mapped_column(JSONB, nullable=False)
    extra_claims: Mapped[dict] = mapped_column(JSONB, default=text("'[]'::jsonb"), nullable=False)
    status: Mapped[str] = mapped_column(String, default="open", nullable=False)
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    resolved_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))

    asset = relationship("Asset", back_populates="contradictions")
    resolver = relationship("User", back_populates="resolved_contradictions")


class TribalKnowledge(Base):
    __tablename__ = "tribal_knowledge"
    __table_args__ = (
        Index("ix_tribal_asset", "asset_id"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    asset_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("assets.id"))
    author_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))
    capture_type: Mapped[CaptureType] = mapped_column(Enum(CaptureType), nullable=False)
    media_key: Mapped[Optional[str]] = mapped_column(String)
    transcript: Mapped[Optional[str]] = mapped_column(Text)
    structured: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    neo4j_node_id: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    asset = relationship("Asset", back_populates="tribal_notes")
    author = relationship("User", back_populates="tribal_notes")


class LessonLearned(Base):
    __tablename__ = "lessons_learned"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    incident_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("incidents.id"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    recommendation: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    citations: Mapped[dict] = mapped_column(JSONB, default=text("'[]'::jsonb"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    incident = relationship("Incident", back_populates="lessons")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))
    title: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_session", "session_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    session_id: Mapped[UUID] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False) # user|assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[dict] = mapped_column(JSONB, default=text("'[]'::jsonb"), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(4, 3))
    agent_trace: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    session = relationship("ChatSession", back_populates="messages")


class KnowledgeScore(Base):
    __tablename__ = "knowledge_scores"
    __table_args__ = (
        Index("ix_scores_scope", "scope", "scope_id", "computed_at"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    scope: Mapped[str] = mapped_column(String, nullable=False) # plant|asset
    scope_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    completeness: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    freshness: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    breakdown: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_resource", "resource_type", "resource_id"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String, nullable=False) # e.g. document.upload
    resource_type: Mapped[Optional[str]] = mapped_column(String)
    resource_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    metadata: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    user = relationship("User", back_populates="audit_logs")
