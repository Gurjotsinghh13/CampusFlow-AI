import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.faculty import FacultyCreate, FacultyRead, FacultySubjectAssignment, FacultyUpdate
from app.services.faculty import FacultyService

router = APIRouter(prefix="/faculty", tags=["Faculty"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=APIResponse[PaginatedResponse[FacultyRead]])
def list_faculty(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    department_id: uuid.UUID | None = Query(None),
    db: Session = Depends(get_db),
):
    items, total = FacultyService(db).list_faculty(page, page_size, search, department_id)
    return APIResponse(
        data=PaginatedResponse(
            items=[FacultyRead.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )
    )


@router.get("/{faculty_id}", response_model=APIResponse[FacultyRead])
def get_faculty(faculty_id: uuid.UUID, db: Session = Depends(get_db)):
    obj = FacultyService(db).get_faculty(faculty_id)
    return APIResponse(data=FacultyRead.model_validate(obj))


@router.post("", response_model=APIResponse[FacultyRead], status_code=201)
def create_faculty(payload: FacultyCreate, db: Session = Depends(get_db)):
    obj = FacultyService(db).create_faculty(payload)
    return APIResponse(message="Faculty created", data=FacultyRead.model_validate(obj))


@router.put("/{faculty_id}", response_model=APIResponse[FacultyRead])
def update_faculty(faculty_id: uuid.UUID, payload: FacultyUpdate, db: Session = Depends(get_db)):
    obj = FacultyService(db).update_faculty(faculty_id, payload)
    return APIResponse(message="Faculty updated", data=FacultyRead.model_validate(obj))


@router.put("/{faculty_id}/subjects", response_model=APIResponse[FacultyRead])
def assign_subjects(faculty_id: uuid.UUID, payload: FacultySubjectAssignment, db: Session = Depends(get_db)):
    obj = FacultyService(db).assign_subjects(faculty_id, payload.subject_ids)
    return APIResponse(message="Subject assignments updated", data=FacultyRead.model_validate(obj))


@router.delete("/{faculty_id}", response_model=APIResponse[None])
def delete_faculty(faculty_id: uuid.UUID, db: Session = Depends(get_db)):
    FacultyService(db).delete_faculty(faculty_id)
    return APIResponse(message="Faculty deleted")
