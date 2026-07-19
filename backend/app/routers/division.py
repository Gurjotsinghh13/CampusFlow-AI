import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.division import DivisionCreate, DivisionRead, DivisionUpdate
from app.services.division import DivisionService

router = APIRouter(prefix="/divisions", tags=["Divisions"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=APIResponse[PaginatedResponse[DivisionRead]])
def list_divisions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    department_id: uuid.UUID | None = Query(None),
    semester_id: uuid.UUID | None = Query(None),
    db: Session = Depends(get_db),
):
    items, total = DivisionService(db).list_divisions(page, page_size, search, department_id, semester_id)
    return APIResponse(
        data=PaginatedResponse(
            items=[DivisionRead.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )
    )


@router.get("/{division_id}", response_model=APIResponse[DivisionRead])
def get_division(division_id: uuid.UUID, db: Session = Depends(get_db)):
    obj = DivisionService(db).get_division(division_id)
    return APIResponse(data=DivisionRead.model_validate(obj))


@router.post("", response_model=APIResponse[DivisionRead], status_code=201)
def create_division(payload: DivisionCreate, db: Session = Depends(get_db)):
    obj = DivisionService(db).create_division(payload)
    return APIResponse(message="Division created", data=DivisionRead.model_validate(obj))


@router.put("/{division_id}", response_model=APIResponse[DivisionRead])
def update_division(division_id: uuid.UUID, payload: DivisionUpdate, db: Session = Depends(get_db)):
    obj = DivisionService(db).update_division(division_id, payload)
    return APIResponse(message="Division updated", data=DivisionRead.model_validate(obj))


@router.delete("/{division_id}", response_model=APIResponse[None])
def delete_division(division_id: uuid.UUID, db: Session = Depends(get_db)):
    DivisionService(db).delete_division(division_id)
    return APIResponse(message="Division deleted")
