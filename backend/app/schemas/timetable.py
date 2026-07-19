import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.timetable import GenerationStatus


class GenerateTimetableRequest(BaseModel):
    academic_year_id: uuid.UUID


class TimetableEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    day: str
    period_index: int
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
    created_at: datetime


class GeneratedTimetableDetail(GeneratedTimetableRead):
    entries: list[TimetableEntryRead] = Field(default_factory=list)
