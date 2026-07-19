import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.repositories.department import DepartmentRepository
from app.repositories.semester import SemesterRepository
from app.repositories.subject import SubjectRepository
from app.schemas.subject import SubjectCreate, SubjectUpdate
from app.services.timetable_references import (
    ensure_subject_not_used_by_timetables,
    ensure_used_entity_field_not_changed,
    subject_is_used_by_timetables,
)


class SubjectService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SubjectRepository(db)
        self.semester_repo = SemesterRepository(db)
        self.department_repo = DepartmentRepository(db)

    def _ensure_semester_exists(self, semester_id: uuid.UUID) -> None:
        if self.semester_repo.get(semester_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found")

    def _ensure_department_exists(self, department_id: uuid.UUID) -> None:
        if self.department_repo.get(department_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    @staticmethod
    def _ensure_has_teaching_hours(theory_hours: int, practical_hours: int) -> None:
        if theory_hours + practical_hours <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A subject must have at least one theory or practical hour per week",
            )

    @staticmethod
    def _ensure_assigned_faculty_belong_to_department(subject: Subject, department_id: uuid.UUID) -> None:
        mismatched = [
            faculty.employee_id for faculty in subject.faculty_members if faculty.department_id != department_id
        ]
        if mismatched:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Subject cannot move to this department while assigned faculty belong to another department: "
                    + ", ".join(sorted(mismatched))
                ),
            )

    def list_subjects(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
        semester_id: uuid.UUID | None = None,
        department_id: uuid.UUID | None = None,
    ):
        return self.repo.list(
            page=page, page_size=page_size, search=search, semester_id=semester_id, department_id=department_id
        )

    def get_subject(self, id_: uuid.UUID) -> Subject:
        obj = self.repo.get(id_)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        return obj

    def create_subject(self, payload: SubjectCreate) -> Subject:
        self._ensure_semester_exists(payload.semester_id)
        self._ensure_department_exists(payload.department_id)
        if self.repo.get_by_code(payload.code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Subject code '{payload.code}' already exists"
            )
        return self.repo.create(payload.model_dump())

    def update_subject(self, id_: uuid.UUID, payload: SubjectUpdate) -> Subject:
        obj = self.get_subject(id_)
        changes = payload.model_dump(exclude_unset=True)
        target_theory_hours = changes.get("theory_hours_per_week", obj.theory_hours_per_week)
        target_practical_hours = changes.get("practical_hours_per_week", obj.practical_hours_per_week)
        self._ensure_has_teaching_hours(target_theory_hours, target_practical_hours)
        changed_values = {field: value for field, value in changes.items() if getattr(obj, field) != value}
        ensure_used_entity_field_not_changed(
            entity_label="Subject",
            is_used=subject_is_used_by_timetables(self.db, id_),
            changes=changed_values,
            protected_fields={"semester_id", "department_id", "theory_hours_per_week", "practical_hours_per_week"},
        )
        if payload.semester_id:
            self._ensure_semester_exists(payload.semester_id)
        if payload.department_id:
            self._ensure_department_exists(payload.department_id)
            self._ensure_assigned_faculty_belong_to_department(obj, payload.department_id)
        existing = self.repo.get_by_code(payload.code) if payload.code else None
        if existing and existing.id != obj.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Subject code '{payload.code}' already exists"
            )
        return self.repo.update(obj, changes)

    def delete_subject(self, id_: uuid.UUID) -> None:
        obj = self.get_subject(id_)
        ensure_subject_not_used_by_timetables(self.db, id_)
        self.repo.delete(obj)
