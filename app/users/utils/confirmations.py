from pydantic import BaseModel
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_429_TOO_MANY_REQUESTS

from app.common.fastapi_ext import Responses


class TokenVerificationResponses(Responses):
    INVALID_TOKEN = (HTTP_401_UNAUTHORIZED, "Invalid token")


class ConfirmationTokenData(BaseModel):
    token: str


class EmailResendResponses(Responses):
    TOO_MANY_EMAILS = (HTTP_429_TOO_MANY_REQUESTS, "Too many emails")
