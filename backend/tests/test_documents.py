import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.db.session import get_db
from app.db.models import User, UserRole, Plant, Document, DocumentStatus, DocumentType
from app.security import hash_password
from tests.test_auth import TestingSessionLocal, engine, Base


import pytest_asyncio

@pytest_asyncio.fixture(name="db", scope="function")
async def db_fixture():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
        await session.close()
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(name="app", scope="function")
async def app_fixture(db):
    app = create_app()
    async def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.mark.asyncio
async def test_upload_document_endpoint(app, db):
    # Seed plant and user
    plant = Plant(name="Riverside Plant", location="Riverside, USA")
    db.add(plant)
    await db.flush()

    user = User(
        email="tech@riverside.plant",
        hashed_password=hash_password("neuron-demo"),
        full_name="Bob Tech",
        role=UserRole.technician,
        plant_id=plant.id,
        is_active=True
    )
    db.add(user)
    await db.commit()

    # Login to get token
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post(
            "/api/auth/login",
            json={"email": "tech@riverside.plant", "password": "neuron-demo"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Mock MinIO storage and Celery task
        with patch("app.services.document_service.storage_service.put") as mock_put, \
             patch("app.services.document_service.ingest_document.delay") as mock_delay:
            
            mock_put.return_value = None
            mock_delay.return_value = None

            # Prepare file upload payload
            files = {"file": ("test.pdf", b"pdf content", "application/pdf")}
            data = {
                "title": "Equipment Manual",
                "doc_type": "equipment_manual",
                "effective_date": "2026-06-22"
            }

            response = await client.post(
                "/api/documents",
                headers=headers,
                data=data,
                files=files
            )
            assert response.status_code == 201
            resp_json = response.json()
            assert resp_json["title"] == "Equipment Manual"
            assert resp_json["status"] == "uploaded"
            assert resp_json["doc_type"] == "equipment_manual"
            assert resp_json["effective_date"] == "2026-06-22"
            assert resp_json["plant_id"] == str(plant.id)
            assert resp_json["uploaded_by"] == str(user.id)

            mock_put.assert_called_once()
            mock_delay.assert_called_once()
