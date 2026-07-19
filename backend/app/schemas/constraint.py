import re
import uuid
from datetime import datetime

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.schemas.common import NonEmptyUpdateModel, StrippedModel

TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

VALID_DAYS = {"MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"}


def _time_to_minutes(value: str) -> int:
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


class ConstraintBase(StrippedModel):
    working_days: list[str] = Field(min_length=1, max_length=7)
    college_start_time: str
    college_end_time: str
    lunch_break_start: str
    lunch_break_end: str
    number_of_periods: int = Field(ge=1, le=20)
    theory_duration_minutes: int = Field(ge=15, le=180, default=60)
    practical_duration_minutes: int = Field(ge=30, le=300, default=120)

    @field_validator("working_days")
    @classmethod
    def validate_days(cls, value: list[str]) -> list[str]:
        normalized = [d.upper() for d in value]
        invalid = set(normalized) - VALID_DAYS
        if invalid:
            raise ValueError(f"Invalid day(s): {', '.join(invalid)}")
        if len(set(normalized)) != len(normalized):
            raise ValueError("working_days cannot contain duplicate days")
        return normalized

    @field_validator("college_start_time", "college_end_time", "lunch_break_start", "lunch_break_end")
    @classmethod
    def validate_time_format(cls, value: str) -> str:
        if not TIME_RE.match(value):
            raise ValueError("Time must be in HH:MM 24-hour format")
        return value

    @model_validator(mode="after")
    def validate_time_ordering(self) -> "ConstraintBase":
        if self.college_start_time >= self.college_end_time:
            raise ValueError("college_start_time must be before college_end_time")
        if self.lunch_break_start >= self.lunch_break_end:
            raise ValueError("lunch_break_start must be before lunch_break_end")
        if not (self.college_start_time <= self.lunch_break_start and self.lunch_break_end <= self.college_end_time):
            raise ValueError("Lunch break must fall within college hours")
        teaching_minutes = (
            _time_to_minutes(self.college_end_time)
            - _time_to_minutes(self.college_start_time)
            - (_time_to_minutes(self.lunch_break_end) - _time_to_minutes(self.lunch_break_start))
        )
        required_minutes = self.number_of_periods * self.theory_duration_minutes
        if required_minutes > teaching_minutes:
            raise ValueError("number_of_periods and theory_duration_minutes exceed available teaching time")
        return self


class ConstraintCreate(ConstraintBase):
    pass


class ConstraintUpdate(NonEmptyUpdateModel):
    working_days: list[str] | None = Field(default=None, min_length=1, max_length=7)
    college_start_time: str | None = None
    college_end_time: str | None = None
    lunch_break_start: str | None = None
    lunch_break_end: str | None = None
    number_of_periods: int | None = Field(default=None, ge=1, le=20)
    theory_duration_minutes: int | None = Field(default=None, ge=15, le=180)
    practical_duration_minutes: int | None = Field(default=None, ge=30, le=300)

    @field_validator("working_days")
    @classmethod
    def validate_days(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        normalized = [d.upper() for d in value]
        invalid = set(normalized) - VALID_DAYS
        if invalid:
            raise ValueError(f"Invalid day(s): {', '.join(invalid)}")
        if len(set(normalized)) != len(normalized):
            raise ValueError("working_days cannot contain duplicate days")
        return normalized

    @field_validator("college_start_time", "college_end_time", "lunch_break_start", "lunch_break_end")
    @classmethod
    def validate_time_format(cls, value: str | None) -> str | None:
        if value is not None and not TIME_RE.match(value):
            raise ValueError("Time must be in HH:MM 24-hour format")
        return value


class ConstraintRead(ConstraintBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
