import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.timetable import GenerationStatus


class GenerateTimetableRequest(BaseModel):
    academic_year_id: uuid.UUID


class PeriodSlotSchema(BaseModel):
    period_index: int
    label: str
    start_time: str
    end_time: str
    duration_minutes: int = 60
    is_before_lunch: bool = True
    is_after_lunch: bool = False


class TimetableEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    day: str
    period_index: int
    start_time: str | None = None
    end_time: str | None = None
    session_type: Literal["THEORY", "PRACTICAL"]
    division_id: uuid.UUID
    subject_id: uuid.UUID
    faculty_id: uuid.UUID
    room_id: uuid.UUID
    division_name: str
    subject_name: str
    subject_code: str
    faculty_name: str
    room_number: str


class GeneratedTimetableRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    academic_year_id: uuid.UUID
    academic_year_label: str
    status: GenerationStatus
    solver_wall_time_seconds: float | None
    objective_value: float | None
    message: str | None
    working_days: list[str]
    periods_per_day: int
    theory_duration_minutes: int
    practical_duration_minutes: int
    period_slots: list[PeriodSlotSchema] = Field(default_factory=list)
    created_at: datetime


class GeneratedTimetableDetail(GeneratedTimetableRead):
    entries: list[TimetableEntryRead] = Field(default_factory=list)
