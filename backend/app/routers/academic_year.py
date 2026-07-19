import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.schemas.academic_year import AcademicYearCreate, AcademicYearRead, AcademicYearUpdate
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.academic_year import AcademicYearService

router = APIRouter(prefix="/academic-years", tags=["Academic Years"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=APIResponse[PaginatedResponse[AcademicYearRead]])
def list_academic_years(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
):
    items, total = AcademicYearService(db).list_academic_years(page, page_size, search)
    return APIResponse(
        data=PaginatedResponse(
            items=[AcademicYearRead.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )
    )


@router.get("/{academic_year_id}", response_model=APIResponse[AcademicYearRead])
def get_academic_year(academic_year_id: uuid.UUID, db: Session = Depends(get_db)):
    obj = AcademicYearService(db).get_academic_year(academic_year_id)
    return APIResponse(data=AcademicYearRead.model_validate(obj))


@router.post("", response_model=APIResponse[AcademicYearRead], status_code=201)
def create_academic_year(payload: AcademicYearCreate, db: Session = Depends(get_db)):
    obj = AcademicYearService(db).create_academic_year(payload)
    return APIResponse(message="Academic year created", data=AcademicYearRead.model_validate(obj))


@router.put("/{academic_year_id}", response_model=APIResponse[AcademicYearRead])
def update_academic_year(academic_year_id: uuid.UUID, payload: AcademicYearUpdate, db: Session = Depends(get_db)):
    obj = AcademicYearService(db).update_academic_year(academic_year_id, payload)
    return APIResponse(message="Academic year updated", data=AcademicYearRead.model_validate(obj))


@router.delete("/{academic_year_id}", response_model=APIResponse[None])
def delete_academic_year(academic_year_id: uuid.UUID, db: Session = Depends(get_db)):
    AcademicYearService(db).delete_academic_year(academic_year_id)
    return APIResponse(message="Academic year deleted")
