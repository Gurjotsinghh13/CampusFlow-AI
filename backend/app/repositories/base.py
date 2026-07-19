import uuid
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id_: uuid.UUID) -> ModelType | None:
        return self.db.get(self.model, id_)

    def list_by_search(
        self, page: int = 1, page_size: int = 20, search: str | None = None, search_field: str | None = None
    ):
        stmt = select(self.model)
        if search and search_field is not None:
            column = getattr(self.model, search_field)
            stmt = stmt.where(column.ilike(f"%{search}%"))

        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        if search_field is not None:
            stmt = stmt.order_by(getattr(self.model, search_field), self.model.id)
        else:
            stmt = stmt.order_by(self.model.id)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.scalars(stmt).all())
        return items, total

    def create(self, obj_in: dict) -> ModelType:
        obj = self.model(**obj_in)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: ModelType) -> None:
        self.db.delete(db_obj)
        self.db.commit()
