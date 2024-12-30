from pydantic import BaseModel


class VacancyFormSchema(BaseModel):
    name: str
    telegram: str
    position: str
    link: str
    message: str | None = None
