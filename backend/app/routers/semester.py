import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.semester import SemesterCreate, SemesterRead, SemesterUpdate
from app.services.semester import SemesterService

router = APIRouter(prefix="/semesters", tags=["Semesters"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=APIResponse[PaginatedResponse[SemesterRead]])
def list_semesters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    academic_year_id: uuid.UUID | None = Query(None),
    db: Session = Depends(get_db),
):
    items, total = SemesterService(db).list_semesters(page, page_size, academic_year_id)
    return APIResponse(
        data=PaginatedResponse(
            items=[SemesterRead.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )
    )


@router.get("/{semester_id}", response_model=APIResponse[SemesterRead])
def get_semester(semester_id: uuid.UUID, db: Session = Depends(get_db)):
    obj = SemesterService(db).get_semester(semester_id)
    return APIResponse(data=SemesterRead.model_validate(obj))


@router.post("", response_model=APIResponse[SemesterRead], status_code=201)
def create_semester(payload: SemesterCreate, db: Session = Depends(get_db)):
    obj = SemesterService(db).create_semester(payload)
    return APIResponse(message="Semester created", data=SemesterRead.model_validate(obj))


@router.put("/{semester_id}", response_model=APIResponse[SemesterRead])
def update_semester(semester_id: uuid.UUID, payload: SemesterUpdate, db: Session = Depends(get_db)):
    obj = SemesterService(db).update_semester(semester_id, payload)
    return APIResponse(message="Semester updated", data=SemesterRead.model_validate(obj))


@router.delete("/{semester_id}", response_model=APIResponse[None])
def delete_semester(semester_id: uuid.UUID, db: Session = Depends(get_db)):
    SemesterService(db).delete_semester(semester_id)
    return APIResponse(message="Semester deleted")
