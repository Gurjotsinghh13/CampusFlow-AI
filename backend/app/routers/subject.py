import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.subject import SubjectCreate, SubjectRead, SubjectUpdate
from app.services.subject import SubjectService

router = APIRouter(prefix="/subjects", tags=["Subjects"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=APIResponse[PaginatedResponse[SubjectRead]])
def list_subjects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    semester_id: uuid.UUID | None = Query(None),
    department_id: uuid.UUID | None = Query(None),
    db: Session = Depends(get_db),
):
    items, total = SubjectService(db).list_subjects(page, page_size, search, semester_id, department_id)
    return APIResponse(
        data=PaginatedResponse(
            items=[SubjectRead.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )
    )


@router.get("/{subject_id}", response_model=APIResponse[SubjectRead])
def get_subject(subject_id: uuid.UUID, db: Session = Depends(get_db)):
    obj = SubjectService(db).get_subject(subject_id)
    return APIResponse(data=SubjectRead.model_validate(obj))


@router.post("", response_model=APIResponse[SubjectRead], status_code=201)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db)):
    obj = SubjectService(db).create_subject(payload)
    return APIResponse(message="Subject created", data=SubjectRead.model_validate(obj))


@router.put("/{subject_id}", response_model=APIResponse[SubjectRead])
def update_subject(subject_id: uuid.UUID, payload: SubjectUpdate, db: Session = Depends(get_db)):
    obj = SubjectService(db).update_subject(subject_id, payload)
    return APIResponse(message="Subject updated", data=SubjectRead.model_validate(obj))


@router.delete("/{subject_id}", response_model=APIResponse[None])
def delete_subject(subject_id: uuid.UUID, db: Session = Depends(get_db)):
    SubjectService(db).delete_subject(subject_id)
    return APIResponse(message="Subject deleted")
