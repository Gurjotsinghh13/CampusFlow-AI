import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.room import RoomType
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.timetable import GenerateTimetableRequest, GeneratedTimetableRead, TimetableEntryRead
from app.services.export.export_service import ExportService
from app.services.timetable import GeneratedTimetableService

router = APIRouter(prefix="/timetables", tags=["Generated Timetables"], dependencies=[Depends(get_current_admin)])


def _validate_single_view_filter(
    division_id: uuid.UUID | None,
    faculty_id: uuid.UUID | None,
    room_id: uuid.UUID | None,
    room_type: RoomType | None,
) -> None:
    selected = [division_id is not None, faculty_id is not None, room_id is not None, room_type is not None]
    if sum(selected) > 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Use only one timetable view filter: division_id, faculty_id, room_id, or room_type",
        )


@router.post("/generate", response_model=APIResponse[GeneratedTimetableRead], status_code=201)
def generate_timetable(payload: GenerateTimetableRequest, db: Session = Depends(get_db)):
    obj = GeneratedTimetableService(db).generate(payload.academic_year_id)
    message = "Timetable generated" if obj.status.value == "SUCCESS" else obj.message
    return APIResponse(message=message, data=GeneratedTimetableRead.model_validate(obj))


@router.get("", response_model=APIResponse[PaginatedResponse[GeneratedTimetableRead]])
def list_timetables(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    academic_year_id: uuid.UUID | None = Query(None),
    db: Session = Depends(get_db),
):
    items, total = GeneratedTimetableService(db).list_timetables(page, page_size, academic_year_id)
    return APIResponse(
        data=PaginatedResponse(
            items=[GeneratedTimetableRead.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )
    )


@router.get("/{timetable_id}", response_model=APIResponse[GeneratedTimetableRead])
def get_timetable(timetable_id: uuid.UUID, db: Session = Depends(get_db)):
    obj = GeneratedTimetableService(db).get_timetable(timetable_id)
    return APIResponse(data=GeneratedTimetableRead.model_validate(obj))


@router.get("/{timetable_id}/entries", response_model=APIResponse[list[TimetableEntryRead]])
def get_timetable_entries(
    timetable_id: uuid.UUID,
    division_id: uuid.UUID | None = Query(None, description="Student Timetable view"),
    faculty_id: uuid.UUID | None = Query(None, description="Faculty Timetable view"),
    room_id: uuid.UUID | None = Query(None, description="Single room view"),
    room_type: RoomType | None = Query(None, description="CLASSROOM = Classroom Timetable, LAB = Laboratory Timetable"),
    db: Session = Depends(get_db),
):
    _validate_single_view_filter(division_id, faculty_id, room_id, room_type)
    entries = GeneratedTimetableService(db).get_entries(
        timetable_id, division_id=division_id, faculty_id=faculty_id, room_id=room_id, room_type=room_type
    )
    return APIResponse(data=[TimetableEntryRead.model_validate(e) for e in entries])


@router.get("/{timetable_id}/export/pdf")
def export_timetable_pdf(
    timetable_id: uuid.UUID,
    division_id: uuid.UUID | None = Query(None),
    faculty_id: uuid.UUID | None = Query(None),
    room_id: uuid.UUID | None = Query(None),
    room_type: RoomType | None = Query(None),
    db: Session = Depends(get_db),
):
    _validate_single_view_filter(division_id, faculty_id, room_id, room_type)
    pdf_bytes = ExportService(db).export_pdf(
        timetable_id, division_id=division_id, faculty_id=faculty_id, room_id=room_id, room_type=room_type
    )
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="timetable-{timetable_id}.pdf"'},
    )


@router.get("/{timetable_id}/export/excel")
def export_timetable_excel(
    timetable_id: uuid.UUID,
    division_id: uuid.UUID | None = Query(None),
    faculty_id: uuid.UUID | None = Query(None),
    room_id: uuid.UUID | None = Query(None),
    room_type: RoomType | None = Query(None),
    db: Session = Depends(get_db),
):
    _validate_single_view_filter(division_id, faculty_id, room_id, room_type)
    excel_bytes = ExportService(db).export_excel(
        timetable_id, division_id=division_id, faculty_id=faculty_id, room_id=room_id, room_type=room_type
    )
    return StreamingResponse(
        iter([excel_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="timetable-{timetable_id}.xlsx"'},
    )


@router.delete("/{timetable_id}", response_model=APIResponse[None])
def delete_timetable(timetable_id: uuid.UUID, db: Session = Depends(get_db)):
    GeneratedTimetableService(db).delete_timetable(timetable_id)
    return APIResponse(message="Generated timetable deleted")
