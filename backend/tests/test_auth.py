import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.base import Base
from app.db.models import User, UserRole, Plant
from app.security import hash_password
from app.main import create_app
from app.db.session import get_db
from app.deps import require_role

import pytest_asyncio

import uuid
import datetime
from sqlalchemy import event

# SQLite in-memory database for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False)

@event.listens_for(engine.sync_engine, "connect")
def add_sqlite_functions(dbapi_connection, connection_record):
    dbapi_connection.create_function("now", 0, lambda: datetime.datetime.utcnow().isoformat())
    dbapi_connection.create_function("gen_random_uuid", 0, lambda: str(uuid.uuid4()))

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)



@pytest_asyncio.fixture(name="db", scope="function")
async def db_fixture():
    # SQLite does not support schemas or PG extensions, but SQLAlchemy handles it.
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
    
    # Add a mock role-guarded endpoint to test require_role
    @app.get("/api/test-manager", dependencies=[Depends(require_role(UserRole.manager))])
    async def manager_endpoint():
        return {"status": "success"}

    async def override_get_db():
        yield db
        
    app.dependency_overrides[get_db] = override_get_db
    return app



# Simple wrapper to avoid import errors on Depends
from fastapi import Depends


@pytest.mark.asyncio
async def test_auth_flow(app, db):
    # 1. Seed a plant and an admin user
    plant = Plant(name="Riverside Plant", location="Riverside, USA")
    db.add(plant)
    await db.flush()

    admin = User(
        email="admin@riverside.plant",
        hashed_password=hash_password("neuron-demo"),
        full_name="Sam Admin",
        role=UserRole.admin,
        plant_id=plant.id,
        is_active=True
    )
    db.add(admin)
    
    # Seed a technician user
    tech = User(
        email="tech@riverside.plant",
        hashed_password=hash_password("neuron-demo"),
        full_name="Bob Tech",
        role=UserRole.technician,
        plant_id=plant.id,
        is_active=True
    )
    db.add(tech)
    await db.commit()

    # Create HTTPX client to test the API
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 2. POST /auth/login - Success case
        login_res = await client.post(
            "/api/auth/login",
            json={"email": "admin@riverside.plant", "password": "neuron-demo"}
        )
        assert login_res.status_code == 200
        data = login_res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == "admin@riverside.plant"

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # 3. GET /auth/me - Success with Bearer token
        headers = {"Authorization": f"Bearer {access_token}"}
        me_res = await client.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["role"] == "admin"

        # 4. POST /auth/refresh - Refresh token flow
        refresh_res = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_res.status_code == 200
        refresh_data = refresh_res.json()
        assert "access_token" in refresh_data
        assert "refresh_token" in refresh_data

        # 5. Test require_role with manager-only endpoint
        # Log in as technician
        tech_login_res = await client.post(
            "/api/auth/login",
            json={"email": "tech@riverside.plant", "password": "neuron-demo"}
        )
        tech_access_token = tech_login_res.json()["access_token"]
        
        # Technician gets 403 Forbidden
        forbidden_res = await client.get(
            "/api/test-manager",
            headers={"Authorization": f"Bearer {tech_access_token}"}
        )
        assert forbidden_res.status_code == 403

        # Admin gets 200 OK because admin bypasses checks
        admin_res = await client.get(
            "/api/test-manager",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert admin_res.status_code == 200
