from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    echo=settings.ECHO_SQL
)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    expire_on_commit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)

async def get_db() -> AsyncSession:
    """
    Dependency function that provides database sessions to FastAPI endpoints.
    """
    async with SessionLocal() as session:
        yield session
