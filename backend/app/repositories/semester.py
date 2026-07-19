import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.semester import Semester
from app.repositories.base import BaseRepository


class SemesterRepository(BaseRepository[Semester]):
    def __init__(self, db: Session):
        super().__init__(Semester, db)

    def get_by_year_and_number(self, academic_year_id: uuid.UUID, number: int) -> Semester | None:
        return (
            self.db.query(Semester)
            .filter(Semester.academic_year_id == academic_year_id, Semester.number == number)
            .first()
        )

    def list(self, page: int = 1, page_size: int = 20, academic_year_id: uuid.UUID | None = None, **_):
        stmt = select(Semester)
        if academic_year_id is not None:
            stmt = stmt.where(Semester.academic_year_id == academic_year_id)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(Semester.number, Semester.id).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.scalars(stmt).all())
        return items, total
