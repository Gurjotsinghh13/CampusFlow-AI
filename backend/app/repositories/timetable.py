from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.room import RoomType
from app.models.timetable import GeneratedTimetable, TimetableEntry
from app.repositories.base import BaseRepository


class GeneratedTimetableRepository(BaseRepository[GeneratedTimetable]):
    def __init__(self, db: Session):
        super().__init__(GeneratedTimetable, db)

    def list(self, page: int = 1, page_size: int = 20, academic_year_id: uuid.UUID | None = None, **_):
        stmt = select(GeneratedTimetable)
        if academic_year_id is not None:
            stmt = stmt.where(GeneratedTimetable.academic_year_id == academic_year_id)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = (
            stmt.order_by(GeneratedTimetable.created_at.desc(), GeneratedTimetable.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(stmt).all())
        return items, total

    def get_entries(
        self,
        timetable_id: uuid.UUID,
        division_id: uuid.UUID | None = None,
        faculty_id: uuid.UUID | None = None,
        room_id: uuid.UUID | None = None,
        room_type: RoomType | None = None,
    ) -> list[TimetableEntry]:
        stmt = (
            select(TimetableEntry)
            .options(
                joinedload(TimetableEntry.division),
                joinedload(TimetableEntry.subject),
                joinedload(TimetableEntry.faculty),
                joinedload(TimetableEntry.room),
            )
            .where(TimetableEntry.timetable_id == timetable_id)
        )
        if division_id is not None:
            stmt = stmt.where(TimetableEntry.division_id == division_id)
        if faculty_id is not None:
            stmt = stmt.where(TimetableEntry.faculty_id == faculty_id)
        if room_id is not None:
            stmt = stmt.where(TimetableEntry.room_id == room_id)
        if room_type is not None:
            stmt = stmt.where(TimetableEntry.room.has(room_type=room_type))
        stmt = stmt.order_by(TimetableEntry.day, TimetableEntry.period_index, TimetableEntry.id)
        return list(self.db.scalars(stmt).unique().all())
