import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.academic_year import AcademicYear
from app.repositories.base import BaseRepository


class AcademicYearRepository(BaseRepository[AcademicYear]):
    def __init__(self, db: Session):
        super().__init__(AcademicYear, db)

    def get_by_label(self, label: str) -> AcademicYear | None:
        normalized = label.strip().lower()
        return (
            self.db.query(AcademicYear)
            .filter(func.lower(func.btrim(AcademicYear.label)) == normalized)
            .first()
        )

    def deactivate_others(self, active_id: uuid.UUID | None) -> None:
        query = self.db.query(AcademicYear).filter(AcademicYear.is_active.is_(True))
        if active_id is not None:
            query = query.filter(AcademicYear.id != active_id)
        query.update({AcademicYear.is_active: False}, synchronize_session="fetch")
