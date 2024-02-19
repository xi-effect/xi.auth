from os import getenv
from pathlib import Path

from sqlalchemy import MetaData, NullPool
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.common.rabbit import RabbitDirectProducer
from app.common.sqla import MappingBase

current_directory: Path = Path.cwd()

COOKIE_DOMAIN: str = getenv("COOKIE_DOMAIN", "localhost")
PRODUCTION_MODE: bool = getenv("PRODUCTION", "0") == "1"
DATABASE_MIGRATED: bool = getenv("DATABASE_MIGRATED", "0") == "1"

DB_URL: str = getenv("DB_LINK", "postgresql+asyncpg://test:test@localhost:5432/test")
DB_SCHEMA: str | None = getenv("DB_SCHEMA", None)

MQ_URL: str = getenv("MQ_URL", "amqp://guest:guest@localhost/")
MQ_POCHTA_QUEUE: str = getenv("MQ_POCHTA_QUEUE", "pochta.send")

convention = {
    "ix": "ix_%(column_0_label)s",  # noqa: WPS323
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # noqa: WPS323
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # noqa: WPS323
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # noqa: WPS323
    "pk": "pk_%(table_name)s",  # noqa: WPS323
}

engine = create_async_engine(
    DB_URL,
    pool_recycle=280,  # noqa: WPS432
    echo=not PRODUCTION_MODE,
    poolclass=None if PRODUCTION_MODE else NullPool,
)
db_meta = MetaData(naming_convention=convention, schema=DB_SCHEMA)
sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)


AVATARS_PATH = "media/avatars/"


class Base(AsyncAttrs, DeclarativeBase, MappingBase):
    __tablename__: str
    __abstract__: bool

    metadata = db_meta


pochta_producer = RabbitDirectProducer(queue_name=MQ_POCHTA_QUEUE)
