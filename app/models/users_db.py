from passlib.handlers.pbkdf2 import pbkdf2_sha256
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(100))

    InputModel = MappedModel.create(columns=[email])
    FullModel = MappedModel.create(columns=[id, email])

    @staticmethod
    def generate_hash(password: str) -> str:
        return pbkdf2_sha256.hash(password)
