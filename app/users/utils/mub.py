from typing import Annotated, Final

from fastapi import Depends
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.config import MUB_KEY
from app.common.fastapi_ext import Responses, with_responses

MUB_KEY_HEADER_NAME: Final[str] = "X-MUB-Secret"

header_mub_scheme = APIKeyHeader(
    name=MUB_KEY_HEADER_NAME, auto_error=False, scheme_name="mub key header"
)
MUBKeyHeader = Annotated[str | None, Depends(header_mub_scheme)]


class MUBResponses(Responses):
    INVALID_MUB_KEY = (HTTP_401_UNAUTHORIZED, "Invalid key")


@with_responses(MUBResponses)
def mub_key_verification(mub_key: MUBKeyHeader = None) -> None:
    if mub_key != MUB_KEY:
        raise MUBResponses.INVALID_MUB_KEY.value


MUBProtection = Depends(mub_key_verification)
