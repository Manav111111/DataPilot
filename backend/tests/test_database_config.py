import pytest
from httpx import AsyncClient
from app.core.config import Settings


def test_supabase_database_url_normalization():
    # 1. Direct Supabase connection (postgresql:// scheme)
    s1 = Settings(DATABASE_URL="postgresql://postgres:mypassword123@db.abcdefghijklm.supabase.co:5432/postgres")
    assert s1.get_database_url() == "postgresql+asyncpg://postgres:mypassword123@db.abcdefghijklm.supabase.co:5432/postgres"
    assert s1.get_sync_database_url() == "postgresql://postgres:mypassword123@db.abcdefghijklm.supabase.co:5432/postgres"

    # 2. Supabase Session Pooler connection (postgres:// scheme)
    s2 = Settings(DATABASE_URL="postgres://postgres.abcdefghijklm:mypassword123@aws-0-us-east-1.pooler.supabase.com:5432/postgres")
    assert s2.get_database_url() == "postgresql+asyncpg://postgres.abcdefghijklm:mypassword123@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    assert s2.get_sync_database_url() == "postgresql://postgres.abcdefghijklm:mypassword123@aws-0-us-east-1.pooler.supabase.com:5432/postgres"

    # 3. Connection with query params (e.g. sslmode=require)
    s3 = Settings(DATABASE_URL="postgresql://postgres:pass@db.ref.supabase.co:5432/postgres?sslmode=require")
    # sslmode stripped for asyncpg compatibility
    assert s3.get_database_url() == "postgresql+asyncpg://postgres:pass@db.ref.supabase.co:5432/postgres"

    # 4. Already normalized postgresql+asyncpg:// scheme
    s4 = Settings(DATABASE_URL="postgresql+asyncpg://postgres:pass@db.ref.supabase.co:5432/postgres")
    assert s4.get_database_url() == "postgresql+asyncpg://postgres:pass@db.ref.supabase.co:5432/postgres"

    # 5. Local default fallback when DATABASE_URL is empty
    s5 = Settings(
        DATABASE_URL="",
        POSTGRES_SERVER="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_USER="postgres",
        POSTGRES_PASSWORD="postgres_password",
        POSTGRES_DB="test_db"
    )
    assert s5.get_database_url() == "postgresql+asyncpg://postgres:postgres_password@localhost:5432/test_db"
    assert s5.get_sync_database_url() == "postgresql://postgres:postgres_password@localhost:5432/test_db"


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database" in data
    # Ensure no credentials or connection strings are present
    assert "password" not in str(data).lower()
    assert "secret" not in str(data).lower()
    assert "postgres:" not in str(data)


@pytest.mark.asyncio
async def test_integrations_health_check_endpoint(client: AsyncClient):
    resp = await client.get("/health/integrations")
    assert resp.status_code == 200
    data = resp.json()
    assert "database" in data
    assert "provider" in data["database"]
    assert "status" in data["database"]
    assert "integrations" in data
    # Ensure no credentials or connection strings are present
    assert "password" not in str(data).lower()
    assert "secret" not in str(data).lower()
    assert "postgres:" not in str(data)
