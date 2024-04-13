from pydantic import BaseModel
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.config import email_confirmation_cryptography
from app.common.fastapi_extension import APIRouterExt, Responses
from app.models.users_db import User

router = APIRouterExt(tags=["email confirmation"])


class EmailConfirmationResponses(Responses):
    INVALID_TOKEN = (HTTP_401_UNAUTHORIZED, "Invalid token")


class EmailConfirmationData(BaseModel):
    confirmation_token: str


@router.post(
    "/confirmations/",
    responses=EmailConfirmationResponses.responses(),
    summary="Confirm user's email",
    status_code=204,
)
async def confirm_email(confirmation_token: EmailConfirmationData) -> None:
    email: str | None = email_confirmation_cryptography.decrypt(
        confirmation_token.confirmation_token
    )
    if email is None:
        raise EmailConfirmationResponses.INVALID_TOKEN
    user = await User.find_first_by_kwargs(email=email)
    if user is None:
        raise EmailConfirmationResponses.INVALID_TOKEN
    user.email_confirmed = True
