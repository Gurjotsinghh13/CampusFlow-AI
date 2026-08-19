import math
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.room import RoomType
from app.models.timetable import GeneratedTimetable, TimetableEntry
from app.repositories.constraint import ConstraintRepository
from app.repositories.division import DivisionRepository
from app.repositories.faculty import FacultyRepository
from app.repositories.room import RoomRepository
from app.repositories.timetable import GeneratedTimetableRepository
from app.schemas.timetable import GeneratedTimetableRead, PeriodSlotSchema, TimetableEntryRead
from app.services.solver.solver_service import TimetableSolverService
from app.utils.timeline import (
    get_period_schedule_from_timetable_record,
    get_session_time_range,
)


class GeneratedTimetableService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = GeneratedTimetableRepository(db)
        self.division_repo = DivisionRepository(db)
        self.faculty_repo = FacultyRepository(db)
        self.room_repo = RoomRepository(db)
        self.constraint_repo = ConstraintRepository(db)
        self.solver_service = TimetableSolverService(db)

    def _get_active_constraint(self):
        return self.constraint_repo.get_singleton()

    def to_read_dto(self, timetable: GeneratedTimetable) -> GeneratedTimetableRead:
        constraint = self._get_active_constraint()
        slots = get_period_schedule_from_timetable_record(timetable, constraint)
        return GeneratedTimetableRead(
            id=timetable.id,
            academic_year_id=timetable.academic_year_id,
            academic_year_label=timetable.academic_year_label,
            status=timetable.status,
            solver_wall_time_seconds=timetable.solver_wall_time_seconds,
            objective_value=timetable.objective_value,
            message=timetable.message,
            working_days=list(timetable.working_days),
            periods_per_day=timetable.periods_per_day,
            theory_duration_minutes=timetable.theory_duration_minutes,
            practical_duration_minutes=timetable.practical_duration_minutes,
            period_slots=[PeriodSlotSchema(**s.to_dict()) for s in slots],
            created_at=timetable.created_at,
        )

    def to_entry_read_dtos(
        self,
        timetable: GeneratedTimetable,
        entries: list[TimetableEntry],
    ) -> list[TimetableEntryRead]:
        constraint = self._get_active_constraint()
        slots = get_period_schedule_from_timetable_record(timetable, constraint)
        practical_block = max(1, math.ceil(timetable.practical_duration_minutes / timetable.theory_duration_minutes))

        dtos = []
        for e in entries:
            duration = practical_block if e.session_type == "PRACTICAL" else 1
            start_time, end_time = get_session_time_range(e.period_index, duration, slots)
            dtos.append(
                TimetableEntryRead(
                    id=e.id,
                    day=e.day,
                    period_index=e.period_index,
                    start_time=start_time,
                    end_time=end_time,
                    session_type=e.session_type,
                    division_id=e.division_id,
                    subject_id=e.subject_id,
                    faculty_id=e.faculty_id,
                    room_id=e.room_id,
                    division_name=e.division_name,
                    subject_name=e.subject_name,
                    subject_code=e.subject_code,
                    faculty_name=e.faculty_name,
                    room_number=e.room_number,
                )
            )
        return dtos

    def generate(self, academic_year_id: uuid.UUID) -> GeneratedTimetable:
        return self.solver_service.generate(academic_year_id)

    def list_timetables(self, page: int, page_size: int, academic_year_id: uuid.UUID | None):
        return self.repo.list(page=page, page_size=page_size, academic_year_id=academic_year_id)

    def get_timetable(self, id_: uuid.UUID) -> GeneratedTimetable:
        obj = self.repo.get(id_)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated timetable not found")
        return obj

    def get_entries(
        self,
        id_: uuid.UUID,
        division_id: uuid.UUID | None = None,
        faculty_id: uuid.UUID | None = None,
        room_id: uuid.UUID | None = None,
        room_type: RoomType | None = None,
    ) -> list[TimetableEntry]:
        self.get_timetable(id_)  # 404s if missing
        if division_id is not None and self.division_repo.get(division_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")
        if faculty_id is not None and self.faculty_repo.get(faculty_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
        if room_id is not None and self.room_repo.get(room_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        return self.repo.get_entries(
            id_, division_id=division_id, faculty_id=faculty_id, room_id=room_id, room_type=room_type
        )

    def delete_timetable(self, id_: uuid.UUID) -> None:
        obj = self.get_timetable(id_)
        self.repo.delete(obj)
