from __future__ import annotations

import enum

from sqlalchemy import CheckConstraint, Enum, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class RoomType(str, enum.Enum):
    CLASSROOM = "CLASSROOM"
    LAB = "LAB"


class Room(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "rooms"
    __table_args__ = (
        Index("uq_rooms_room_number_lower", text("lower(btrim(room_number))"), unique=True),
        CheckConstraint("capacity BETWEEN 1 AND 1000", name="ck_rooms_capacity_range"),
    )

    room_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    room_type: Mapped[RoomType] = mapped_column(Enum(RoomType, name="room_type_enum"), nullable=False)

    def __repr__(self) -> str:
        return f"<Room {self.room_number}>"
