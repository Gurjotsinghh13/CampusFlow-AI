from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.division import Division
    from app.models.faculty import Faculty
    from app.models.subject import Subject


class Department(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (
        Index("uq_departments_code_lower", text("lower(btrim(code))"), unique=True),
        Index("uq_departments_name_lower", text("lower(btrim(name))"), unique=True),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    faculty: Mapped[list["Faculty"]] = relationship(back_populates="department", cascade="all, delete-orphan")
    subjects: Mapped[list["Subject"]] = relationship(back_populates="department", cascade="all, delete-orphan")
    divisions: Mapped[list["Division"]] = relationship(back_populates="department", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Department {self.code}>"
