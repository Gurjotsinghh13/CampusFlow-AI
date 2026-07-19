import uuid
from datetime import datetime

from pydantic import ConfigDict, Field

from app.models.room import RoomType
from app.schemas.common import NonEmptyUpdateModel, StrippedModel


class RoomBase(StrippedModel):
    room_number: str = Field(min_length=1, max_length=20)
    capacity: int = Field(ge=1, le=1000)
    room_type: RoomType


class RoomCreate(RoomBase):
    pass


class RoomUpdate(NonEmptyUpdateModel):
    room_number: str | None = Field(default=None, min_length=1, max_length=20)
    capacity: int | None = Field(default=None, ge=1, le=1000)
    room_type: RoomType | None = None


class RoomRead(RoomBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
