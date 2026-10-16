import app.models  # noqa: F401  (registers all entities on Base.metadata)
from app.db.base import Base
from app.db.session import get_engine


async def init_db() -> None:
    """Create all tables if they do not exist."""
    async with get_engine().begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
