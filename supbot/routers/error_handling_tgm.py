import logging
from typing import Literal

from aiogram import Router
from aiogram.types import ErrorEvent

router = Router()


@router.errors()
async def error_handler(error: ErrorEvent) -> Literal[True]:
    logging.error(f"Error in supbot: {error.exception}", exc_info=error.exception)
    return True
