import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.room import RoomType
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.room import RoomCreate, RoomRead, RoomUpdate
from app.services.room import RoomService

router = APIRouter(prefix="/rooms", tags=["Rooms & Laboratories"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=APIResponse[PaginatedResponse[RoomRead]])
def list_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    room_type: RoomType | None = Query(None, description="Filter: CLASSROOM for Rooms page, LAB for Labs page"),
    db: Session = Depends(get_db),
):
    items, total = RoomService(db).list_rooms(page, page_size, search, room_type)
    return APIResponse(
        data=PaginatedResponse(
            items=[RoomRead.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )
    )


@router.get("/{room_id}", response_model=APIResponse[RoomRead])
def get_room(room_id: uuid.UUID, db: Session = Depends(get_db)):
    obj = RoomService(db).get_room(room_id)
    return APIResponse(data=RoomRead.model_validate(obj))


@router.post("", response_model=APIResponse[RoomRead], status_code=201)
def create_room(payload: RoomCreate, db: Session = Depends(get_db)):
    obj = RoomService(db).create_room(payload)
    return APIResponse(message="Room created", data=RoomRead.model_validate(obj))


@router.put("/{room_id}", response_model=APIResponse[RoomRead])
def update_room(room_id: uuid.UUID, payload: RoomUpdate, db: Session = Depends(get_db)):
    obj = RoomService(db).update_room(room_id, payload)
    return APIResponse(message="Room updated", data=RoomRead.model_validate(obj))


@router.delete("/{room_id}", response_model=APIResponse[None])
def delete_room(room_id: uuid.UUID, db: Session = Depends(get_db)):
    RoomService(db).delete_room(room_id)
    return APIResponse(message="Room deleted")
