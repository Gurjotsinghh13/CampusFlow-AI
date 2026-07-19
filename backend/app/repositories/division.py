import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.division import Division
from app.repositories.base import BaseRepository


class DivisionRepository(BaseRepository[Division]):
    def __init__(self, db: Session):
        super().__init__(Division, db)

    def get_by_department_semester_and_name(
        self, department_id: uuid.UUID, semester_id: uuid.UUID, name: str
    ) -> Division | None:
        normalized = name.strip().lower()
        return (
            self.db.query(Division)
            .filter(
                Division.department_id == department_id,
                Division.semester_id == semester_id,
                func.lower(func.btrim(Division.name)) == normalized,
            )
            .first()
        )

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        department_id: uuid.UUID | None = None,
        semester_id: uuid.UUID | None = None,
        **_,
    ):
        stmt = select(Division)
        if search:
            stmt = stmt.where(Division.name.ilike(f"%{search}%"))
        if department_id is not None:
            stmt = stmt.where(Division.department_id == department_id)
        if semester_id is not None:
            stmt = stmt.where(Division.semester_id == semester_id)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(Division.name, Division.id).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.scalars(stmt).all())
        return items, total
