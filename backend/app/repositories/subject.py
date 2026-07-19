import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.repositories.base import BaseRepository


class SubjectRepository(BaseRepository[Subject]):
    def __init__(self, db: Session):
        super().__init__(Subject, db)

    def get_by_code(self, code: str) -> Subject | None:
        normalized = code.strip().lower()
        return self.db.query(Subject).filter(func.lower(func.btrim(Subject.code)) == normalized).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        semester_id: uuid.UUID | None = None,
        department_id: uuid.UUID | None = None,
        **_,
    ):
        stmt = select(Subject)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Subject.name.ilike(pattern), Subject.code.ilike(pattern)))
        if semester_id is not None:
            stmt = stmt.where(Subject.semester_id == semester_id)
        if department_id is not None:
            stmt = stmt.where(Subject.department_id == department_id)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(Subject.name, Subject.id).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.scalars(stmt).all())
        return items, total
