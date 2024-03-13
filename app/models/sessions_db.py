from collections.abc import Sequence
from datetime import datetime, timedelta
from secrets import token_urlsafe
from typing import Any, ClassVar, Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import CHAR, ForeignKey, Index, delete, select, update
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.common.sqla import db
from app.models.users_db import User


class Session(Base):
    __tablename__ = "sessions"
    not_found_text: ClassVar[str] = "Session not found"

    token_randomness: ClassVar[int] = 40
    token_length: ClassVar[int] = 50

    expiry_timeout: ClassVar[timedelta] = timedelta(days=7)
    renew_period_length: ClassVar[timedelta] = timedelta(days=3)

    max_concurrent_sessions: ClassVar[int] = 10
    max_history_sessions: ClassVar[int] = 20
    max_history_timedelta: ClassVar[timedelta] = timedelta(days=7)

    @staticmethod
    def generate_token() -> str:
        return token_urlsafe(Session.token_randomness)[: Session.token_length]

    @staticmethod
    def generate_expiry() -> datetime:
        return datetime.utcnow() + Session.expiry_timeout

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete="CASCADE"))
    user: Mapped[User] = relationship(passive_deletes=True)

    # Security
    token: Mapped[str] = mapped_column(CHAR(token_length))
    expiry: Mapped[datetime] = mapped_column(default=generate_expiry)
    disabled: Mapped[bool] = mapped_column(default=False)

    @property
    def invalid(self) -> bool:  # noqa: FNE005
        return self.disabled or self.expiry < datetime.utcnow()

    # User info
    created: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    cross_site: Mapped[bool] = mapped_column(default=False)

    # Admin
    mub: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (
        Index("hash_index_session_token", token, postgresql_using="hash"),
    )

    FullModel = MappedModel.create(
        columns=[id, created, expiry, disabled],
        properties=[invalid],
    )
    MUBFullModel = FullModel.extend(columns=[mub])

    def is_renewal_required(self) -> bool:
        return self.expiry - self.renew_period_length < datetime.utcnow()

    def renew(self) -> None:
        self.token = self.generate_token()
        self.expiry = self.generate_expiry()

    @classmethod
    async def create(cls, **kwargs: Any) -> Self:
        if kwargs.get("token") is None:
            token = cls.generate_token()
            if (await Session.find_first_by_kwargs(token=token)) is not None:
                raise RuntimeError("Token collision happened (!wow!)")
            kwargs["token"] = token
        return await super().create(**kwargs)

    @classmethod
    async def find_by_user(
        cls,
        user_id: int,
        exclude_id: int | None = None,
    ) -> Sequence[Self]:
        stmt = (
            select(cls)
            .filter_by(user_id=user_id, mub=False)
            .order_by(cls.expiry.desc())
        )
        if exclude_id is not None:
            stmt = stmt.filter(cls.id != exclude_id)
        return await db.get_all(stmt)

    async def disable_all_other(self) -> None:
        await db.session.execute(
            update(type(self))
            .where(
                type(self).id != self.id,
                type(self).mub.is_(False),
                type(self).user_id == self.user_id,
                type(self).disabled.is_(False),
            )
            .values(disabled=True)
        )

    @classmethod
    async def cleanup_concurrent_by_user(cls, user_id: int) -> None:
        """Disable sessions above :py:attr:`max_concurrent_sessions`"""
        first_outside_limit: Self | None = await db.get_first(
            select(cls)
            .filter(cls.disabled.is_(False), cls.expiry >= datetime.utcnow())
            .filter_by(user_id=user_id, mub=False)
            .order_by(cls.expiry.desc())
            .offset(cls.max_concurrent_sessions)
        )
        if first_outside_limit is not None:
            await db.session.execute(
                update(cls)
                .where(
                    cls.user_id == user_id,
                    cls.mub.is_(False),
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

    @classmethod
    async def find_active_mub_session(cls, user_id: int) -> Self | None:
        return await db.get_first(
            select(cls)
            .filter(cls.disabled.is_(False), cls.expiry > datetime.utcnow())
            .filter_by(user_id=user_id)
            .order_by(cls.expiry.desc())
        )
