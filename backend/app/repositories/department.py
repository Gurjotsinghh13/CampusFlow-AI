from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, db: Session):
        super().__init__(Department, db)

    def get_by_code(self, code: str) -> Department | None:
        normalized = code.strip().lower()
        return self.db.query(Department).filter(func.lower(func.btrim(Department.code)) == normalized).first()

    def get_by_name(self, name: str) -> Department | None:
        normalized = name.strip().lower()
        return self.db.query(Department).filter(func.lower(func.btrim(Department.name)) == normalized).first()

    def list(self, page: int = 1, page_size: int = 20, search: str | None = None, **_):
        stmt = select(Department)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Department.name.ilike(pattern), Department.code.ilike(pattern)))
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(Department.name, Department.id).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.scalars(stmt).all())
        return items, total
