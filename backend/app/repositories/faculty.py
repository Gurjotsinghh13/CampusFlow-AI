from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.faculty import Faculty
from app.models.subject import Subject
from app.repositories.base import BaseRepository


class FacultyRepository(BaseRepository[Faculty]):
    def __init__(self, db: Session):
        super().__init__(Faculty, db)

    def get_by_employee_id(self, employee_id: str) -> Faculty | None:
        normalized = employee_id.strip().lower()
        return self.db.query(Faculty).filter(func.lower(func.btrim(Faculty.employee_id)) == normalized).first()

    def get(self, id_: uuid.UUID) -> Faculty | None:
        return self.db.scalars(
            select(Faculty).options(selectinload(Faculty.subjects)).where(Faculty.id == id_)
        ).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        department_id: uuid.UUID | None = None,
        **_,
    ):
        stmt = select(Faculty)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Faculty.full_name.ilike(pattern), Faculty.employee_id.ilike(pattern)))
        if department_id is not None:
            stmt = stmt.where(Faculty.department_id == department_id)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = (
            stmt.options(selectinload(Faculty.subjects))
            .order_by(Faculty.full_name, Faculty.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(stmt).all())
        return items, total

    def get_subjects_by_ids(self, subject_ids: list[uuid.UUID]) -> list[Subject]:
        if not subject_ids:
            return []
        return self.db.query(Subject).filter(Subject.id.in_(subject_ids)).all()

    def create_with_subjects(self, faculty_fields: dict, subjects: list[Subject]) -> Faculty:
        obj = Faculty(**faculty_fields)
        obj.subjects = subjects
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def set_subjects(self, obj: Faculty, subjects: list[Subject]) -> Faculty:
        obj.subjects = subjects
        self.db.commit()
        self.db.refresh(obj)
        return obj
