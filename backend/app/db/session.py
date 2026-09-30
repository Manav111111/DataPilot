from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

db_url = settings.get_database_url()

# Extra arguments depending on database dialect
connect_args = {}
if "sqlite" in db_url:
    connect_args["check_same_thread"] = False
else:
    # Supabase PostgreSQL & Connection Poolers (PgBouncer/Supavisor):
    # Disable statement caching to allow seamless connection via Supabase Session and Transaction poolers
    connect_args["statement_cache_size"] = 0
    # Enable SSL for remote/cloud PostgreSQL (Supabase, AWS RDS, etc.) when not connecting locally
    if "localhost" not in db_url and "127.0.0.1" not in db_url:
        connect_args["ssl"] = "require"

engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,  # Recycle connections every 5 minutes for cloud resilience
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
