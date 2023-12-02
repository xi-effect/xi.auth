from typing import Annotated, ClassVar

from passlib.handlers.pbkdf2 import pbkdf2_sha256
from pydantic import AfterValidator, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


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

    __table_args__ = (
        Index("hash_index_users_username", username, postgresql_using="hash"),
        Index("hash_index_users_email", email, postgresql_using="hash"),
    )

    PasswordType = Annotated[
        str, Field(min_length=6, max_length=100), AfterValidator(generate_hash)
    ]

    InputModel = MappedModel.create(
        columns=[
            (username, Annotated[str, Field(pattern=r"[a-z0-9_\.]{5,30}")]),
            email,  # TODO (email, Annotated[str, AfterValidator(email_validator)]),
            (password, PasswordType),
        ]
    )
    PatchModel = InputModel.as_patch()
    CredentialsModel = MappedModel.create(columns=[email, password])
    ProfileModel = MappedModel.create(columns=[id, username])
    FullModel = ProfileModel.extend(columns=[email])

    def is_password_valid(self, password: str) -> bool:
        return pbkdf2_sha256.verify(password, self.password)
