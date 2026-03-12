import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.api.routers import auth, chat, appointment, analytics, assessment
from app.db.database import engine, Base

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle for the application."""
    # ── STARTUP ──
    # Verify database connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection to Supabase verified successfully.")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    # Create tables (fallback — Alembic is the primary migration tool)
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables ensured via metadata.create_all().")

    yield  # ← Application runs here

    # ── SHUTDOWN ──
    engine.dispose()
    logger.info("🔌 Database engine disposed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should be restricted in prod!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(appointment.router, prefix=f"{settings.API_V1_STR}/appointment", tags=["appointment"])
app.include_router(assessment.router, prefix=f"{settings.API_V1_STR}/assessment", tags=["assessment"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin-analytics"])

@app.get("/")
def root():
    return {"message": "Welcome to MindleapV1 API"}
