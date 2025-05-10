from typing import Annotated

from fastapi import Depends, UploadFile
from filetype import filetype  # type: ignore[import-untyped]
from filetype.types.archive import Pdf  # type: ignore[import-untyped]

from app.common.fastapi_ext import Responses, with_responses


class ResumeFileResponses(Responses):
    WRONG_FORMAT = 415, "Invalid file format"


@with_responses(ResumeFileResponses)
async def validate_resume_file(resume: UploadFile) -> UploadFile:
    if not filetype.match(resume.file, [Pdf()]):
        raise ResumeFileResponses.WRONG_FORMAT
    return resume


ResumeFile = Annotated[UploadFile, Depends(validate_resume_file)]
