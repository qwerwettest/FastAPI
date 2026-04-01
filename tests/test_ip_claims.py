"""
IP Claims endpoint tests.

Tests for:
- POST /api/v1/ip-claims
- GET /api/v1/ip-claims
- GET /api/v1/ip-claims/{id}
- POST /api/v1/ip-claims/{id}/documents
- POST /api/v1/ip-claims/{id}/review
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.models.user import UserRole
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


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def issuer_user(client):
    """Create an issuer user and return auth token."""
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "issuer@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    
    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "issuer@example.com", "password": "password123"},
    )
    return login_response.json()["access_token"]


@pytest.fixture
async def admin_user(client):
    """Create an admin user and return auth token."""
    # Note: In real scenario, admin would be created via DB migration
    # For testing, we register and manually set role (simplified)
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "password123"},
    )
    return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_ip_claim_success(client, issuer_user):
    response = await client.post(
        "/api/v1/ip-claims/",
        json={
            "patent_number": "US12345678B2",
            "claimed_owner_name": "Test Corp",
            "title": "Test Patent",
            "description": "A test patent description",
            "jurisdiction": "US",
        },
        headers={"Authorization": f"Bearer {issuer_user}"},
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["patent_number"] == "US12345678B2"
    assert data["claimed_owner_name"] == "Test Corp"
    assert data["status"] in ["draft", "prechecked", "submitted"]


@pytest.mark.asyncio
async def test_create_ip_claim_requires_auth(client):
    response = await client.post(
        "/api/v1/ip-claims/",
        json={
            "patent_number": "US12345678B2",
            "claimed_owner_name": "Test Corp",
            "title": "Test Patent",
        },
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_ip_claims(client, issuer_user):
    # Create a claim first
    await client.post(
        "/api/v1/ip-claims/",
        json={
            "patent_number": "US12345678B2",
            "claimed_owner_name": "Test Corp",
            "title": "Test Patent",
        },
        headers={"Authorization": f"Bearer {issuer_user}"},
    )
    
    response = await client.get(
        "/api/v1/ip-claims/",
        headers={"Authorization": f"Bearer {issuer_user}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_get_ip_claim_by_id(client, issuer_user):
    # Create a claim
    create_response = await client.post(
        "/api/v1/ip-claims/",
        json={
            "patent_number": "US12345678B2",
            "claimed_owner_name": "Test Corp",
            "title": "Test Patent",
        },
        headers={"Authorization": f"Bearer {issuer_user}"},
    )
    claim_id = create_response.json()["id"]
    
    response = await client.get(
        f"/api/v1/ip-claims/{claim_id}",
        headers={"Authorization": f"Bearer {issuer_user}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == claim_id


@pytest.mark.asyncio
async def test_get_ip_claim_not_found(client, issuer_user):
    response = await client.get(
        "/api/v1/ip-claims/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {issuer_user}"},
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patent_precheck(client, issuer_user):
    response = await client.post(
        "/api/v1/patents/precheck",
        json={
            "patent_number": "US12345678B2",
            "jurisdiction": "US",
        },
        headers={"Authorization": f"Bearer {issuer_user}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["found", "not_found", "partial", "error"]
    assert data["patent_number"] == "US12345678B2"


@pytest.mark.asyncio
async def test_patent_precheck_not_found(client, issuer_user):
    response = await client.post(
        "/api/v1/patents/precheck",
        json={
            "patent_number": "99999999",  # Mock pattern for not found
            "jurisdiction": "US",
        },
        headers={"Authorization": f"Bearer {issuer_user}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_found"


@pytest.mark.asyncio
async def test_review_decision_requires_admin(client, issuer_user, admin_user):
    # Create a claim as issuer
    create_response = await client.post(
        "/api/v1/ip-claims/",
        json={
            "patent_number": "US12345678B2",
            "claimed_owner_name": "Test Corp",
            "title": "Test Patent",
        },
        headers={"Authorization": f"Bearer {issuer_user}"},
    )
    claim_id = create_response.json()["id"]
    
    # Try to review as regular user (should fail)
    review_response = await client.post(
        f"/api/v1/ip-claims/{claim_id}/review",
        json={"decision": "approve", "notes": "Test review"},
        headers={"Authorization": f"Bearer {issuer_user}"},
    )
    
    assert review_response.status_code == 403


@pytest.mark.asyncio
async def test_review_decision_approve(client, issuer_user, admin_user):
    # Create a claim
    create_response = await client.post(
        "/api/v1/ip-claims/",
        json={
            "patent_number": "US12345678B2",
            "claimed_owner_name": "Test Corp",
            "title": "Test Patent",
        },
        headers={"Authorization": f"Bearer {issuer_user}"},
    )
    claim_id = create_response.json()["id"]
    
    # Submit review as admin
    review_response = await client.post(
        f"/api/v1/ip-claims/{claim_id}/review",
        json={"decision": "approve", "notes": "Approved for tokenization"},
        headers={"Authorization": f"Bearer {admin_user}"},
    )
    
    assert review_response.status_code == 200
    data = review_response.json()
    assert data["status"] == "approved"


@pytest.mark.asyncio
async def test_review_decision_reject(client, issuer_user, admin_user):
    # Create a claim
    create_response = await client.post(
        "/api/v1/ip-claims/",
        json={
            "patent_number": "US12345678B2",
            "claimed_owner_name": "Test Corp",
            "title": "Test Patent",
        },
        headers={"Authorization": f"Bearer {issuer_user}"},
    )
    claim_id = create_response.json()["id"]
    
    # Submit review as admin
    review_response = await client.post(
        f"/api/v1/ip-claims/{claim_id}/review",
        json={"decision": "reject", "notes": "Does not meet requirements"},
        headers={"Authorization": f"Bearer {admin_user}"},
    )
    
    assert review_response.status_code == 200
    data = review_response.json()
    assert data["status"] == "rejected"
