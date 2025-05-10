from typing import Literal

from pydantic import BaseModel, Field

from app.common.config import settings
from app.common.redis_ext import RedisRouter


class RegistrationEmailV1Data(BaseModel):
    template: Literal["registration-v1"] = "registration-v1"
    email_confirmation_token: str


class RegistrationEmailV2Data(BaseModel):
    template: Literal["registration-v2"] = "registration-v2"
    email_confirmation_token: str
    username: str


class PasswordResetEmailData(BaseModel):
    template: Literal["password-reset-v1"] = "password-reset-v1"
    reset_confirmation_token: str


class EmailSendRequest(BaseModel):
    email: str
    data: RegistrationEmailV1Data | RegistrationEmailV2Data | PasswordResetEmailData = Field(discriminator="template")


# {{ data.email_confirmation_token }}

# {"email": "test@test.test", "data": {"template": "registration-v1", "email_confirmation_token": ""}}
# {"email": "test@test.test", "data": {"template": "password-reset-v1", "reset_confirmation_token": ""}}


class PochtaSchema(BaseModel):
    key: str


router = RedisRouter()


@router.add_consumer(
    stream_name=settings.redis_pochta_stream,
    group_name="pochta:group",
    consumer_name="pochta_consumer",
)
async def process_email_message(message: PochtaSchema) -> None:
    print(f"Message: {message}")  # noqa T201  # temporary print for debugging
