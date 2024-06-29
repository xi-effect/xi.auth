import logging
from typing import Literal

from aiogram import Router
from aiogram.types import ErrorEvent

router = Router()


@router.errors()
async def error_handler(error: ErrorEvent) -> Literal[True]:
    logging.error(f"An error has occurred: {error.exception}", exc_info=True)
    return True
