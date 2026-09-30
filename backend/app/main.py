from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.exceptions import AppException
from app.api.routes import api_router
from app.db.session import engine, Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    # Create tables automatically on startup for local dev/sqlite/test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schemas verified.")
    yield
    logger.info("Shutting down application...")
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS Configuration
if settings.BACKEND_CORS_ORIGINS:
    origins = [str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=r"^https:\/\/.*\.onrender\.com$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "success": False},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0]["msg"] if errors else "Validation error"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": first_error, "errors": errors, "success": False},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred", "success": False},
    )


# Health Check
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint reporting overall application status and database reachability.
    Never prints or exposes database credentials, hostnames, or internal tracebacks.
    """
    db_status = "healthy"
    try:
        from sqlalchemy import text
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {type(e).__name__}")
        db_status = "unhealthy"

    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "app": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health/integrations", tags=["Health"])
async def integrations_health_check():
    """
    Checks configuration status and connectivity indicators for integrated services.
    Never prints or exposes raw API keys, passwords, or connection strings.
    """
    from sqlalchemy import text
    from app.db.session import AsyncSessionLocal

    db_url = settings.get_database_url()
    if "supabase" in db_url.lower():
        db_provider = "Supabase PostgreSQL"
    elif "sqlite" in db_url.lower():
        db_provider = "SQLite (Local/Test)"
    else:
        db_provider = "PostgreSQL"

    db_status = "active"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"

    tavily_configured = bool(settings.TAVILY_API_KEY and not settings.TAVILY_API_KEY.startswith("your_") and not settings.TAVILY_API_KEY.startswith("mock_"))
    firecrawl_configured = bool(settings.FIRECRAWL_API_KEY and not settings.FIRECRAWL_API_KEY.startswith("your_") and not settings.FIRECRAWL_API_KEY.startswith("mock_"))
    gemini_configured = bool(settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_") and not settings.GEMINI_API_KEY.startswith("mock_"))

    return {
        "status": "online" if db_status == "active" else "degraded",
        "app": settings.PROJECT_NAME,
        "database": {
            "provider": db_provider,
            "status": db_status,
        },
        "integrations": {
            "tavily": {
                "configured": tavily_configured,
                "provider": "Tavily Search API",
                "status": "active" if tavily_configured else "unconfigured"
            },
            "firecrawl": {
                "configured": firecrawl_configured,
                "provider": "Firecrawl Scrape API",
                "status": "active" if firecrawl_configured else "unconfigured"
            },
            "gemini": {
                "configured": gemini_configured,
                "model": settings.GEMINI_MODEL,
                "status": "active" if gemini_configured else "unconfigured"
            },
            "celery_redis": {
                "broker": settings.CELERY_BROKER_URL.split("@")[-1],
                "configured": bool(settings.REDIS_URL),
                "status": "active"
            }
        }
    }


# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)
