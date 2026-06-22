import pytest
from datetime import datetime, date
import uuid
from sqlalchemy import select
from app.db.models import (
    Plant, Asset, Document, DocumentType, DocumentStatus, User, UserRole, Criticality,
    FindingStatus, Severity, ContradictionKind, CaptureType, EntityType,
    ComplianceFinding, Contradiction, TribalKnowledge, KnowledgeScore, ChatSession, ChatMessage
)
from app.repositories.compliance_repo import ComplianceFindingRepository
from app.repositories.contradiction_repo import ContradictionRepository
from app.repositories.tribal_repo import TribalKnowledgeRepository
from app.repositories.score_repo import KnowledgeScoreRepository
from app.repositories.chat_repo import ChatRepository
from app.repositories.entity_repo import EntityRepository
from app.security import hash_password

import pytest_asyncio

@pytest_asyncio.fixture(name="db", scope="function")
async def db_fixture():
    from tests.test_auth import engine, TestingSessionLocal, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
        await session.close()
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_all_new_repositories(db):
    # 0. Seed basic records needed for foreign keys (Plant, User, Asset, Document)
    plant = Plant(name="Test Plant", location="Test Location")
    db.add(plant)
    await db.flush()

    user = User(
        email="test@user.com",
        hashed_password=hash_password("password"),
        full_name="Test User",
        role=UserRole.technician,
        plant_id=plant.id
    )
    db.add(user)
    await db.flush()

    asset = Asset(
        tag="P-101",
        name="Feed Pump 101",
        plant_id=plant.id,
        criticality=Criticality.high
    )
    db.add(asset)
    await db.flush()

    doc = Document(
        title="P-101 Manual",
        doc_type=DocumentType.equipment_manual,
        status=DocumentStatus.uploaded,
        storage_key="manuals/p101.pdf",
        mime_type="application/pdf",
        checksum_sha256="abc123sha",
        plant_id=plant.id,
        uploaded_by=user.id
    )
    db.add(doc)
    await db.flush()
    await db.commit()

    # 1. Test ComplianceFindingRepository
    comp_repo = ComplianceFindingRepository(db)
    finding = await comp_repo.create(
        asset_id=asset.id,
        document_id=doc.id,
        regulation_ref="OSHA 1910.119",
        requirement="Check seal weekly",
        status=FindingStatus.gap,
        severity=Severity.medium,
        description="Seal not checked recently",
        citations=[{"page": 2, "text": "Inspect seals weekly"}]
    )
    assert finding.id is not None
    assert finding.regulation_ref == "OSHA 1910.119"
    assert finding.status == FindingStatus.gap

    fetched_finding = await comp_repo.get(finding.id)
    assert fetched_finding is not None
    assert fetched_finding.regulation_ref == "OSHA 1910.119"

    findings_list = await comp_repo.list(plant_id=plant.id, status=FindingStatus.gap)
    assert len(findings_list) == 1
    assert findings_list[0].id == finding.id

    updated_finding = await comp_repo.update_status(finding.id, FindingStatus.compliant)
    assert updated_finding.status == FindingStatus.compliant
    assert updated_finding.resolved_at is not None

    # 2. Test ContradictionRepository
    contra_repo = ContradictionRepository(db)
    claim_a = {"value": "120", "unit": "Nm", "document_id": str(doc.id)}
    claim_b = {"value": "95", "unit": "Nm", "document_id": str(doc.id)}
    contradiction = await contra_repo.create(
        asset_id=asset.id,
        parameter="torque",
        kind=ContradictionKind.spec_value,
        claim_a=claim_a,
        claim_b=claim_b,
        severity=Severity.high
    )
    assert contradiction.id is not None
    assert contradiction.parameter == "torque"
    assert contradiction.status == "open"

    fetched_contra = await contra_repo.get(contradiction.id)
    assert fetched_contra is not None
    assert fetched_contra.claim_a == claim_a

    contra_list = await contra_repo.list(plant_id=plant.id, status="open")
    assert len(contra_list) == 1

    resolved_contra = await contra_repo.resolve(contradiction.id, "Use 120 Nm per manufacturer guidance", user.id)
    assert resolved_contra.status == "resolved"
    assert resolved_contra.resolved_by == user.id

    # 3. Test TribalKnowledgeRepository
    tribal_repo = TribalKnowledgeRepository(db)
    note = await tribal_repo.create(
        asset_id=asset.id,
        author_id=user.id,
        capture_type=CaptureType.text,
        transcript="We always grease the bearings when we hear a squeal.",
        structured={"action": "grease bearings", "symptom": "squealing sound"}
    )
    assert note.id is not None
    assert note.verified is False

    fetched_note = await tribal_repo.get(note.id)
    assert fetched_note is not None
    assert fetched_note.transcript == "We always grease the bearings when we hear a squeal."

    notes_list = await tribal_repo.list(asset_id=asset.id, verified=False)
    assert len(notes_list) == 1

    verified_note = await tribal_repo.verify(note.id, verified=True, neo4j_node_id="neo4j-node-123")
    assert verified_note.verified is True
    assert verified_note.neo4j_node_id == "neo4j-node-123"

    # 4. Test KnowledgeScoreRepository
    score_repo = KnowledgeScoreRepository(db)
    score = await score_repo.create(
        scope="asset",
        scope_id=asset.id,
        completeness=0.85,
        freshness=0.90,
        breakdown={"missing_fields": ["install_date"]}
    )
    assert score.id is not None
    assert score.completeness == 0.85

    latest_score = await score_repo.get_latest("asset", asset.id)
    assert latest_score is not None
    assert latest_score.completeness == 0.85

    history = await score_repo.get_history("asset", asset.id, limit=5)
    assert len(history) == 1

    # 5. Test ChatRepository
    chat_repo = ChatRepository(db)
    session = await chat_repo.create_session(user_id=user.id, title="Troubleshooting P-101")
    assert session.id is not None
    assert session.title == "Troubleshooting P-101"

    msg = await chat_repo.create_message(
        session_id=session.id,
        role="user",
        content="What is the torque for P-101?",
        citations=[],
        confidence=1.0,
        agent_trace={"agent": "user"}
    )
    assert msg.id is not None
    assert msg.content == "What is the torque for P-101?"

    fetched_session = await chat_repo.get_session(session.id)
    assert fetched_session is not None
    assert len(fetched_session.messages) == 1
    assert fetched_session.messages[0].content == "What is the torque for P-101?"

    sessions_list = await chat_repo.list_sessions(user_id=user.id)
    assert len(sessions_list) == 1

    deleted = await chat_repo.delete_session(session.id)
    assert deleted is True
    assert await chat_repo.get_session(session.id) is None

    # 6. Test EntityRepository Trigram Match
    entity_repo = EntityRepository(db)
    ent1 = await entity_repo.create(
        canonical_name="Centrifugal Pump P-101",
        entity_type=EntityType.asset,
        plant_id=plant.id
    )
    assert ent1.id is not None

    # Trigram similarity matching test
    match_res = await entity_repo.find_by_trigram_match(
        plant_id=plant.id,
        name="Centrifugal Pump P-101 near duplicate",
        entity_type=EntityType.asset,
        threshold=0.5
    )
    assert match_res is not None
    matched_ent, score = match_res
    assert matched_ent.canonical_name == "Centrifugal Pump P-101"
