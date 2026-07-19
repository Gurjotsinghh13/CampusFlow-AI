import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.semester import Semester
from app.repositories.academic_year import AcademicYearRepository
from app.repositories.semester import SemesterRepository
from app.schemas.semester import SemesterCreate, SemesterUpdate
from app.services.timetable_references import (
    ensure_semester_not_used_by_timetables,
    ensure_used_entity_field_not_changed,
    semester_is_used_by_timetables,
)


class SemesterService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SemesterRepository(db)
        self.academic_year_repo = AcademicYearRepository(db)

    def _ensure_academic_year_exists(self, academic_year_id: uuid.UUID) -> None:
        if self.academic_year_repo.get(academic_year_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")

    def list_semesters(self, page: int, page_size: int, academic_year_id: uuid.UUID | None = None):
        return self.repo.list(page=page, page_size=page_size, academic_year_id=academic_year_id)

    def get_semester(self, id_: uuid.UUID) -> Semester:
        obj = self.repo.get(id_)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found")
        return obj

    def create_semester(self, payload: SemesterCreate) -> Semester:
        self._ensure_academic_year_exists(payload.academic_year_id)
        if self.repo.get_by_year_and_number(payload.academic_year_id, payload.number):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Semester {payload.number} already exists for this academic year",
            )
        return self.repo.create(payload.model_dump())

    def update_semester(self, id_: uuid.UUID, payload: SemesterUpdate) -> Semester:
        obj = self.get_semester(id_)
        changes = payload.model_dump(exclude_unset=True)
        changed_values = {field: value for field, value in changes.items() if getattr(obj, field) != value}
        ensure_used_entity_field_not_changed(
            entity_label="Semester",
            is_used=semester_is_used_by_timetables(self.db, id_),
            changes=changed_values,
            protected_fields={"number", "academic_year_id"},
        )
        target_year_id = payload.academic_year_id or obj.academic_year_id
        if payload.academic_year_id:
            self._ensure_academic_year_exists(payload.academic_year_id)
        target_number = payload.number if payload.number is not None else obj.number
        existing = self.repo.get_by_year_and_number(target_year_id, target_number)
        if existing and existing.id != obj.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Semester {target_number} already exists for this academic year",
            )
        return self.repo.update(obj, changes)

    def delete_semester(self, id_: uuid.UUID) -> None:
        obj = self.get_semester(id_)
        ensure_semester_not_used_by_timetables(self.db, id_)
        self.repo.delete(obj)
