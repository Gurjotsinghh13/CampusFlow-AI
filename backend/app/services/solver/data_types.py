from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID


class SessionType(str, Enum):
    THEORY = "THEORY"
    PRACTICAL = "PRACTICAL"


@dataclass(frozen=True)
class DivisionData:
    id: UUID
    name: str
    department_id: UUID
    semester_id: UUID
    student_count: int


@dataclass(frozen=True)
class SubjectData:
    id: UUID
    name: str
    code: str
    semester_id: UUID
    department_id: UUID
    theory_sessions_per_week: int
    practical_sessions_per_week: int
    eligible_faculty_ids: tuple[UUID, ...]


@dataclass(frozen=True)
class FacultyData:
    id: UUID
    full_name: str
    department_id: UUID
    max_daily_lectures: int
    max_weekly_lectures: int


@dataclass(frozen=True)
class RoomData:
    id: UUID
    room_number: str
    capacity: int
    room_type: str  # "CLASSROOM" | "LAB"


@dataclass(frozen=True)
class SessionRequirement:
    """One required weekly occurrence that the solver must place on the grid."""

    division_id: UUID
    subject_id: UUID
    session_type: SessionType
    session_index: int  # 0-based instance number among sessions of this type for this (division, subject)
    duration_periods: int
    eligible_faculty_ids: tuple[UUID, ...]
    eligible_room_ids: tuple[UUID, ...]

    @property
    def key(self) -> str:
        return f"{self.division_id}:{self.subject_id}:{self.session_type.value}:{self.session_index}"


@dataclass
class SolverInput:
    days: list[str]
    periods_per_day: int
    theory_duration_minutes: int
    practical_duration_minutes: int
    divisions: dict[UUID, DivisionData]
    subjects: dict[UUID, SubjectData]
    faculty: dict[UUID, FacultyData]
    rooms: dict[UUID, RoomData]
    requirements: list[SessionRequirement] = field(default_factory=list)
