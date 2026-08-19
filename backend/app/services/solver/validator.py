from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.models.room import RoomType
from app.services.solver.data_types import SessionType, SolverInput
from app.utils.timeline import (
    PeriodSlot,
    is_block_continuous,
    time_to_minutes,
)


class TimetableValidationError(Exception):
    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("; ".join(issues))


@dataclass(frozen=True)
class AssignmentRecord:
    requirement_key: str
    division_id: UUID
    subject_id: UUID
    faculty_id: UUID
    room_id: UUID
    day: str
    period_index: int
    duration_periods: int
    session_type: str
    start_time: str
    end_time: str


@dataclass(frozen=True)
class TimetableQualityMetrics:
    total_required_sessions: int
    total_generated_sessions: int
    division_conflicts: int
    faculty_conflicts: int
    room_conflicts: int
    student_gap_periods: int
    faculty_gap_periods: int
    is_valid: bool
    quality_score: float  # 0 to 100


def validate_generated_timetable(
    solver_input: SolverInput,
    assignments: list[AssignmentRecord],
    period_slots: list[PeriodSlot],
) -> TimetableQualityMetrics:
    """
    Automated validation layer executing 16 integrity and quality checks
    before a generated timetable is persisted or shown to users.
    """
    issues: list[str] = []

    # 1. Required session count == generated session count
    required_keys = {req.key for req in solver_input.requirements}
    generated_keys = [a.requirement_key for a in assignments]

    if len(generated_keys) != len(required_keys):
        issues.append(
            f"Expected {len(required_keys)} scheduled sessions, but generated {len(generated_keys)}"
        )

    # 2. No duplicate session assignments
    if len(generated_keys) != len(set(generated_keys)):
        issues.append("Duplicate session assignment detected in generated timetable")

    missing_keys = required_keys - set(generated_keys)
    if missing_keys:
        issues.append(f"Missing required sessions: {', '.join(sorted(missing_keys))}")

    # Track occupancies for conflict detection
    # (entity_id, day, period) -> list of assignment details
    division_occupancy: dict[tuple[UUID, str, int], list[AssignmentRecord]] = {}
    faculty_occupancy: dict[tuple[UUID, str, int], list[AssignmentRecord]] = {}
    room_occupancy: dict[tuple[UUID, str, int], list[AssignmentRecord]] = {}

    faculty_daily_hours: dict[tuple[UUID, str], int] = {}
    faculty_weekly_hours: dict[UUID, int] = {}

    division_conflicts = 0
    faculty_conflicts = 0
    room_conflicts = 0

    slots_by_index = {s.period_index: s for s in period_slots}
    lunch_start_m = time_to_minutes(solver_input.lunch_break_start)
    lunch_end_m = time_to_minutes(solver_input.lunch_break_end)

    for a in assignments:
        # 16. Every generated period_index maps to a valid PeriodSlot
        if a.period_index not in slots_by_index:
            issues.append(f"Assignment has invalid period index {a.period_index}")
            continue

        # 14. All sessions are inside working hours
        if a.day not in solver_input.days:
            issues.append(f"Assignment scheduled on non-working day '{a.day}'")

        # 11 & 12. Multi-period continuity and no lunch crossing
        if a.duration_periods > 1:
            if not is_block_continuous(a.period_index, a.duration_periods, period_slots):
                issues.append(
                    f"Practical session for subject '{a.requirement_key}' starting at P{a.period_index + 1} "
                    f"spans across lunch or is not continuous"
                )

        # 13 & 15. Valid start/end times and not inside lunch
        start_m = time_to_minutes(a.start_time)
        end_m = time_to_minutes(a.end_time)
        if start_m >= end_m:
            issues.append(f"Invalid time range {a.start_time}-{a.end_time} for session '{a.requirement_key}'")

        if start_m < lunch_end_m and end_m > lunch_start_m:
            # Check if duration overlaps the actual lunch gap
            if start_m < lunch_end_m and start_m >= lunch_start_m:
                issues.append(f"Session '{a.requirement_key}' is scheduled inside lunch break ({a.start_time})")

        # 9. Room capacity check
        room = solver_input.rooms.get(a.room_id)
        division = solver_input.divisions.get(a.division_id)
        if room and division:
            if room.capacity < division.student_count:
                issues.append(
                    f"Room '{room.room_number}' capacity ({room.capacity}) is smaller than "
                    f"division '{division.name}' student count ({division.student_count})"
                )

            # 10. Lab requirements respected
            if a.session_type == SessionType.PRACTICAL.value and room.room_type != RoomType.LAB.value:
                issues.append(
                    f"Practical session '{a.requirement_key}' is placed in non-laboratory room '{room.room_number}'"
                )

        # Resource occupancies across occupied periods
        for offset in range(a.duration_periods):
            p = a.period_index + offset

            # 3. Division conflicts
            div_key = (a.division_id, a.day, p)
            division_occupancy.setdefault(div_key, []).append(a)

            # 4. Faculty conflicts
            fac_key = (a.faculty_id, a.day, p)
            faculty_occupancy.setdefault(fac_key, []).append(a)

            # 5 & 6. Room/Lab conflicts
            rm_key = (a.room_id, a.day, p)
            room_occupancy.setdefault(rm_key, []).append(a)

        # Workload accumulators
        faculty_daily_hours[(a.faculty_id, a.day)] = (
            faculty_daily_hours.get((a.faculty_id, a.day), 0) + a.duration_periods
        )
        faculty_weekly_hours[a.faculty_id] = (
            faculty_weekly_hours.get(a.faculty_id, 0) + a.duration_periods
        )

    # Check overlaps
    for (div_id, day, p), occs in division_occupancy.items():
        if len(occs) > 1:
            division_conflicts += 1
            issues.append(f"Division {div_id} has {len(occs)} simultaneous classes on {day} period P{p + 1}")

    for (fac_id, day, p), occs in faculty_occupancy.items():
        if len(occs) > 1:
            faculty_conflicts += 1
            faculty_name = solver_input.faculty[fac_id].full_name if fac_id in solver_input.faculty else str(fac_id)
            issues.append(f"Faculty '{faculty_name}' is double-booked on {day} period P{p + 1}")

    for (rm_id, day, p), occs in room_occupancy.items():
        if len(occs) > 1:
            room_conflicts += 1
            room_num = solver_input.rooms[rm_id].room_number if rm_id in solver_input.rooms else str(rm_id)
            issues.append(f"Room '{room_num}' is double-booked on {day} period P{p + 1}")

    # 7 & 8. Faculty workload limit checks
    for (fac_id, day), daily_hours in faculty_daily_hours.items():
        faculty = solver_input.faculty.get(fac_id)
        if faculty and daily_hours > faculty.max_daily_lectures:
            issues.append(
                f"Faculty '{faculty.full_name}' daily load ({daily_hours} periods on {day}) "
                f"exceeds limit ({faculty.max_daily_lectures})"
            )

    for fac_id, weekly_hours in faculty_weekly_hours.items():
        faculty = solver_input.faculty.get(fac_id)
        if faculty and weekly_hours > faculty.max_weekly_lectures:
            issues.append(
                f"Faculty '{faculty.full_name}' weekly load ({weekly_hours} periods) "
                f"exceeds limit ({faculty.max_weekly_lectures})"
            )

    # Quality metrics: count idle gaps
    student_gap_periods = _count_division_idle_gaps(division_occupancy, solver_input)
    faculty_gap_periods = _count_faculty_idle_gaps(faculty_occupancy, solver_input)

    is_valid = len(issues) == 0
    if not is_valid:
        raise TimetableValidationError(issues)

    # Calculate overall quality score (100 = perfect compact, balanced schedule)
    gap_penalty = min(30.0, (student_gap_periods * 3.0) + (faculty_gap_periods * 1.5))
    quality_score = max(50.0, 100.0 - gap_penalty)

    return TimetableQualityMetrics(
        total_required_sessions=len(required_keys),
        total_generated_sessions=len(assignments),
        division_conflicts=division_conflicts,
        faculty_conflicts=faculty_conflicts,
        room_conflicts=room_conflicts,
        student_gap_periods=student_gap_periods,
        faculty_gap_periods=faculty_gap_periods,
        is_valid=is_valid,
        quality_score=round(quality_score, 1),
    )


def _count_division_idle_gaps(
    division_occupancy: dict[tuple[UUID, str, int], list[AssignmentRecord]],
    solver_input: SolverInput,
) -> int:
    total_gaps = 0
    n_periods = solver_input.periods_per_day
    for division_id in solver_input.divisions:
        for day in solver_input.days:
            occupied = [
                p for p in range(n_periods)
                if (division_id, day, p) in division_occupancy
            ]
            if len(occupied) >= 2:
                span = max(occupied) - min(occupied) + 1
                gaps = span - len(occupied)
                total_gaps += max(0, gaps)
    return total_gaps


def _count_faculty_idle_gaps(
    faculty_occupancy: dict[tuple[UUID, str, int], list[AssignmentRecord]],
    solver_input: SolverInput,
) -> int:
    total_gaps = 0
    n_periods = solver_input.periods_per_day
    for faculty_id in solver_input.faculty:
        for day in solver_input.days:
            occupied = [
                p for p in range(n_periods)
                if (faculty_id, day, p) in faculty_occupancy
            ]
            if len(occupied) >= 2:
                span = max(occupied) - min(occupied) + 1
                gaps = span - len(occupied)
                total_gaps += max(0, gaps)
    return total_gaps
