import pytest
import shutil
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test_ip_claims.db"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()
    shutil.rmtree("uploads", ignore_errors=True)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _create_and_login(client: AsyncClient, email: str, password: str, role: str):
    create_response = await client.post(
        "/api/v1/users/",
        json={"email": email, "password": password, "role": role},
    )
    assert create_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_patent_precheck_and_ip_claim_flow(client: AsyncClient):
    issuer_headers = await _create_and_login(
        client,
        email="issuer@example.com",
        password="password123",
        role="issuer",
    )

    precheck_response = await client.post(
        "/api/v1/patents/precheck",
        json={"patent_number": "US123456"},
        headers=issuer_headers,
    )
    assert precheck_response.status_code == 200
    precheck = precheck_response.json()
    assert precheck["status"] == "found"

    create_claim_response = await client.post(
        "/api/v1/ip-claims",
        json={
            "patent_number": "US123456",
            "patent_title": "Test Patent",
            "claimed_owner_name": "Issuer Inc",
            "description": "Ownership claim",
            "jurisdiction": "US",
            "precheck_snapshot": precheck,
        },
        headers=issuer_headers,
    )
    assert create_claim_response.status_code == 200
    claim = create_claim_response.json()
    claim_id = claim["id"]

    list_response = await client.get("/api/v1/ip-claims", headers=issuer_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    upload_response = await client.post(
        f"/api/v1/ip-claims/{claim_id}/documents",
        headers=issuer_headers,
        files={"file": ("ownership.pdf", b"fake-pdf-content", "application/pdf")},
        data={"doc_type": "supporting"},
    )
    assert upload_response.status_code == 200
    assert upload_response.json()["ip_claim_id"] == claim_id

    admin_headers = await _create_and_login(
        client,
        email="admin@example.com",
        password="password123",
        role="admin",
    )

    review_response = await client.post(
        f"/api/v1/ip-claims/{claim_id}/review",
        headers=admin_headers,
        json={"decision": "approve", "notes": "ok"},
    )
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "approved"
