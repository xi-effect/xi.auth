from pydantic import BaseModel


class VacancyFormSchema(BaseModel):
    position: str
    name: str
    telegram: str
    message: str | None = None
