import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.department import Department
from app.repositories.department import DepartmentRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services.timetable_references import ensure_department_not_used_by_timetables


class DepartmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DepartmentRepository(db)

    def list_departments(self, page: int, page_size: int, search: str | None):
        return self.repo.list(page=page, page_size=page_size, search=search)

    def get_department(self, id_: uuid.UUID) -> Department:
        obj = self.repo.get(id_)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
        return obj

    def create_department(self, payload: DepartmentCreate) -> Department:
        if self.repo.get_by_code(payload.code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Department code '{payload.code}' already exists"
            )
        if self.repo.get_by_name(payload.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Department name '{payload.name}' already exists"
            )
        return self.repo.create(payload.model_dump())

    def update_department(self, id_: uuid.UUID, payload: DepartmentUpdate) -> Department:
        obj = self.get_department(id_)
        existing_code = self.repo.get_by_code(payload.code) if payload.code else None
        if existing_code and existing_code.id != obj.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Department code '{payload.code}' already exists"
            )
        existing_name = self.repo.get_by_name(payload.name) if payload.name else None
        if existing_name and existing_name.id != obj.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Department name '{payload.name}' already exists"
            )
        return self.repo.update(obj, payload.model_dump(exclude_unset=True))

    def delete_department(self, id_: uuid.UUID) -> None:
        obj = self.get_department(id_)
        ensure_department_not_used_by_timetables(self.db, id_)
        self.repo.delete(obj)
