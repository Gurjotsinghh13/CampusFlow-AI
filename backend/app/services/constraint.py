from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.constraint import Constraint
from app.repositories.constraint import ConstraintRepository
from app.schemas.constraint import ConstraintBase, ConstraintCreate, ConstraintUpdate


class ConstraintService:
    def __init__(self, db: Session):
        self.repo = ConstraintRepository(db)

    def _ensure_singleton_not_duplicated(self) -> None:
        if self.repo.count() > 1:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Multiple scheduling constraint rows exist; clean up duplicate configuration rows",
            )

    def get_constraints(self) -> Constraint:
        self._ensure_singleton_not_duplicated()
        obj = self.repo.get_singleton()
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduling constraints have not been configured yet",
            )
        return obj

    def save_constraints(self, payload: ConstraintCreate) -> Constraint:
        self._ensure_singleton_not_duplicated()
        existing = self.repo.get_singleton()
        if existing is None:
            return self.repo.create(payload.model_dump())
        return self.repo.update(existing, payload.model_dump())

    def patch_constraints(self, payload: ConstraintUpdate) -> Constraint:
        existing = self.get_constraints()
        update_data = payload.model_dump(exclude_unset=True)
        merged = {
            "working_days": existing.working_days,
            "college_start_time": existing.college_start_time,
            "college_end_time": existing.college_end_time,
            "lunch_break_start": existing.lunch_break_start,
            "lunch_break_end": existing.lunch_break_end,
            "number_of_periods": existing.number_of_periods,
            "theory_duration_minutes": existing.theory_duration_minutes,
            "practical_duration_minutes": existing.practical_duration_minutes,
            **update_data,
        }
        try:
            ConstraintBase.model_validate(merged)
        except ValidationError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        return self.repo.update(existing, update_data)
