from typing import Annotated

from pydantic import BaseModel, Field


class DemoFormSchema(BaseModel):
    name: str
    contacts: Annotated[list[str], Field(min_length=1)]
