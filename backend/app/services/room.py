import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.room import Room, RoomType
from app.repositories.room import RoomRepository
from app.schemas.room import RoomCreate, RoomUpdate
from app.services.timetable_references import (
    ensure_room_not_used_by_timetables,
    ensure_used_entity_field_not_changed,
    room_is_used_by_timetables,
)


class RoomService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RoomRepository(db)

    def list_rooms(self, page: int, page_size: int, search: str | None, room_type: RoomType | None):
        return self.repo.list(page=page, page_size=page_size, search=search, room_type=room_type)

    def get_room(self, id_: uuid.UUID) -> Room:
        obj = self.repo.get(id_)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        return obj

    def create_room(self, payload: RoomCreate) -> Room:
        if self.repo.get_by_room_number(payload.room_number):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Room '{payload.room_number}' already exists"
            )
        return self.repo.create(payload.model_dump())

    def update_room(self, id_: uuid.UUID, payload: RoomUpdate) -> Room:
        obj = self.get_room(id_)
        changes = payload.model_dump(exclude_unset=True)
        changed_values = {field: value for field, value in changes.items() if getattr(obj, field) != value}
        ensure_used_entity_field_not_changed(
            entity_label="Room",
            is_used=room_is_used_by_timetables(self.db, id_),
            changes=changed_values,
            protected_fields={"room_type", "capacity"},
        )
        existing = self.repo.get_by_room_number(payload.room_number) if payload.room_number else None
        if existing and existing.id != obj.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Room '{payload.room_number}' already exists"
            )
        return self.repo.update(obj, changes)

    def delete_room(self, id_: uuid.UUID) -> None:
        obj = self.get_room(id_)
        ensure_room_not_used_by_timetables(self.db, id_)
        self.repo.delete(obj)
