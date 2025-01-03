import asyncio
import sys
from os import getenv
from pathlib import Path

from aiosmtplib import SMTP
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.common.aiopika_ext import RabbitDirectProducer
from app.common.cryptography import CryptographyProvider, TokenGenerator
from app.common.sqlalchemy_ext import MappingBase

current_directory: Path = Path.cwd()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv(current_directory / ".env")

AVATARS_PATH: Path = current_directory / "avatars"

PRODUCTION_MODE: bool = getenv("PRODUCTION", "0") == "1"
TESTING_MODE: bool = "pytest" in sys.modules

COOKIE_DOMAIN: str = getenv("COOKIE_DOMAIN", "localhost")
DATABASE_MIGRATED: bool = getenv("DATABASE_MIGRATED", "0") == "1"

DB_URL: str = getenv("DB_LINK", "postgresql+psycopg://test:test@localhost:5432/test")
DB_SCHEMA: str | None = getenv("DB_SCHEMA", None)

MQ_URL: str = getenv("MQ_URL", "amqp://guest:guest@localhost/")
MQ_POCHTA_QUEUE: str = getenv("MQ_POCHTA_QUEUE", "pochta.send")

PASSWORD_RESET_KEYS: list[str] = getenv(
    "PASSWORD_RESET_KEYS", Fernet.generate_key().decode("utf-8")
).split("|")

EMAIL_CONFIRMATION_KEYS: list[str] = getenv(
    "EMAIL_CONFIRMATION_KEYS", Fernet.generate_key().decode("utf-8")
).split("|")

DEMO_WEBHOOK_URL: str | None = getenv("DEMO_WEBHOOK_URL", None)
VACANCY_WEBHOOK_URL: str | None = getenv("VACANCY_WEBHOOK_URL", None)

MUB_KEY: str = getenv("MUB_KEY", "local")

SUPBOT_TOKEN: str | None = getenv("SUPBOT_TOKEN")
SUPBOT_GROUP_ID: str | None = getenv("SUPBOT_GROUP_ID")
SUPBOT_CHANNEL_ID: str | None = getenv("SUPBOT_CHANNEL_ID")
SUPBOT_POLLING: bool = getenv("SUPBOT_POLLING", "0") == "1"
SUPBOT_WEBHOOK_URL: str = getenv("SUPBOT_WEBHOOK_URL", "http://localhost:5100")

EMAIL_HOSTNAME: str | None = getenv("EMAIL_HOSTNAME")
EMAIL_USERNAME: str | None = getenv("EMAIL_USERNAME")
EMAIL_PASSWORD: str | None = getenv("EMAIL_PASSWORD")
EMAIL_INITIALIZED: bool = all((EMAIL_HOSTNAME, EMAIL_USERNAME, EMAIL_PASSWORD))
EMAIL_PORT = int(getenv("EMAIL_PORT", 465))
EMAIL_TIMEOUT = int(getenv("EMAIL_TIMEOUT", 20))
EMAIL_USE_TLS: bool = getenv("EMAIL_USE_TLS", "1") == "1"

smtp_client: SMTP | None = (
    SMTP(
        hostname=EMAIL_HOSTNAME,
        username=EMAIL_USERNAME,
        password=EMAIL_PASSWORD,
        use_tls=EMAIL_USE_TLS,
        port=EMAIL_PORT,
        timeout=EMAIL_TIMEOUT,
    )
    if EMAIL_INITIALIZED
    else None
)

LOCAL_PORT: str = getenv("LOCAL_PORT", "8000")

BRIDGE_BASE_URL: str = getenv("BRIDGE_BASE_URL", f"http://localhost:{LOCAL_PORT}")

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
)
db_meta = MetaData(naming_convention=convention, schema=DB_SCHEMA)
sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase, MappingBase):
    __tablename__: str
    __abstract__: bool

    metadata = db_meta


pochta_producer = RabbitDirectProducer(queue_name=MQ_POCHTA_QUEUE)

password_reset_cryptography = CryptographyProvider(
    PASSWORD_RESET_KEYS,
    encryption_ttl=60 * 60,
)
email_confirmation_cryptography = CryptographyProvider(
    EMAIL_CONFIRMATION_KEYS,
    encryption_ttl=60 * 60 * 24,
)

token_generator = TokenGenerator(randomness=40, length=50)
