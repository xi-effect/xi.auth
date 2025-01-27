import sys
from pathlib import Path

from aiosmtplib import SMTP
from cryptography.fernet import Fernet
from pydantic import AmqpDsn, BaseModel, Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.common.aiopika_ext import RabbitDirectProducer
from app.common.cryptography import CryptographyProvider, TokenGenerator
from app.common.sqlalchemy_ext import MappingBase, sqlalchemy_naming_convention


class FernetSettings(BaseModel):
    current_key: str = Field(default_factory=lambda: Fernet.generate_key().decode())
    backup_key: str | None = None
    encryption_ttl: int

    @computed_field
    @property
    def keys(self) -> list[str]:
        return (
            [self.current_key]
            if self.backup_key is None
            else [self.current_key, self.backup_key]
        )


class EmailSettings(BaseModel):
    hostname: str
    username: str
    password: str
    port: int = 465
    timeout: int = 20
    use_tls: bool = True


class SupbotSettings(BaseModel):
    token: str
    group_id: int
    channel_id: int
    polling: bool = False
    webhook_url: str = "http://localhost:5100"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_ignore_empty=True,
        nested_model_default_partial_update=True,
    )

    production_mode: bool = False

    @computed_field
    @property
    def is_testing_mode(self) -> bool:
        return "pytest" in sys.modules

    mub_key: str = "local"

    bridge_base_url: str = "http://localhost:8000"
    cookie_domain: str = "localhost"

    password_reset_keys: FernetSettings = FernetSettings(encryption_ttl=60 * 60)
    email_confirmation_keys: FernetSettings = FernetSettings(
        encryption_ttl=60 * 60 * 24
    )

    demo_webhook_url: str | None = None
    vacancy_webhook_url: str | None = None

    base_path: Path = Path.cwd()
    avatars_folder: Path = Path("avatars")

    @computed_field
    @property
    def avatars_path(self) -> Path:
        return self.base_path / self.avatars_folder

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_username: str = "test"
    postgres_password: str = "test"
    postgres_database: str = "test"
    postgres_schema: str | None = None
    postgres_automigrate: bool = True
    postgres_echo: bool = True
    postgres_pool_recycle: int = 280

    @computed_field
    @property
    def postgres_dsn(self) -> str:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.postgres_username,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_database,
        ).unicode_string()

    mq_host: str = "localhost"
    mq_port: int = 5672
    mq_username: str = "guest"
    mq_password: str = "guest"
    mq_pochta_queue: str = "pochta.send"

    @computed_field
    @property
    def mq_dsn(self) -> str:
        return AmqpDsn.build(
            scheme="amqp",
            username=self.mq_username,
            password=self.mq_password,
            host=self.mq_host,
            port=self.mq_port,
        ).unicode_string()

    email: EmailSettings | None = None
    supbot: SupbotSettings | None = None


settings = Settings()

smtp_client: SMTP | None = (
    None
    if settings.email is None
    else SMTP(
        hostname=settings.email.hostname,
        username=settings.email.username,
        password=settings.email.password,
        use_tls=settings.email.use_tls,
        port=settings.email.port,
        timeout=settings.email.timeout,
    )
)

engine = create_async_engine(
    settings.postgres_dsn,
    echo=settings.postgres_echo,
    pool_recycle=settings.postgres_pool_recycle,
)
db_meta = MetaData(
    naming_convention=sqlalchemy_naming_convention,
    schema=settings.postgres_schema,
)
sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase, MappingBase):
    __tablename__: str
    __abstract__: bool

    metadata = db_meta


pochta_producer = RabbitDirectProducer(queue_name=settings.mq_pochta_queue)

password_reset_cryptography = CryptographyProvider(
    settings.password_reset_keys.keys,
    encryption_ttl=settings.password_reset_keys.encryption_ttl,
)
email_confirmation_cryptography = CryptographyProvider(
    settings.email_confirmation_keys.keys,
    encryption_ttl=settings.email_confirmation_keys.encryption_ttl,
)

token_generator = TokenGenerator(randomness=40, length=50)
