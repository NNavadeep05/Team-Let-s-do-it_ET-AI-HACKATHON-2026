"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-06-22 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_init'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

    # Create enums
    user_role = postgresql.ENUM('admin', 'technician', 'manager', 'compliance_officer', 'plant_head', name='user_role')
    user_role.create(op.get_bind(), checkfirst=True)

    document_type = postgresql.ENUM('pid', 'sop', 'work_order', 'inspection_report', 'maintenance_log', 'regulatory', 'equipment_manual', 'email', 'excel', 'incident_report', name='document_type')
    document_type.create(op.get_bind(), checkfirst=True)

    document_status = postgresql.ENUM('uploaded', 'processing', 'processed', 'failed', name='document_status')
    document_status.create(op.get_bind(), checkfirst=True)

    ingest_stage = postgresql.ENUM('parse_ocr', 'extract_layout', 'extract_entities', 'resolve_entities', 'extract_relationships', 'write_stores', 'scoring', 'done', name='ingest_stage')
    ingest_stage.create(op.get_bind(), checkfirst=True)

    entity_type = postgresql.ENUM('asset', 'equipment', 'system', 'procedure', 'material', 'spare', 'lubricant', 'hazard', 'safety_control', 'person', 'role', 'regulation', 'requirement', 'measurement', 'failure_mode', 'cause', 'symptom', 'lesson', 'tribal_note', name='entity_type')
    entity_type.create(op.get_bind(), checkfirst=True)

    criticality = postgresql.ENUM('low', 'medium', 'high', 'critical', name='criticality')
    criticality.create(op.get_bind(), checkfirst=True)

    finding_status = postgresql.ENUM('compliant', 'gap', 'conflict', 'expired', name='finding_status')
    finding_status.create(op.get_bind(), checkfirst=True)

    contradiction_kind = postgresql.ENUM('spec_value', 'procedure_step', 'schedule', 'status', 'safety_limit', name='contradiction_kind')
    contradiction_kind.create(op.get_bind(), checkfirst=True)

    severity = postgresql.ENUM('info', 'low', 'medium', 'high', 'critical', name='severity')
    severity.create(op.get_bind(), checkfirst=True)

    capture_type = postgresql.ENUM('voice', 'text', 'email', 'image', name='capture_type')
    capture_type.create(op.get_bind(), checkfirst=True)

    # 1. plants
    op.create_table(
        'plants',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('neo4j_node_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. users
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', postgresql.CITEXT(), nullable=False),
        sa.Column('hashed_password', sa.Text(), nullable=False),
        sa.Column('full_name', sa.Text(), nullable=False),
        sa.Column('role', sa.Enum('admin', 'technician', 'manager', 'compliance_officer', 'plant_head', name='user_role'), server_default='technician', nullable=False),
        sa.Column('plant_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # 3. assets
    op.create_table(
        'assets',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tag', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('asset_type', sa.Text(), nullable=True),
        sa.Column('iso14224_class', sa.Text(), nullable=True),
        sa.Column('plant_id', sa.UUID(), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('criticality', sa.Enum('low', 'medium', 'high', 'critical', name='criticality'), server_default='medium', nullable=False),
        sa.Column('manufacturer', sa.Text(), nullable=True),
        sa.Column('model', sa.Text(), nullable=True),
        sa.Column('install_date', sa.Date(), nullable=True),
        sa.Column('neo4j_node_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plant_id', 'tag', name='uq_assets_plant_tag')
    )
    op.create_index('ix_assets_plant', 'assets', ['plant_id'], unique=False)
    op.create_index('ix_assets_tag', 'assets', ['tag'], unique=False)

    # 4. documents
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('doc_type', sa.Enum('pid', 'sop', 'work_order', 'inspection_report', 'maintenance_log', 'regulatory', 'equipment_manual', 'email', 'excel', 'incident_report', name='document_type'), nullable=False),
        sa.Column('status', sa.Enum('uploaded', 'processing', 'processed', 'failed', name='document_status'), server_default='uploaded', nullable=False),
        sa.Column('storage_key', sa.Text(), nullable=False),
        sa.Column('mime_type', sa.Text(), nullable=False),
        sa.Column('checksum_sha256', sa.Text(), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('plant_id', sa.UUID(), nullable=True),
        sa.Column('uploaded_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('supersedes_id', sa.UUID(), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['supersedes_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documents_effective', 'documents', ['effective_date'], unique=False)
    op.create_index('ix_documents_plant', 'documents', ['plant_id'], unique=False)
    op.create_index('ix_documents_type_status', 'documents', ['doc_type', 'status'], unique=False)

    # 5. document_pages
    op.create_table(
        'document_pages',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('image_key', sa.Text(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('ocr_confidence', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'page_number', name='uq_pages_document_page')
    )

    # 6. ingestion_jobs
    op.create_table(
        'ingestion_jobs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('stage', sa.Enum('parse_ocr', 'extract_layout', 'extract_entities', 'resolve_entities', 'extract_relationships', 'write_stores', 'scoring', 'done', name='ingest_stage'), server_default='parse_ocr', nullable=False),
        sa.Column('status', sa.Text(), server_default='pending', nullable=False),
        sa.Column('progress', sa.Numeric(precision=4, scale=3), server_default='0.000', nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('celery_task_id', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. chunks
    op.create_table(
        'chunks',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('section_path', sa.Text(), nullable=True),
        sa.Column('qdrant_point_id', sa.UUID(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'chunk_index', name='uq_chunks_document_index')
    )
    op.create_index('ix_chunks_document', 'chunks', ['document_id'], unique=False)
    op.create_index('ix_chunks_fts', 'chunks', [sa.text("to_tsvector('english', content)")], postgres_using='gin')
    op.create_index('ix_chunks_meta', 'chunks', ['metadata'], postgres_using='gin')

    # 8. entities
    op.create_table(
        'entities',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('canonical_name', sa.Text(), nullable=False),
        sa.Column('entity_type', sa.Enum('asset', 'equipment', 'system', 'procedure', 'material', 'spare', 'lubricant', 'hazard', 'safety_control', 'person', 'role', 'regulation', 'requirement', 'measurement', 'failure_mode', 'cause', 'symptom', 'lesson', 'tribal_note', name='entity_type'), nullable=False),
        sa.Column('plant_id', sa.UUID(), nullable=True),
        sa.Column('asset_id', sa.UUID(), nullable=True),
        sa.Column('neo4j_node_id', sa.Text(), nullable=True),
        sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_entities_asset', 'entities', ['asset_id'], unique=False)
    op.create_index('ix_entities_name_trgm', 'entities', ['canonical_name'], postgres_using='gin', postgres_ops={'canonical_name': 'gin_trgm_ops'})
    op.create_index('ix_entities_type', 'entities', ['entity_type'], unique=False)

    # 9. entity_mentions
    op.create_table(
        'entity_mentions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('chunk_id', sa.UUID(), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('surface_text', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chunk_id'], ['chunks.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mentions_document', 'entity_mentions', ['document_id'], unique=False)
    op.create_index('ix_mentions_entity', 'entity_mentions', ['entity_id'], unique=False)

    # 10. work_orders
    op.create_table(
        'work_orders',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('wo_number', sa.Text(), nullable=False),
        sa.Column('asset_id', sa.UUID(), nullable=True),
        sa.Column('wo_type', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('performed_by', sa.Text(), nullable=True),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('document_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_id', 'wo_number', name='uq_wo_asset_number')
    )

    # 11. rca_reports (stub table first to solve circular reference)
    op.create_table(
        'rca_reports',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('incident_id', sa.UUID(), nullable=True),
        sa.Column('hypotheses', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('graph_path', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('generated_by', sa.Text(), server_default='rca_agent', nullable=False),
        sa.Column('reviewed_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 12. incidents
    op.create_table(
        'incidents',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('incident_number', sa.Text(), nullable=True),
        sa.Column('asset_id', sa.UUID(), nullable=True),
        sa.Column('severity', sa.Enum('info', 'low', 'medium', 'high', 'critical', name='severity'), server_default='medium', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('document_id', sa.UUID(), nullable=True),
        sa.Column('rca_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['rca_id'], ['rca_reports.id'], name='fk_incident_rca', use_alter=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_incidents_asset', 'incidents', ['asset_id'], unique=False)
    op.create_index('ix_incidents_occurred', 'incidents', ['occurred_at'], unique=False)

    # Add foreign key constraints on rca_reports now that incidents exists
    op.create_foreign_key(
        'fk_rca_reports_incident', 'rca_reports', 'incidents',
        ['incident_id'], ['id'], ondelete='CASCADE'
    )

    # 13. compliance_findings
    op.create_table(
        'compliance_findings',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('asset_id', sa.UUID(), nullable=True),
        sa.Column('document_id', sa.UUID(), nullable=True),
        sa.Column('regulation_ref', sa.Text(), nullable=False),
        sa.Column('requirement', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('compliant', 'gap', 'conflict', 'expired', name='finding_status'), nullable=False),
        sa.Column('severity', sa.Enum('info', 'low', 'medium', 'high', 'critical', name='severity'), server_default='medium', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('detected_by', sa.Text(), server_default='compliance_agent', nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_findings_status', 'compliance_findings', ['status', 'severity'], unique=False)

    # 14. contradictions
    op.create_table(
        'contradictions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('asset_id', sa.UUID(), nullable=True),
        sa.Column('parameter', sa.Text(), nullable=True),
        sa.Column('kind', sa.Enum('spec_value', 'procedure_step', 'schedule', 'status', 'safety_limit', name='contradiction_kind'), nullable=False),
        sa.Column('severity', sa.Enum('info', 'low', 'medium', 'high', 'critical', name='severity'), server_default='high', nullable=False),
        sa.Column('claim_a', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('claim_b', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('extra_claims', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('status', sa.Text(), server_default='open', nullable=False),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_contradictions_asset', 'contradictions', ['asset_id'], unique=False)
    op.create_index('ix_contradictions_status_sev', 'contradictions', ['status', 'severity'], unique=False)

    # 15. tribal_knowledge
    op.create_table(
        'tribal_knowledge',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('asset_id', sa.UUID(), nullable=True),
        sa.Column('author_id', sa.UUID(), nullable=True),
        sa.Column('capture_type', sa.Enum('voice', 'text', 'email', 'image', name='capture_type'), nullable=False),
        sa.Column('media_key', sa.Text(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('structured', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('neo4j_node_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tribal_asset', 'tribal_knowledge', ['asset_id'], unique=False)

    # 16. lessons_learned
    op.create_table(
        'lessons_learned',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('incident_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('tags', sa.ARRAY(sa.Text()), nullable=True),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 17. chat_sessions
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 18. chat_messages
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('confidence', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('agent_trace', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_messages_session', 'chat_messages', ['session_id', 'created_at'], unique=False)

    # 19. knowledge_scores
    op.create_table(
        'knowledge_scores',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('scope', sa.Text(), nullable=False),
        sa.Column('scope_id', sa.UUID(), nullable=False),
        sa.Column('completeness', sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column('freshness', sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column('breakdown', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scores_scope', 'knowledge_scores', ['scope', 'scope_id', 'computed_at'], unique=False)

    # 20. audit_log
    op.create_table(
        'audit_log',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('resource_type', sa.Text(), nullable=True),
        sa.Column('resource_id', sa.UUID(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_resource', 'audit_log', ['resource_type', 'resource_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of dependencies
    op.drop_table('audit_log')
    op.drop_table('knowledge_scores')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('lessons_learned')
    op.drop_table('tribal_knowledge')
    op.drop_table('contradictions')
    op.drop_table('compliance_findings')

    # Circular ref drop constraints
    op.drop_constraint('fk_rca_reports_incident', 'rca_reports', type_='foreignkey')
    op.drop_constraint('fk_incident_rca', 'incidents', type_='foreignkey')

    op.drop_table('incidents')
    op.drop_table('rca_reports')
    op.drop_table('work_orders')
    op.drop_table('entity_mentions')
    op.drop_table('entities')
    op.drop_table('chunks')
    op.drop_table('ingestion_jobs')
    op.drop_table('document_pages')
    op.drop_table('documents')
    op.drop_table('assets')
    op.drop_table('users')
    op.drop_table('plants')

    # Drop enums
    op.execute(sa.text("DROP TYPE IF EXISTS user_role"))
    op.execute(sa.text("DROP TYPE IF EXISTS document_type"))
    op.execute(sa.text("DROP TYPE IF EXISTS document_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS ingest_stage"))
    op.execute(sa.text("DROP TYPE IF EXISTS entity_type"))
    op.execute(sa.text("DROP TYPE IF EXISTS criticality"))
    op.execute(sa.text("DROP TYPE IF EXISTS finding_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS contradiction_kind"))
    op.execute(sa.text("DROP TYPE IF EXISTS severity"))
    op.execute(sa.text("DROP TYPE IF EXISTS capture_type"))
