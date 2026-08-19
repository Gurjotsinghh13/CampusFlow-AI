from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.room import RoomType
from app.models.timetable import TimetableEntry
from app.repositories.constraint import ConstraintRepository
from app.repositories.division import DivisionRepository
from app.repositories.faculty import FacultyRepository
from app.repositories.room import RoomRepository
from app.repositories.timetable import GeneratedTimetableRepository
from app.services.export.excel_export import build_excel
from app.services.export.grid_builder import ViewType, build_grid
from app.services.export.pdf_export import build_pdf
from app.utils.timeline import get_period_schedule_from_timetable_record


class ExportService:
    def __init__(self, db: Session):
        self.db = db
        self.timetable_repo = GeneratedTimetableRepository(db)
        self.division_repo = DivisionRepository(db)
        self.faculty_repo = FacultyRepository(db)
        self.room_repo = RoomRepository(db)
        self.constraint_repo = ConstraintRepository(db)

    def _resolve_view(
        self,
        division_id: uuid.UUID | None,
        faculty_id: uuid.UUID | None,
        room_id: uuid.UUID | None,
        room_type: RoomType | None,
        entries: list[TimetableEntry],
    ) -> tuple[ViewType, str]:
        if division_id is not None:
            if entries:
                return ViewType.STUDENT, f"Student Timetable - Division {entries[0].division_name}"
            division = self.division_repo.get(division_id)
            if division is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")
            return ViewType.STUDENT, f"Student Timetable - Division {division.name}"
        if faculty_id is not None:
            if entries:
                return ViewType.FACULTY, f"Faculty Timetable - {entries[0].faculty_name}"
            faculty = self.faculty_repo.get(faculty_id)
            if faculty is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
            return ViewType.FACULTY, f"Faculty Timetable - {faculty.full_name}"
        if room_id is not None:
            if entries:
                return ViewType.ROOM, f"Room Timetable - {entries[0].room_number}"
            room = self.room_repo.get(room_id)
            if room is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
            return ViewType.ROOM, f"Room Timetable - {room.room_number}"
        if room_type == RoomType.LAB:
            return ViewType.ROOM, "Laboratory Timetable"
        if room_type == RoomType.CLASSROOM:
            return ViewType.ROOM, "Classroom Timetable"
        return ViewType.ROOM, "Complete Timetable"

    def _build_grid_and_title(
        self,
        timetable_id: uuid.UUID,
        division_id: uuid.UUID | None,
        faculty_id: uuid.UUID | None,
        room_id: uuid.UUID | None,
        room_type: RoomType | None,
    ):
        run = self.timetable_repo.get(timetable_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated timetable not found")

        constraint = self.constraint_repo.get_singleton()
        period_slots = get_period_schedule_from_timetable_record(run, constraint)

        entries = self.timetable_repo.get_entries(
            timetable_id, division_id=division_id, faculty_id=faculty_id, room_id=room_id, room_type=room_type
        )
        view_type, title = self._resolve_view(division_id, faculty_id, room_id, room_type, entries)
        practical_block_periods = max(1, math.ceil(run.practical_duration_minutes / run.theory_duration_minutes))

        grid = build_grid(
            entries,
            days=list(run.working_days),
            periods_per_day=run.periods_per_day,
            view_type=view_type,
            practical_block_periods=practical_block_periods,
            period_slots=period_slots,
            include_room_in_room_view=view_type == ViewType.ROOM and room_id is None,
        )
        return title, list(run.working_days), run.periods_per_day, period_slots, grid

    def export_pdf(
        self,
        timetable_id: uuid.UUID,
        division_id: uuid.UUID | None = None,
        faculty_id: uuid.UUID | None = None,
        room_id: uuid.UUID | None = None,
        room_type: RoomType | None = None,
    ) -> bytes:
        title, days, periods, period_slots, grid = self._build_grid_and_title(
            timetable_id, division_id, faculty_id, room_id, room_type
        )
        return build_pdf(title, days, periods, period_slots, grid)

    def export_excel(
        self,
        timetable_id: uuid.UUID,
        division_id: uuid.UUID | None = None,
        faculty_id: uuid.UUID | None = None,
        room_id: uuid.UUID | None = None,
        room_type: RoomType | None = None,
    ) -> bytes:
        title, days, periods, period_slots, grid = self._build_grid_and_title(
            timetable_id, division_id, faculty_id, room_id, room_type
        )
        return build_excel(title, days, periods, period_slots, grid)
