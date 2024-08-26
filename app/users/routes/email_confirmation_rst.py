from aio_pika import Message
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.config import email_confirmation_cryptography, pochta_producer
from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.models.users_db import User
from app.users.utils.authorization import AuthorizedUser
from app.users.utils.confirmations import (
    ConfirmationTokenData,
    EmailResendResponses,
    TokenVerificationResponses,
)

router = APIRouterExt(tags=["email confirmation"])


class EmailConfirmationResponses(Responses):
    INVALID_TOKEN = (HTTP_401_UNAUTHORIZED, "Invalid token")


@router.post(
    "/confirmations/",
    responses=TokenVerificationResponses.responses(),
    summary="Confirm user's email",
    status_code=204,
)
async def confirm_email(confirmation_token: ConfirmationTokenData) -> None:
    email: str | None = email_confirmation_cryptography.decrypt(
        confirmation_token.token
    )
    if email is None:
        raise TokenVerificationResponses.INVALID_TOKEN
    user = await User.find_first_by_kwargs(email=email)
    if user is None:
        raise TokenVerificationResponses.INVALID_TOKEN
    user.email_confirmed = True


@router.post(
    "/requests/",
    responses=EmailResendResponses.responses(),
    summary="Resend email confirmation message",
    status_code=204,
)
async def resend_email_confirmation(user: AuthorizedUser) -> None:
    if not user.is_email_confirmation_resend_allowed():
        raise EmailResendResponses.TOO_MANY_EMAILS
    confirmation_token: str = email_confirmation_cryptography.encrypt(user.email)
    user.set_confirmation_resend_timeout()
    await pochta_producer.send_message(
        message=Message(
            f"Hi {user.email}, verify email: {confirmation_token}".encode("utf-8")
        ),
    )
