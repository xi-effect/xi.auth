from typing import Annotated, ClassVar

from passlib.handlers.pbkdf2 import pbkdf2_sha256
from pydantic import AfterValidator
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


class User(Base):
    __tablename__ = "users"
    not_found_text: ClassVar[str] = "User not found"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(100))

    __table_args__ = (Index("hash_index_users_email", email, postgresql_using="hash"),)

    InputModel = MappedModel.create(columns=[email, password])
    PatchModel = InputModel.as_patch()
    FullModel = MappedModel.create(columns=[id, email])

    @staticmethod
    def generate_hash(password: str) -> str:
        return pbkdf2_sha256.hash(password)

    def is_password_valid(self, password: str) -> bool:
        return pbkdf2_sha256.verify(password, self.password)


class UserPasswordModel(User.InputModel):
    password: Annotated[str, AfterValidator(User.generate_hash)]
