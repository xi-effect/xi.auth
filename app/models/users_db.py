from pathlib import Path
from typing import Annotated, ClassVar

from passlib.handlers.pbkdf2 import pbkdf2_sha256
from pydantic import AfterValidator, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import AVATARS_PATH, Base


class User(Base):
    __tablename__ = "users"
    not_found_text: ClassVar[str] = "User not found"

    @staticmethod
    def generate_hash(password: str) -> str:
        return pbkdf2_sha256.hash(password)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(30))
    password: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[str | None] = mapped_column(String(30))
    theme: Mapped[str] = mapped_column(String(10), default="system")

    __table_args__ = (
        Index("hash_index_users_username", username, postgresql_using="hash"),
        Index("hash_index_users_email", email, postgresql_using="hash"),
    )

    PasswordType = Annotated[
        str, Field(min_length=6, max_length=100), AfterValidator(generate_hash)
    ]
    UsernameType = Annotated[str, Field(pattern=r"[a-z0-9_\.]{5,30}")]

    InputModel = MappedModel.create(
        columns=[
            (username, UsernameType),
            email,  # TODO (email, Annotated[str, AfterValidator(email_validator)]),
            (password, PasswordType),
        ]
    )
    CredentialsModel = MappedModel.create(columns=[email, password])
    ProfileModel = MappedModel.create(
        columns=[(username, UsernameType), display_name, theme]
    )
    ProfilePatchModel = ProfileModel.as_patch()
    FullModel = ProfileModel.extend(columns=[id, email])
    FullPatchModel = InputModel.extend(columns=[display_name, theme]).as_patch()

    def is_password_valid(self, password: str) -> bool:
        return pbkdf2_sha256.verify(password, self.password)

    @property
    def avatar_path(self) -> Path:
        return AVATARS_PATH / f"{self.id}.webp"
