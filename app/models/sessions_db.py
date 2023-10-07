from datetime import datetime, timedelta
from secrets import token_urlsafe
from typing import ClassVar

from sqlalchemy import CHAR, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.models.users_db import User


class Session(Base):
    __tablename__ = "sessions"
    not_found_text: ClassVar[str] = "Session not found"

    @staticmethod
    def generate_token() -> str:
        return token_urlsafe(40)[:50]

    @staticmethod
    def generate_expiry() -> datetime:
        return datetime.utcnow() + timedelta(days=7)

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete="CASCADE"))
    user: Mapped[User] = relationship(passive_deletes=True)

    # Security
    token: Mapped[str] = mapped_column(CHAR(50), default=generate_token)
    expiry: Mapped[datetime] = mapped_column(default=generate_expiry)
    disabled: Mapped[bool] = mapped_column(default=False)

    @property
    def invalid(self) -> bool:  # noqa: FNE005
        return self.disabled or self.expiry < datetime.utcnow()

    # User info
    created: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        Index("hash_index_session_token", token, postgresql_using="hash", unique=True),
    )
