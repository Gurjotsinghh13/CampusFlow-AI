from sqlalchemy.orm import Session

from app.models.constraint import Constraint
from app.repositories.base import BaseRepository


class ConstraintRepository(BaseRepository[Constraint]):
    def __init__(self, db: Session):
        super().__init__(Constraint, db)

    def get_singleton(self) -> Constraint | None:
        return self.db.query(Constraint).order_by(Constraint.created_at.desc()).first()

    def count(self) -> int:
        return self.db.query(Constraint).count()
