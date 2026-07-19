import uuid
from datetime import datetime

from pydantic import ConfigDict, Field, field_validator

from app.schemas.common import NonEmptyUpdateModel, StrippedModel


def _is_consecutive_label(value: str) -> bool:
    start_year, end_year = value.split("-")
    return int(end_year) == int(start_year) + 1


class AcademicYearBase(StrippedModel):
    label: str = Field(min_length=9, max_length=9, pattern=r"^\d{4}-\d{4}$", description='e.g. "2025-2026"')
    is_active: bool = True

    @field_validator("label")
    @classmethod
    def validate_consecutive_label(cls, value: str) -> str:
        if not _is_consecutive_label(value):
            raise ValueError("Academic year label must span exactly one year, e.g. 2025-2026")
        return value


class AcademicYearCreate(AcademicYearBase):
    pass


class AcademicYearUpdate(NonEmptyUpdateModel):
    label: str | None = Field(default=None, min_length=9, max_length=9, pattern=r"^\d{4}-\d{4}$")
    is_active: bool | None = None

    @field_validator("label")
    @classmethod
    def validate_consecutive_label(cls, value: str | None) -> str | None:
        if value is not None and not _is_consecutive_label(value):
            raise ValueError("Academic year label must span exactly one year, e.g. 2025-2026")
        return value


class AcademicYearRead(AcademicYearBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
