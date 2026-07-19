import uuid
from datetime import datetime

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import NonEmptyUpdateModel, StrippedModel


class SubjectBase(StrippedModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=2, max_length=20)
    credits: int = Field(ge=1, le=10, default=3)
    theory_hours_per_week: int = Field(ge=0, le=20, default=0)
    practical_hours_per_week: int = Field(ge=0, le=20, default=0)
    semester_id: uuid.UUID
    department_id: uuid.UUID

    @model_validator(mode="after")
    def validate_has_teaching_hours(self) -> "SubjectBase":
        if self.theory_hours_per_week + self.practical_hours_per_week <= 0:
            raise ValueError("A subject must have at least one theory or practical hour per week")
        return self


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(NonEmptyUpdateModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    code: str | None = Field(default=None, min_length=2, max_length=20)
    credits: int | None = Field(default=None, ge=1, le=10)
    theory_hours_per_week: int | None = Field(default=None, ge=0, le=20)
    practical_hours_per_week: int | None = Field(default=None, ge=0, le=20)
    semester_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None


class SubjectRead(SubjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
