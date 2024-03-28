import asyncio

import app.main  # noqa: F401 WPS301
from app.common.config import Base, engine


async def create_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(create_database())
