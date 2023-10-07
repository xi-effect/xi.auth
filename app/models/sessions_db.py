from datetime import datetime, timedelta
from secrets import token_urlsafe
from typing import ClassVar, Self

from sqlalchemy import CHAR, ForeignKey, Index, delete, select, update
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.common.sqla import db
from app.models.users_db import User


class Session(Base):
    __tablename__ = "sessions"
    not_found_text: ClassVar[str] = "Session not found"
    max_concurrent_sessions: ClassVar[int] = 10
    max_history_sessions: ClassVar[int] = 20
    max_history_timedelta: ClassVar[timedelta] = timedelta(days=7)

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

    @classmethod
    async def cleanup_concurrent_by_user(cls, user_id: int) -> None:
        """Disable sessions above :py:attr:`max_concurrent_sessions`"""
        first_outside_limit: Self | None = await db.get_first(
            select(cls)
            .filter(cls.disabled.is_(False), cls.expiry >= datetime.utcnow())
            .filter_by(user_id=user_id)
            .order_by(cls.expiry.desc())
            .offset(cls.max_concurrent_sessions)
        )
        if first_outside_limit is not None:
            await db.session.execute(
                update(cls)
                .where(
                    cls.user_id == user_id,
                    cls.expiry <= first_outside_limit.expiry,
                    cls.disabled.is_(False),
                )
                .values(disabled=True)
            )

    @classmethod
    async def cleanup_history_by_user(cls, user_id: int) -> None:
        """
        Delete sessions for the list of invalid ones, which are
        above :py:attr:`max_history_sessions` by number in the list
        or expired more than :py:attr:`max_history_timedelta` ago
        """

        max_outside_timestamp = datetime.utcnow() - cls.max_history_timedelta
        outside_limit: datetime = (
            await db.get_first(
                select(cls.expiry)
                .filter(
                    cls.expiry > max_outside_timestamp
                )  # if greater, fallback to max
                .filter_by(user_id=user_id)
                .order_by(cls.expiry.desc())
                .offset(cls.max_history_sessions)
            )
            or max_outside_timestamp
        )

        await db.session.execute(
            delete(cls).where(
                cls.user_id == user_id,
                cls.expiry <= outside_limit,
            )
        )

    @classmethod
    async def cleanup_by_user(cls, user_id: int) -> None:
        await cls.cleanup_concurrent_by_user(user_id)
        await cls.cleanup_history_by_user(user_id)
