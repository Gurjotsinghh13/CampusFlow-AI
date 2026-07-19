import math
from dataclasses import replace
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.academic_year import AcademicYear
from app.models.constraint import Constraint
from app.models.division import Division
from app.models.faculty import Faculty
from app.models.room import Room, RoomType
from app.models.semester import Semester
from app.models.subject import Subject
from app.services.solver.data_types import (
    DivisionData,
    FacultyData,
    RoomData,
    SessionRequirement,
    SessionType,
    SolverInput,
    SubjectData,
)


class SolverValidationError(Exception):
    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("; ".join(issues))


def _theory_sessions_count(theory_hours_per_week: int, period_minutes: int) -> int:
    if theory_hours_per_week <= 0:
        return 0
    hours_per_session = period_minutes / 60
    if hours_per_session <= 0:
        return theory_hours_per_week
    return max(1, math.ceil(theory_hours_per_week / hours_per_session))


def _practical_sessions_count(practical_hours_per_week: int, practical_duration_minutes: int) -> int:
    if practical_hours_per_week <= 0:
        return 0
    hours_per_block = practical_duration_minutes / 60
    if hours_per_block <= 0:
        return practical_hours_per_week
    return max(1, math.ceil(practical_hours_per_week / hours_per_block))


def load_solver_input(db: Session, academic_year_id: UUID) -> SolverInput:
    issues: list[str] = []

    academic_year = db.get(AcademicYear, academic_year_id)
    if academic_year is None:
        raise SolverValidationError([f"Academic year {academic_year_id} not found"])

    constraints = db.query(Constraint).order_by(Constraint.created_at.desc()).all()
    if len(constraints) > 1:
        raise SolverValidationError(
            ["Multiple scheduling constraint rows exist; clean up duplicate configuration rows"]
        )
    constraint = constraints[0] if constraints else None
    if constraint is None:
        raise SolverValidationError(["Scheduling constraints have not been configured yet"])

    period_minutes = constraint.theory_duration_minutes
    practical_block_periods = max(1, math.ceil(constraint.practical_duration_minutes / period_minutes))
    if practical_block_periods > constraint.number_of_periods:
        issues.append(
            "Practical session duration is longer than the entire teaching day - "
            "reduce practical_duration_minutes or increase number_of_periods"
        )

    divisions = (
        db.query(Division)
        .join(Semester, Division.semester_id == Semester.id)
        .filter(Semester.academic_year_id == academic_year_id)
        .all()
    )
    if not divisions:
        issues.append("No divisions are configured for this academic year")

    division_data: dict[UUID, DivisionData] = {
        d.id: DivisionData(
            id=d.id,
            name=d.name,
            department_id=d.department_id,
            semester_id=d.semester_id,
            student_count=d.student_count,
        )
        for d in divisions
    }

    all_rooms = db.query(Room).all()
    room_data = {
        r.id: RoomData(id=r.id, room_number=r.room_number, capacity=r.capacity, room_type=r.room_type.value)
        for r in all_rooms
    }
    classroom_ids = tuple(r.id for r in all_rooms if r.room_type == RoomType.CLASSROOM)
    lab_ids = tuple(r.id for r in all_rooms if r.room_type == RoomType.LAB)
    if not classroom_ids:
        issues.append("No classrooms configured - add at least one Room of type CLASSROOM")
    has_practical_subjects = False

    subject_data: dict[UUID, SubjectData] = {}
    all_faculty_ids: set[UUID] = set()
    requirements: list[SessionRequirement] = []

    needed_semester_dept_pairs = {(d.semester_id, d.department_id) for d in division_data.values()}

    for semester_id, department_id in needed_semester_dept_pairs:
        subjects = (
            db.query(Subject)
            .filter(Subject.semester_id == semester_id, Subject.department_id == department_id)
            .all()
        )
        for subj in subjects:
            eligible_faculty = tuple(f.id for f in subj.faculty_members)
            all_faculty_ids.update(eligible_faculty)
            has_practical_subjects = has_practical_subjects or subj.practical_hours_per_week > 0

            subject_data[subj.id] = SubjectData(
                id=subj.id,
                name=subj.name,
                code=subj.code,
                semester_id=subj.semester_id,
                department_id=subj.department_id,
                theory_sessions_per_week=_theory_sessions_count(subj.theory_hours_per_week, period_minutes),
                practical_sessions_per_week=_practical_sessions_count(
                    subj.practical_hours_per_week, constraint.practical_duration_minutes
                ),
                eligible_faculty_ids=eligible_faculty,
            )

            if subj.theory_hours_per_week > 0 and not eligible_faculty:
                issues.append(f"Subject '{subj.code}' has theory hours but no faculty assigned to teach it")
            if subj.practical_hours_per_week > 0 and not eligible_faculty:
                issues.append(f"Subject '{subj.code}' has practical hours but no faculty assigned to teach it")
            if subj.practical_hours_per_week > 0 and not lab_ids:
                issues.append(f"Subject '{subj.code}' requires a laboratory but none is configured")
            if subject_data[subj.id].theory_sessions_per_week > len(constraint.working_days):
                issues.append(
                    f"Subject '{subj.code}' requires {subject_data[subj.id].theory_sessions_per_week} theory "
                    f"sessions per week but only {len(constraint.working_days)} working days are configured"
                )
            if subject_data[subj.id].practical_sessions_per_week > len(constraint.working_days):
                issues.append(
                    f"Subject '{subj.code}' requires {subject_data[subj.id].practical_sessions_per_week} practical "
                    f"sessions per week but only {len(constraint.working_days)} working days are configured"
                )

    if has_practical_subjects and not lab_ids:
        issues.append("No laboratories configured - add at least one Room of type LAB")

    for div in division_data.values():
        division_required_periods = 0
        has_subject_for_division = False
        for subj in subject_data.values():
            if subj.semester_id != div.semester_id or subj.department_id != div.department_id:
                continue

            has_subject_for_division = True
            division_required_periods += subj.theory_sessions_per_week
            division_required_periods += subj.practical_sessions_per_week * practical_block_periods

            eligible_rooms_theory = tuple(
                r.id for r in all_rooms if r.room_type == RoomType.CLASSROOM and r.capacity >= div.student_count
            )
            if subj.theory_sessions_per_week > 0 and not eligible_rooms_theory:
                issues.append(
                    f"No classroom has enough capacity ({div.student_count} students) for division '{div.name}'"
                )
            for i in range(subj.theory_sessions_per_week):
                requirements.append(
                    SessionRequirement(
                        division_id=div.id,
                        subject_id=subj.id,
                        session_type=SessionType.THEORY,
                        session_index=i,
                        duration_periods=1,
                        eligible_faculty_ids=subj.eligible_faculty_ids,
                        eligible_room_ids=eligible_rooms_theory,
                    )
                )

            eligible_rooms_practical = tuple(
                r.id for r in all_rooms if r.room_type == RoomType.LAB and r.capacity >= div.student_count
            )
            if subj.practical_sessions_per_week > 0 and not eligible_rooms_practical:
                issues.append(
                    f"No laboratory has enough capacity ({div.student_count} students) for division '{div.name}'"
                )
            for i in range(subj.practical_sessions_per_week):
                requirements.append(
                    SessionRequirement(
                        division_id=div.id,
                        subject_id=subj.id,
                        session_type=SessionType.PRACTICAL,
                        session_index=i,
                        duration_periods=practical_block_periods,
                        eligible_faculty_ids=subj.eligible_faculty_ids,
                        eligible_room_ids=eligible_rooms_practical,
                    )
                )

        available_slots = len(constraint.working_days) * constraint.number_of_periods
        if not has_subject_for_division:
            issues.append(f"No subjects are configured for division '{div.name}' in its semester and department")
        elif division_required_periods == 0:
            issues.append(f"Division '{div.name}' has subjects, but none require weekly theory or practical sessions")
        elif division_required_periods > available_slots:
            issues.append(
                f"Division '{div.name}' requires {division_required_periods} periods, "
                f"but only {available_slots} teaching slots are available"
            )

    available_slots = len(constraint.working_days) * constraint.number_of_periods
    required_theory_room_periods = sum(
        req.duration_periods for req in requirements if req.session_type == SessionType.THEORY
    )
    classroom_capacity_periods = len(classroom_ids) * available_slots
    if required_theory_room_periods > classroom_capacity_periods:
        issues.append(
            f"The timetable requires {required_theory_room_periods} classroom periods per week, "
            f"but configured classrooms provide only {classroom_capacity_periods}"
        )

    required_practical_room_periods = sum(
        req.duration_periods for req in requirements if req.session_type == SessionType.PRACTICAL
    )
    lab_capacity_periods = len(lab_ids) * available_slots
    if required_practical_room_periods > lab_capacity_periods:
        issues.append(
            f"The timetable requires {required_practical_room_periods} laboratory periods per week, "
            f"but configured laboratories provide only {lab_capacity_periods}"
        )

    faculty_rows = db.query(Faculty).filter(Faculty.id.in_(all_faculty_ids)).all() if all_faculty_ids else []
    faculty_data = {
        f.id: FacultyData(
            id=f.id,
            full_name=f.full_name,
            department_id=f.department_id,
            max_daily_lectures=f.max_daily_lectures,
            max_weekly_lectures=f.max_weekly_lectures,
        )
        for f in faculty_rows
    }

    filtered_requirements: list[SessionRequirement] = []
    for req in requirements:
        eligible_faculty_ids = []
        missing_faculty_ids = []
        for faculty_id in req.eligible_faculty_ids:
            faculty = faculty_data.get(faculty_id)
            if faculty is None:
                missing_faculty_ids.append(faculty_id)
                continue
            subject = subject_data[req.subject_id]
            if faculty.department_id != subject.department_id:
                issues.append(
                    f"Faculty '{faculty.full_name}' is assigned to subject '{subject.code}' "
                    "from a different department"
                )
                continue
            can_teach_duration = (
                faculty.max_daily_lectures >= req.duration_periods
                and faculty.max_weekly_lectures >= req.duration_periods
            )
            if can_teach_duration:
                eligible_faculty_ids.append(faculty_id)

        if missing_faculty_ids:
            issues.append(
                "Faculty assignment references missing faculty record(s): "
                + ", ".join(str(faculty_id) for faculty_id in missing_faculty_ids)
            )
        if not eligible_faculty_ids:
            subject = subject_data[req.subject_id]
            division = division_data[req.division_id]
            issues.append(
                f"No assigned faculty has enough daily/weekly capacity for {req.session_type.value.lower()} "
                f"session '{subject.code}' in division '{division.name}'"
            )

        filtered_requirements.append(replace(req, eligible_faculty_ids=tuple(eligible_faculty_ids)))

    total_required_faculty_periods = sum(req.duration_periods for req in filtered_requirements)
    total_available_faculty_periods = sum(
        min(faculty.max_weekly_lectures, faculty.max_daily_lectures * len(constraint.working_days))
        for faculty in faculty_data.values()
    )
    if total_required_faculty_periods > total_available_faculty_periods:
        issues.append(
            f"The timetable requires {total_required_faculty_periods} faculty periods per week, "
            f"but assigned faculty can cover at most {total_available_faculty_periods}"
        )

    required_periods_by_subject: dict[UUID, int] = {}
    eligible_faculty_by_subject: dict[UUID, set[UUID]] = {}
    for req in filtered_requirements:
        required_periods_by_subject[req.subject_id] = (
            required_periods_by_subject.get(req.subject_id, 0) + req.duration_periods
        )
        eligible_faculty_by_subject.setdefault(req.subject_id, set()).update(req.eligible_faculty_ids)

    for subject_id, required_periods in required_periods_by_subject.items():
        subject = subject_data[subject_id]
        faculty_ids = eligible_faculty_by_subject.get(subject_id, set())
        available_periods = sum(
            min(
                faculty_data[faculty_id].max_weekly_lectures,
                faculty_data[faculty_id].max_daily_lectures * len(constraint.working_days),
            )
            for faculty_id in faculty_ids
            if faculty_id in faculty_data
        )
        if available_periods < required_periods:
            issues.append(
                f"Subject '{subject.code}' requires {required_periods} faculty periods per week, "
                f"but assigned faculty can cover at most {available_periods}"
            )

    required_periods_by_sole_faculty: dict[UUID, int] = {}
    for req in filtered_requirements:
        if len(req.eligible_faculty_ids) == 1:
            faculty_id = req.eligible_faculty_ids[0]
            required_periods_by_sole_faculty[faculty_id] = (
                required_periods_by_sole_faculty.get(faculty_id, 0) + req.duration_periods
            )

    for faculty_id, required_periods in required_periods_by_sole_faculty.items():
        faculty = faculty_data[faculty_id]
        available_periods = min(
            faculty.max_weekly_lectures,
            faculty.max_daily_lectures * len(constraint.working_days),
        )
        if required_periods > available_periods:
            issues.append(
                f"Faculty '{faculty.full_name}' is the only eligible teacher for {required_periods} periods, "
                f"but can cover at most {available_periods} per week"
            )

    if issues:
        raise SolverValidationError(issues)

    return SolverInput(
        days=list(constraint.working_days),
        periods_per_day=constraint.number_of_periods,
        theory_duration_minutes=constraint.theory_duration_minutes,
        practical_duration_minutes=constraint.practical_duration_minutes,
        divisions=division_data,
        subjects=subject_data,
        faculty=faculty_data,
        rooms=room_data,
        requirements=filtered_requirements,
    )
