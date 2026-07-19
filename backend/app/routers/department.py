import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.services.department import DepartmentService

router = APIRouter(prefix="/departments", tags=["Departments"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=APIResponse[PaginatedResponse[DepartmentRead]])
def list_departments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
):
    items, total = DepartmentService(db).list_departments(page, page_size, search)
    return APIResponse(
        data=PaginatedResponse(
            items=[DepartmentRead.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )
    )


@router.get("/{department_id}", response_model=APIResponse[DepartmentRead])
def get_department(department_id: uuid.UUID, db: Session = Depends(get_db)):
    obj = DepartmentService(db).get_department(department_id)
    return APIResponse(data=DepartmentRead.model_validate(obj))


@router.post("", response_model=APIResponse[DepartmentRead], status_code=201)
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    obj = DepartmentService(db).create_department(payload)
    return APIResponse(message="Department created", data=DepartmentRead.model_validate(obj))


@router.put("/{department_id}", response_model=APIResponse[DepartmentRead])
def update_department(department_id: uuid.UUID, payload: DepartmentUpdate, db: Session = Depends(get_db)):
    obj = DepartmentService(db).update_department(department_id, payload)
    return APIResponse(message="Department updated", data=DepartmentRead.model_validate(obj))


@router.delete("/{department_id}", response_model=APIResponse[None])
def delete_department(department_id: uuid.UUID, db: Session = Depends(get_db)):
    DepartmentService(db).delete_department(department_id)
    return APIResponse(message="Department deleted")
