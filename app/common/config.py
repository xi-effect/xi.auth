from os import getenv
from pathlib import Path

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.common.sqla import MappingBase

current_directory: Path = Path.cwd()

PRODUCTION_MODE: bool = getenv("PRODUCTION", "0") == "1"
DATABASE_RESET: bool = getenv("DATABASE_RESET", "0") == "1"

convention = {
    "ix": "ix_%(column_0_label)s",  # noqa: WPS323
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # noqa: WPS323
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # noqa: WPS323
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # noqa: WPS323
    "pk": "pk_%(table_name)s",  # noqa: WPS323
}

db_url: str = getenv("DB_LINK", f"sqlite+aiosqlite:///{current_directory / 'app.db'}")
engine = create_async_engine(db_url, pool_recycle=280, echo=True)  # noqa: WPS432
db_meta = MetaData(naming_convention=convention)
sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase, MappingBase):
    __tablename__: str
    __abstract__: bool

    metadata = db_meta
