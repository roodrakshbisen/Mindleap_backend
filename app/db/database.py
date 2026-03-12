from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# ── PostgreSQL Engine with Supabase-optimized connection pooling ──
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,        # Detect stale connections before using them
    pool_size=5,               # Maintain 5 persistent connections
    max_overflow=10,           # Allow up to 10 additional connections under load
    pool_timeout=30,           # Wait up to 30s for a connection from the pool
    pool_recycle=1800,         # Recycle connections every 30 min (Supabase idle timeout)
    connect_args={
        "options": "-c timezone=utc",  # Enforce UTC timezone on all connections
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI dependency that yields a database session and closes it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
