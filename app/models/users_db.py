import enum
from datetime import datetime
from pathlib import Path
from secrets import token_urlsafe
from typing import Annotated, ClassVar

from passlib.handlers.pbkdf2 import pbkdf2_sha256
from pydantic import AfterValidator, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import CHAR, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import AVATARS_PATH, Base


class OnboardingStage(str, enum.Enum):
    CREATED = "created"
    COMMUNITY_CHOICE = "community-choice"
    COMMUNITY_CREATE = "community-create"
    COMMUNITY_INVITE = "community-invite"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"
    not_found_text: ClassVar[str] = "User not found"
    token_randomness: ClassVar[int] = 40
    token_length: ClassVar[int] = 15

    @staticmethod
    def generate_hash(password: str) -> str:
        return pbkdf2_sha256.hash(password)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(30))
    password: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[str | None] = mapped_column(String(30))
    onboarding_stage: Mapped[OnboardingStage] = mapped_column(
        Enum(OnboardingStage), default=OnboardingStage.CREATED
    )
    theme: Mapped[str] = mapped_column(String(10), default="system")

    reset_token: Mapped[str | None] = mapped_column(CHAR(token_length))
    last_password_change: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        Index("hash_index_users_username", username, postgresql_using="hash"),
        Index("hash_index_users_email", email, postgresql_using="hash"),
        Index("hash_index_users_token", reset_token, postgresql_using="hash"),
    )

    PasswordType = Annotated[
        str, Field(min_length=6, max_length=100), AfterValidator(generate_hash)
    ]
    UsernameType = Annotated[str, Field(pattern=r"[a-z0-9_\.]{5,30}")]
    EmailModel = MappedModel.create(
        columns=[email]
    )  # TODO (email, Annotated[str, AfterValidator(email_validator)]),
    InputModel = EmailModel.extend(
        columns=[
            (username, UsernameType),
            (password, PasswordType),
        ]
    )
    PasswordModel = MappedModel.create(columns=[password])
    CredentialsModel = MappedModel.create(columns=[email, password])
    UserProfileModel = MappedModel.create(
        columns=[id, (username, UsernameType), display_name]
    )
    ProfileModel = MappedModel.create(
        columns=[(username, UsernameType), display_name, theme]
    )
    ProfilePatchModel = ProfileModel.as_patch()
    FullModel = ProfileModel.extend(columns=[id, email, onboarding_stage])
    FullPatchModel = InputModel.extend(
        columns=[display_name, theme, onboarding_stage]
    ).as_patch()

    def is_password_valid(self, password: str) -> bool:
        return pbkdf2_sha256.verify(password, self.password)

    def generate_token(self) -> str:
        return token_urlsafe(self.token_randomness)[: self.token_length]

    @property
    def avatar_path(self) -> Path:
        return AVATARS_PATH / f"{self.id}.webp"

    @property
    def generated_reset_token(self) -> str:  # noqa: FNE002  # reset is a noun here
        if self.reset_token is None:
            self.reset_token = self.generate_token()
        return self.reset_token

    def reset_password(self, password: str) -> None:
        self.password = password
        self.last_password_change = datetime.utcnow()
        self.reset_token = None
