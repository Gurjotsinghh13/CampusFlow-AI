from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.room import Room, RoomType
from app.repositories.base import BaseRepository


class RoomRepository(BaseRepository[Room]):
    def __init__(self, db: Session):
        super().__init__(Room, db)

    def get_by_room_number(self, room_number: str) -> Room | None:
        normalized = room_number.strip().lower()
        return self.db.query(Room).filter(func.lower(func.btrim(Room.room_number)) == normalized).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        room_type: RoomType | None = None,
        **_,
    ):
        stmt = select(Room)
        if search:
            stmt = stmt.where(Room.room_number.ilike(f"%{search}%"))
        if room_type is not None:
            stmt = stmt.where(Room.room_type == room_type)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(Room.room_number, Room.id).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.scalars(stmt).all())
        return items, total
