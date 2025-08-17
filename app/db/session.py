from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    echo=settings.ECHO_SQL
)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that provides database sessions to FastAPI endpoints.
    
    Usage in endpoints:
    @router.get("/items/")
    async def get_items(db: Session = Depends(get_db)):
        # Use db session here
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def create_db_session() -> Session:
    """
    Create a new database session.
    Use this when you need a session outside of FastAPI dependency injection.
    Remember to close the session when done.
    """
    return SessionLocal()

# For testing purposes
def get_test_db() -> Generator[Session, None, None]:
    """
    Test database session generator.
    This would typically use a separate test database.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()