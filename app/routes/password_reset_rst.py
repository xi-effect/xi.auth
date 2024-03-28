from aio_pika import Message
from fastapi import APIRouter
from pydantic import BaseModel
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.config import password_reset_cryptography, pochta_producer
from app.common.responses import Responses
from app.models.users_db import User
from app.utils.users import UserResponses

router = APIRouter(tags=["password reset"])


@router.post(
    "/requests/",
    responses=UserResponses.responses(),
    summary="Request for a password reset",
    status_code=202,
)
async def request_password_reset(data: User.EmailModel) -> None:
    user = await User.find_first_by_kwargs(email=data.email)
    if user is None:
        raise UserResponses.USER_NOT_FOUND
    reset_token = password_reset_cryptography.encrypt(user.generated_reset_token)
    await pochta_producer.send_message(
        message=Message(f"Hi {data}! reset_token: {reset_token}".encode("utf-8")),
    )


class ResetCredentials(BaseModel):
    reset_token: str
    new_password: User.PasswordType


class ResetCompleteResponses(Responses):
    INVALID_TOKEN = (HTTP_401_UNAUTHORIZED, "Invalid token")


@router.post(
    "/confirmations/",
    responses=ResetCompleteResponses.responses(),
    summary="Confirm password reset and set a new password",
    status_code=204,
)
async def confirm_password_reset(reset_data: ResetCredentials) -> None:
    token = password_reset_cryptography.decrypt(reset_data.reset_token)
    if token is None:
        raise ResetCompleteResponses.INVALID_TOKEN
    user = await User.find_first_by_kwargs(reset_token=token)
    if user is None:
        raise ResetCompleteResponses.INVALID_TOKEN
    user.reset_password(password=reset_data.new_password)
