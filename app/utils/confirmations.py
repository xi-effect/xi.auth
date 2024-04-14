from pydantic import BaseModel
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.fastapi_extension import Responses


class TokenVerificationResponses(Responses):
    INVALID_TOKEN = (HTTP_401_UNAUTHORIZED, "Invalid token")


class ConfirmationTokenData(BaseModel):
    token: str
