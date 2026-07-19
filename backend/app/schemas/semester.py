import uuid
from datetime import datetime

from pydantic import ConfigDict, Field

from app.schemas.common import NonEmptyUpdateModel, StrippedModel


class SemesterBase(StrippedModel):
    number: int = Field(ge=1, le=12)
    academic_year_id: uuid.UUID


class SemesterCreate(SemesterBase):
    pass


class SemesterUpdate(NonEmptyUpdateModel):
    number: int | None = Field(default=None, ge=1, le=12)
    academic_year_id: uuid.UUID | None = None


class SemesterRead(SemesterBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
