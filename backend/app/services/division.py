import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.division import Division
from app.repositories.department import DepartmentRepository
from app.repositories.division import DivisionRepository
from app.repositories.semester import SemesterRepository
from app.schemas.division import DivisionCreate, DivisionUpdate
from app.services.timetable_references import (
    division_is_used_by_timetables,
    ensure_division_not_used_by_timetables,
    ensure_used_entity_field_not_changed,
)


class DivisionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DivisionRepository(db)
        self.department_repo = DepartmentRepository(db)
        self.semester_repo = SemesterRepository(db)

    def _ensure_department_exists(self, department_id: uuid.UUID) -> None:
        if self.department_repo.get(department_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    def _ensure_semester_exists(self, semester_id: uuid.UUID) -> None:
        if self.semester_repo.get(semester_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found")

    def list_divisions(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
        department_id: uuid.UUID | None = None,
        semester_id: uuid.UUID | None = None,
    ):
        return self.repo.list(
            page=page,
            page_size=page_size,
            search=search,
            department_id=department_id,
            semester_id=semester_id,
        )

    def get_division(self, id_: uuid.UUID) -> Division:
        obj = self.repo.get(id_)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")
        return obj

    def create_division(self, payload: DivisionCreate) -> Division:
        self._ensure_department_exists(payload.department_id)
        self._ensure_semester_exists(payload.semester_id)
        if self.repo.get_by_department_semester_and_name(payload.department_id, payload.semester_id, payload.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Division '{payload.name}' already exists for this department and semester",
            )
        return self.repo.create(payload.model_dump())

    def update_division(self, id_: uuid.UUID, payload: DivisionUpdate) -> Division:
        obj = self.get_division(id_)
        changes = payload.model_dump(exclude_unset=True)
        changed_values = {field: value for field, value in changes.items() if getattr(obj, field) != value}
        ensure_used_entity_field_not_changed(
            entity_label="Division",
            is_used=division_is_used_by_timetables(self.db, id_),
            changes=changed_values,
            protected_fields={"department_id", "semester_id", "student_count"},
        )
        if payload.department_id:
            self._ensure_department_exists(payload.department_id)
        if payload.semester_id:
            self._ensure_semester_exists(payload.semester_id)

        target_department_id = payload.department_id or obj.department_id
        target_semester_id = payload.semester_id or obj.semester_id
        target_name = payload.name or obj.name
        existing = self.repo.get_by_department_semester_and_name(target_department_id, target_semester_id, target_name)
        if existing and existing.id != obj.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Division '{target_name}' already exists for this department and semester",
            )
        return self.repo.update(obj, changes)

    def delete_division(self, id_: uuid.UUID) -> None:
        obj = self.get_division(id_)
        ensure_division_not_used_by_timetables(self.db, id_)
        self.repo.delete(obj)
