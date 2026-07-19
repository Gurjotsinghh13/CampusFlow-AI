import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import NonEmptyUpdateModel, StrippedModel


class SubjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str


class FacultyBase(StrippedModel):
    full_name: str = Field(min_length=2, max_length=150)
    employee_id: str = Field(min_length=2, max_length=30)
    max_daily_lectures: int = Field(ge=1, le=12, default=4)
    max_weekly_lectures: int = Field(ge=1, le=60, default=20)
    department_id: uuid.UUID


class FacultyCreate(FacultyBase):
    subject_ids: list[uuid.UUID] = Field(default_factory=list)

    @field_validator("subject_ids")
    @classmethod
    def validate_unique_subject_ids(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(set(value)) != len(value):
            raise ValueError("subject_ids cannot contain duplicates")
        return value


class FacultyUpdate(NonEmptyUpdateModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    employee_id: str | None = Field(default=None, min_length=2, max_length=30)
    max_daily_lectures: int | None = Field(default=None, ge=1, le=12)
    max_weekly_lectures: int | None = Field(default=None, ge=1, le=60)
    department_id: uuid.UUID | None = None


class FacultySubjectAssignment(BaseModel):
    subject_ids: list[uuid.UUID]

    @field_validator("subject_ids")
    @classmethod
    def validate_unique_subject_ids(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(set(value)) != len(value):
            raise ValueError("subject_ids cannot contain duplicates")
        return value


class FacultyRead(FacultyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subjects: list[SubjectSummary] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
