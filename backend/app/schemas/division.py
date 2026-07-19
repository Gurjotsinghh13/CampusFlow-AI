import uuid
from datetime import datetime

from pydantic import ConfigDict, Field

from app.schemas.common import NonEmptyUpdateModel, StrippedModel


class DivisionBase(StrippedModel):
    name: str = Field(min_length=1, max_length=20, description='e.g. "A"')
    student_count: int = Field(ge=1, default=1)
    department_id: uuid.UUID
    semester_id: uuid.UUID


class DivisionCreate(DivisionBase):
    pass


class DivisionUpdate(NonEmptyUpdateModel):
    name: str | None = Field(default=None, min_length=1, max_length=20)
    student_count: int | None = Field(default=None, ge=1)
    department_id: uuid.UUID | None = None
    semester_id: uuid.UUID | None = None


class DivisionRead(DivisionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
