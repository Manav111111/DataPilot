import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.core.security import create_access_token
from app.models.user import User
from app.core.config import settings

settings.AI_PROVIDER = "mock"
settings.TAVILY_API_KEY = "mock_tavily_key"
settings.FIRECRAWL_API_KEY = "mock_firecrawl_key"

# In-memory SQLite async test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user_a(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "password": "Password123!",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    token = data["access_token"]
    user_id = data["user"]["id"]
    return {
        "id": user_id,
        "token": token,
        "email": "alice@example.com",
        "name": "Alice Engineer",
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest_asyncio.fixture(scope="function")
async def test_user_b(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Bob Analyst",
            "email": "bob@example.com",
            "password": "Password123!",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    token = data["access_token"]
    user_id = data["user"]["id"]
    return {
        "id": user_id,
        "token": token,
        "email": "bob@example.com",
        "name": "Bob Analyst",
        "headers": {"Authorization": f"Bearer {token}"},
    }
