from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.constraint import Constraint
    from app.models.timetable import GeneratedTimetable


@dataclass(frozen=True)
class PeriodSlot:
    period_index: int
    label: str  # e.g. "P1"
    start_time: str  # "09:00"
    end_time: str  # "10:00"
    duration_minutes: int  # 60
    is_before_lunch: bool
    is_after_lunch: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "period_index": self.period_index,
            "label": self.label,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_minutes": self.duration_minutes,
            "is_before_lunch": self.is_before_lunch,
            "is_after_lunch": self.is_after_lunch,
        }


def time_to_minutes(time_str: str) -> int:
    """Parse 'HH:MM' string into minutes from midnight."""
    hours, minutes = map(int, time_str.strip().split(":"))
    return hours * 60 + minutes


def minutes_to_time(minutes: int) -> str:
    """Format minutes from midnight into 'HH:MM' string."""
    h = (minutes // 60) % 24
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def compute_period_slots(
    college_start_time: str,
    college_end_time: str,
    lunch_break_start: str,
    lunch_break_end: str,
    number_of_periods: int,
    theory_duration_minutes: int,
) -> list[PeriodSlot]:
    """
    Derive exact PeriodSlot objects from institutional scheduling constraints.
    Period slots increment by theory_duration_minutes, stepping over the lunch break
    when reached.
    """
    start_m = time_to_minutes(college_start_time)
    end_m = time_to_minutes(college_end_time)
    lunch_start_m = time_to_minutes(lunch_break_start)
    lunch_end_m = time_to_minutes(lunch_break_end)

    slots: list[PeriodSlot] = []
    current_m = start_m

    for p in range(number_of_periods):
        # If current pointer falls in lunch break, advance past lunch
        if lunch_start_m <= current_m < lunch_end_m:
            current_m = lunch_end_m
        elif current_m < lunch_start_m and (current_m + theory_duration_minutes) > lunch_start_m:
            # If a period would overlap the start of lunch, adjust if starting exactly at lunch
            if current_m == lunch_start_m:
                current_m = lunch_end_m

        period_start_m = current_m
        period_end_m = period_start_m + theory_duration_minutes

        is_before_lunch = period_end_m <= lunch_start_m
        is_after_lunch = period_start_m >= lunch_end_m

        slots.append(
            PeriodSlot(
                period_index=p,
                label=f"P{p + 1}",
                start_time=minutes_to_time(period_start_m),
                end_time=minutes_to_time(period_end_m),
                duration_minutes=theory_duration_minutes,
                is_before_lunch=is_before_lunch,
                is_after_lunch=is_after_lunch,
            )
        )

        # Advance pointer for next period
        current_m = period_end_m
        if lunch_start_m <= current_m < lunch_end_m:
            current_m = lunch_end_m

    return slots


def get_period_schedule_from_constraint(constraint: Constraint) -> list[PeriodSlot]:
    """Compute period slots from a Constraint database record."""
    return compute_period_slots(
        college_start_time=constraint.college_start_time,
        college_end_time=constraint.college_end_time,
        lunch_break_start=constraint.lunch_break_start,
        lunch_break_end=constraint.lunch_break_end,
        number_of_periods=constraint.number_of_periods,
        theory_duration_minutes=constraint.theory_duration_minutes,
    )


def get_period_schedule_from_timetable_record(
    timetable: GeneratedTimetable,
    constraint: Constraint | None = None,
) -> list[PeriodSlot]:
    """
    Compute period slots for a GeneratedTimetable record.
    Uses constraint if provided; otherwise falls back to standard 09:00-17:00 defaults.
    """
    if constraint is not None:
        return compute_period_slots(
            college_start_time=constraint.college_start_time,
            college_end_time=constraint.college_end_time,
            lunch_break_start=constraint.lunch_break_start,
            lunch_break_end=constraint.lunch_break_end,
            number_of_periods=timetable.periods_per_day,
            theory_duration_minutes=timetable.theory_duration_minutes,
        )

    # Fallback to standard 09:00 default schedule
    return compute_period_slots(
        college_start_time="09:00",
        college_end_time="17:00",
        lunch_break_start="13:00",
        lunch_break_end="14:00",
        number_of_periods=timetable.periods_per_day,
        theory_duration_minutes=timetable.theory_duration_minutes,
    )


def is_block_continuous(start_period: int, duration_periods: int, slots: list[PeriodSlot]) -> bool:
    """
    Check whether duration_periods consecutive periods starting at start_period
    form a continuous timeline block (i.e. no lunch break or gaps between them).
    """
    if start_period < 0 or (start_period + duration_periods) > len(slots):
        return False
    if duration_periods <= 1:
        return True

    for i in range(start_period, start_period + duration_periods - 1):
        curr_end_m = time_to_minutes(slots[i].end_time)
        next_start_m = time_to_minutes(slots[i + 1].start_time)
        if curr_end_m != next_start_m:
            return False

    return True


def get_session_time_range(
    period_index: int,
    duration_periods: int,
    slots: list[PeriodSlot],
) -> tuple[str, str]:
    """
    Get the exact (start_time, end_time) string tuple for a session starting at period_index
    and spanning duration_periods.
    """
    if not slots:
        return ("09:00", "10:00")
    if period_index < 0:
        period_index = 0
    if period_index >= len(slots):
        period_index = len(slots) - 1

    start_time = slots[period_index].start_time
    end_idx = min(period_index + max(1, duration_periods) - 1, len(slots) - 1)
    end_time = slots[end_idx].end_time
    return (start_time, end_time)


def get_valid_start_periods_for_duration(duration_periods: int, slots: list[PeriodSlot]) -> list[int]:
    """
    Return all period indices where a session of duration_periods can legally start
    without crossing the lunch break and without exceeding the available periods.
    """
    valid_starts = []
    max_start = len(slots) - duration_periods
    for p in range(max_start + 1):
        if is_block_continuous(p, duration_periods, slots):
            valid_starts.append(p)
    return valid_starts
