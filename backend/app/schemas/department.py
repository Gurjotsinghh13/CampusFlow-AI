import uuid
from datetime import datetime

from pydantic import ConfigDict, Field

from app.schemas.common import NonEmptyUpdateModel, StrippedModel


class DepartmentBase(StrippedModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=2, max_length=20)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(NonEmptyUpdateModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    code: str | None = Field(default=None, min_length=2, max_length=20)


class DepartmentRead(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
