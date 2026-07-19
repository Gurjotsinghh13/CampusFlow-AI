import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.room import RoomType
from app.models.timetable import GeneratedTimetable, TimetableEntry
from app.repositories.division import DivisionRepository
from app.repositories.faculty import FacultyRepository
from app.repositories.room import RoomRepository
from app.repositories.timetable import GeneratedTimetableRepository
from app.services.solver.solver_service import TimetableSolverService


class GeneratedTimetableService:
    def __init__(self, db: Session):
        self.repo = GeneratedTimetableRepository(db)
        self.division_repo = DivisionRepository(db)
        self.faculty_repo = FacultyRepository(db)
        self.room_repo = RoomRepository(db)
        self.solver_service = TimetableSolverService(db)

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
