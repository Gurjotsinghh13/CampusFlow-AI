import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.academic_year import AcademicYear
from app.repositories.academic_year import AcademicYearRepository
from app.schemas.academic_year import AcademicYearCreate, AcademicYearUpdate
from app.services.timetable_references import ensure_academic_year_not_used_by_timetables


class AcademicYearService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AcademicYearRepository(db)

    def list_academic_years(self, page: int, page_size: int, search: str | None):
        return self.repo.list_by_search(page=page, page_size=page_size, search=search, search_field="label")

    def get_academic_year(self, id_: uuid.UUID) -> AcademicYear:
        obj = self.repo.get(id_)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
        return obj

    def create_academic_year(self, payload: AcademicYearCreate) -> AcademicYear:
        if self.repo.get_by_label(payload.label):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Academic year '{payload.label}' already exists"
            )
        if payload.is_active:
            self.repo.deactivate_others(None)
        obj = AcademicYear(**payload.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_academic_year(self, id_: uuid.UUID, payload: AcademicYearUpdate) -> AcademicYear:
        obj = self.get_academic_year(id_)
        existing = self.repo.get_by_label(payload.label) if payload.label else None
        if existing and existing.id != obj.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Academic year '{payload.label}' already exists"
            )
        changes = payload.model_dump(exclude_unset=True)
        if changes.get("is_active") is True:
            self.repo.deactivate_others(obj.id)
        for field, value in changes.items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_academic_year(self, id_: uuid.UUID) -> None:
        obj = self.get_academic_year(id_)
        ensure_academic_year_not_used_by_timetables(self.db, id_)
        self.repo.delete(obj)
