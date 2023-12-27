from typing import Annotated, ClassVar, Self

from passlib.handlers.pbkdf2 import pbkdf2_sha256
from pydantic import AfterValidator, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqla import db


class User(Base):
    __tablename__ = "users"
    not_found_text: ClassVar[str] = "User not found"

    @staticmethod
    def generate_hash(password: str) -> str:
        return pbkdf2_sha256.hash(password)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(100))

    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(100))
    theme: Mapped[str] = mapped_column(String(10), default="system")

    __table_args__ = (
        Index("hash_index_users_username", username, postgresql_using="hash"),
        Index("hash_index_users_email", email, postgresql_using="hash"),
    )

    PasswordType = Annotated[
        str, Field(min_length=6, max_length=100), AfterValidator(generate_hash)
    ]

    InputModel = MappedModel.create(
        columns=[
            (username, Annotated[str, Field(pattern=r"[a-z0-9_\.]{5,100}")]),
            email,  # TODO (email, Annotated[str, AfterValidator(email_validator)]),
            (password, PasswordType),
        ]
    )
    InputPatchModel = InputModel.as_patch()
    CredentialsModel = MappedModel.create(columns=[email, password])
    ProfileModel = MappedModel.create(
        columns=[
            (username, Annotated[str, Field(pattern=r"[a-z0-9_\.]{5,100}")]),
            display_name,
        ]
    )
    ProfilePatchModel = ProfileModel.as_patch()
    ThemeModel = MappedModel.create(columns=[theme]).as_patch()
    CurrentThemeModel = ThemeModel.extend(columns=[id])
    FullModel = ProfileModel.extend(columns=[id, email])

    def is_password_valid(self, password: str) -> bool:
        return pbkdf2_sha256.verify(password, self.password)

    async def username_verify(self, username: str | None) -> Self | None:
        if username is None:
            return None
        stmt = User.select_by_kwargs(username=username).filter(User.id != self.id)
        return await db.get_first(stmt)
