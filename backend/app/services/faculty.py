import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.faculty import Faculty
from app.models.subject import Subject
from app.repositories.department import DepartmentRepository
from app.repositories.faculty import FacultyRepository
from app.schemas.faculty import FacultyCreate, FacultyUpdate
from app.services.timetable_references import (
    ensure_faculty_not_used_by_timetables,
    ensure_used_entity_field_not_changed,
    faculty_is_used_by_timetables,
)


class FacultyService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FacultyRepository(db)
        self.department_repo = DepartmentRepository(db)

    def _ensure_department_exists(self, department_id: uuid.UUID) -> None:
        if self.department_repo.get(department_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    def _resolve_subjects(self, subject_ids: list[uuid.UUID]) -> list[Subject]:
        subjects = self.repo.get_subjects_by_ids(subject_ids)
        found_ids = {s.id for s in subjects}
        missing = set(subject_ids) - found_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject(s) not found: {', '.join(str(m) for m in missing)}",
            )
        return subjects

    @staticmethod
    def _ensure_subjects_belong_to_department(subjects: list[Subject], department_id: uuid.UUID) -> None:
        mismatched = [subject.code for subject in subjects if subject.department_id != department_id]
        if mismatched:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Subject(s) do not belong to the faculty department: {', '.join(sorted(mismatched))}",
            )

    @staticmethod
    def _prune_subjects_outside_department(obj: Faculty, department_id: uuid.UUID) -> None:
        obj.subjects = [subject for subject in obj.subjects if subject.department_id == department_id]

    def list_faculty(self, page: int, page_size: int, search: str | None, department_id: uuid.UUID | None):
        return self.repo.list(page=page, page_size=page_size, search=search, department_id=department_id)

    def get_faculty(self, id_: uuid.UUID) -> Faculty:
        obj = self.repo.get(id_)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
        return obj

    def create_faculty(self, payload: FacultyCreate) -> Faculty:
        self._ensure_department_exists(payload.department_id)
        if self.repo.get_by_employee_id(payload.employee_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee ID '{payload.employee_id}' already exists",
            )
        subjects = self._resolve_subjects(payload.subject_ids)
        self._ensure_subjects_belong_to_department(subjects, payload.department_id)
        fields = payload.model_dump(exclude={"subject_ids"})
        return self.repo.create_with_subjects(fields, subjects)

    def update_faculty(self, id_: uuid.UUID, payload: FacultyUpdate) -> Faculty:
        obj = self.get_faculty(id_)
        changes = payload.model_dump(exclude_unset=True)
        changed_values = {field: value for field, value in changes.items() if getattr(obj, field) != value}
        ensure_used_entity_field_not_changed(
            entity_label="Faculty member",
            is_used=faculty_is_used_by_timetables(self.db, id_),
            changes=changed_values,
            protected_fields={"department_id"},
        )
        if payload.department_id:
            self._ensure_department_exists(payload.department_id)
            if payload.department_id != obj.department_id:
                self._prune_subjects_outside_department(obj, payload.department_id)
            else:
                self._ensure_subjects_belong_to_department(obj.subjects, payload.department_id)
        existing = self.repo.get_by_employee_id(payload.employee_id) if payload.employee_id else None
        if existing and existing.id != obj.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee ID '{payload.employee_id}' already exists",
            )
        return self.repo.update(obj, changes)

    def assign_subjects(self, id_: uuid.UUID, subject_ids: list[uuid.UUID]) -> Faculty:
        obj = self.get_faculty(id_)
        subjects = self._resolve_subjects(subject_ids)
        self._ensure_subjects_belong_to_department(subjects, obj.department_id)
        return self.repo.set_subjects(obj, subjects)

    def delete_faculty(self, id_: uuid.UUID) -> None:
        obj = self.get_faculty(id_)
        ensure_faculty_not_used_by_timetables(self.db, id_)
        self.repo.delete(obj)
