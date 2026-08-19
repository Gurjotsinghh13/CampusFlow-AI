from __future__ import annotations

from enum import Enum

from app.models.timetable import TimetableEntry
from app.utils.timeline import PeriodSlot, get_session_time_range


class ViewType(str, Enum):
    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    ROOM = "ROOM"


SESSION_TYPE_ABBREVIATION = {"THEORY": "T", "PRACTICAL": "P"}


def _cell_text(
    entry: TimetableEntry,
    view_type: ViewType,
    start_time: str,
    end_time: str,
    include_room_in_room_view: bool = False,
) -> str:
    abbrev = SESSION_TYPE_ABBREVIATION.get(entry.session_type, entry.session_type[:1])
    time_str = f"{start_time}–{end_time}"

    if view_type == ViewType.STUDENT:
        return f"{entry.subject_code} ({abbrev})\n{time_str}\n{entry.faculty_name}\n{entry.room_number}"
    if view_type == ViewType.FACULTY:
        return f"{entry.subject_code} ({abbrev})\n{time_str}\n{entry.division_name}\n{entry.room_number}"
    if include_room_in_room_view:
        return f"{entry.subject_code} ({abbrev})\n{time_str}\n{entry.division_name}\n{entry.faculty_name}\n{entry.room_number}"
    return f"{entry.subject_code} ({abbrev})\n{time_str}\n{entry.division_name}\n{entry.faculty_name}"


def build_grid(
    entries: list[TimetableEntry],
    days: list[str],
    periods_per_day: int,
    view_type: ViewType,
    practical_block_periods: int = 1,
    period_slots: list[PeriodSlot] | None = None,
    include_room_in_room_view: bool = False,
) -> dict[str, list[str]]:
    """
    Construct a 2D timetable grid mapping day -> list of period cell strings.
    Practical sessions occupy `practical_block_periods` consecutive periods.
    """
    grid: dict[str, list[str]] = {day: [""] * periods_per_day for day in days}

    for entry in entries:
        if entry.day not in grid:
            continue
        span = practical_block_periods if entry.session_type == "PRACTICAL" else 1
        start_time, end_time = get_session_time_range(entry.period_index, span, period_slots or [])
        text = _cell_text(entry, view_type, start_time, end_time, include_room_in_room_view)

        for offset in range(span):
            period = entry.period_index + offset
            if 0 <= period < periods_per_day:
                existing = grid[entry.day][period]
                grid[entry.day][period] = f"{existing}\n\n{text}" if existing and text not in existing else text

    return grid
