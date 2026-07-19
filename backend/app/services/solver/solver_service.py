import logging
import time
from uuid import UUID

from fastapi import HTTPException, status
from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.academic_year import AcademicYear
from app.models.timetable import GeneratedTimetable, GenerationStatus, TimetableEntry
from app.services.solver.data_loader import SolverValidationError, load_solver_input
from app.services.solver.model_builder import CPSATModelBuilder, ModelTooLargeError

logger = logging.getLogger("campusflow.solver")


class TimetableSolverService:
    def __init__(self, db: Session):
        self.db = db

    def _mark_failed(self, run_id: UUID, message: str, wall_time: float | None = None) -> None:
        self.db.rollback()
        run = self.db.get(GeneratedTimetable, run_id)
        if run is None:
            return
        run.status = GenerationStatus.FAILED
        run.message = message[:500]
        if wall_time is not None:
            run.solver_wall_time_seconds = wall_time
        self.db.commit()

    def generate(self, academic_year_id: UUID) -> GeneratedTimetable:
        academic_year = self.db.get(AcademicYear, academic_year_id)
        if academic_year is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")

        try:
            solver_input = load_solver_input(self.db, academic_year_id)
        except SolverValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "Cannot generate timetable - data is incomplete", "issues": exc.issues},
            ) from exc

        run = GeneratedTimetable(
            academic_year_id=academic_year_id,
            academic_year_label=academic_year.label,
            status=GenerationStatus.RUNNING,
            working_days=solver_input.days,
            periods_per_day=solver_input.periods_per_day,
            theory_duration_minutes=solver_input.theory_duration_minutes,
            practical_duration_minutes=solver_input.practical_duration_minutes,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        try:
            builder = CPSATModelBuilder(solver_input)
            model = builder.build()

            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = settings.SOLVER_MAX_TIME_SECONDS
            solver.parameters.num_search_workers = settings.SOLVER_NUM_WORKERS

            start = time.monotonic()
            status_code = solver.Solve(model)
            wall_time = time.monotonic() - start

            if status_code not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                run.status = GenerationStatus.INFEASIBLE
                run.solver_wall_time_seconds = wall_time
                run.message = (
                    "No conflict-free timetable exists for the current data and constraints. "
                    "Try relaxing faculty workload limits, adding rooms/labs, or reducing weekly hours."
                )
                self.db.commit()
                self.db.refresh(run)
                logger.warning("Timetable generation infeasible for academic_year_id=%s", academic_year_id)
                return run

            requirements_by_key = {r.key: r for r in solver_input.requirements}
            entries = []
            for key, var in builder.assignment_vars.items():
                if solver.Value(var) != 1:
                    continue
                req = requirements_by_key[key.requirement_key]
                division = solver_input.divisions[req.division_id]
                subject = solver_input.subjects[req.subject_id]
                faculty = solver_input.faculty[key.faculty_id]
                room = solver_input.rooms[key.room_id]
                entries.append(
                    TimetableEntry(
                        timetable_id=run.id,
                        division_id=req.division_id,
                        subject_id=req.subject_id,
                        faculty_id=key.faculty_id,
                        room_id=key.room_id,
                        day=solver_input.days[key.day_idx],
                        period_index=key.start_period,
                        session_type=req.session_type.value,
                        division_name=division.name,
                        subject_name=subject.name,
                        subject_code=subject.code,
                        faculty_name=faculty.full_name,
                        room_number=room.room_number,
                    )
                )

            run.status = GenerationStatus.SUCCESS
            run.solver_wall_time_seconds = wall_time
            run.objective_value = solver.ObjectiveValue() if solver_input.requirements else None
            run.message = (
                "Optimal solution found"
                if status_code == cp_model.OPTIMAL
                else "Feasible solution found within time limit"
            )
            self.db.add_all(entries)
            self.db.commit()
            self.db.refresh(run)
        except ModelTooLargeError as exc:
            self._mark_failed(run.id, str(exc))
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception("Timetable generation failed for academic_year_id=%s", academic_year_id)
            self._mark_failed(run.id, "Timetable generation failed unexpectedly")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Timetable generation failed unexpectedly",
            ) from exc

        logger.info(
            "Timetable generated academic_year_id=%s entries=%d wall_time=%.2fs",
            academic_year_id,
            len(entries),
            wall_time,
        )
        return run
