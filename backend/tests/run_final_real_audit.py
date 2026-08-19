from __future__ import annotations

import math
import sys
import uuid
from typing import Any

from ortools.sat.python import cp_model

from app.models.room import RoomType
from app.services.solver.data_types import (
    DivisionData,
    FacultyData,
    RoomData,
    SessionRequirement,
    SessionType,
    SolverInput,
    SubjectData,
)
from app.services.solver.model_builder import CPSATModelBuilder
from app.services.solver.validator import (
    AssignmentRecord,
    validate_generated_timetable,
)
from app.utils.timeline import compute_period_slots, get_session_time_range


def run_audit() -> dict[str, Any]:
    slots = compute_period_slots("09:00", "17:00", "13:00", "14:00", 7, 60)
    dept_id = uuid.uuid4()
    sem_id = uuid.uuid4()

    div_a_id = uuid.uuid4()
    div_b_id = uuid.uuid4()

    divisions = {
        div_a_id: DivisionData(div_a_id, "Division A (CSE-4A)", dept_id, sem_id, 60),
        div_b_id: DivisionData(div_b_id, "Division B (CSE-4B)", dept_id, sem_id, 60),
    }

    fac_ids = [uuid.uuid4() for _ in range(6)]
    faculty = {
        fac_ids[0]: FacultyData(fac_ids[0], "Prof. Alan Turing", dept_id, 4, 18),
        fac_ids[1]: FacultyData(fac_ids[1], "Prof. Grace Hopper", dept_id, 4, 18),
        fac_ids[2]: FacultyData(fac_ids[2], "Prof. Ken Thompson", dept_id, 4, 18),
        fac_ids[3]: FacultyData(fac_ids[3], "Prof. Vint Cerf", dept_id, 4, 18),
        fac_ids[4]: FacultyData(fac_ids[4], "Prof. Claude Shannon", dept_id, 4, 18),
        fac_ids[5]: FacultyData(fac_ids[5], "Prof. Ada Lovelace", dept_id, 4, 18),
    }

    cr1_id, cr2_id, cr3_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    lab1_id, lab2_id, lab3_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    rooms = {
        cr1_id: RoomData(cr1_id, "CR-101", 70, "CLASSROOM"),
        cr2_id: RoomData(cr2_id, "CR-102", 70, "CLASSROOM"),
        cr3_id: RoomData(cr3_id, "CR-103", 70, "CLASSROOM"),
        lab1_id: RoomData(lab1_id, "SW-LAB-1", 70, "LAB"),
        lab2_id: RoomData(lab2_id, "DB-LAB-2", 70, "LAB"),
        lab3_id: RoomData(lab3_id, "NET-LAB-3", 70, "LAB"),
    }

    sub_ids = [uuid.uuid4() for _ in range(5)]
    subjects = {
        sub_ids[0]: SubjectData(sub_ids[0], "Data Structures & Algorithms", "CS401", sem_id, dept_id, 3, 1, (fac_ids[0], fac_ids[5])),
        sub_ids[1]: SubjectData(sub_ids[1], "Database Management Systems", "CS402", sem_id, dept_id, 3, 1, (fac_ids[1],)),
        sub_ids[2]: SubjectData(sub_ids[2], "Operating Systems", "CS403", sem_id, dept_id, 3, 1, (fac_ids[2], fac_ids[5])),
        sub_ids[3]: SubjectData(sub_ids[3], "Computer Networks", "CS404", sem_id, dept_id, 3, 1, (fac_ids[3],)),
        sub_ids[4]: SubjectData(sub_ids[4], "Discrete Mathematics", "CS405", sem_id, dept_id, 4, 0, (fac_ids[4],)),
    }

    classroom_ids = (cr1_id, cr2_id, cr3_id)
    requirements: list[SessionRequirement] = []

    for div_id in (div_a_id, div_b_id):
        # CS401 (3 Theory, 1 Practical [2h])
        for i in range(3):
            requirements.append(SessionRequirement(div_id, sub_ids[0], SessionType.THEORY, i, 1, (fac_ids[0], fac_ids[5]), classroom_ids))
        requirements.append(SessionRequirement(div_id, sub_ids[0], SessionType.PRACTICAL, 0, 2, (fac_ids[0], fac_ids[5]), (lab1_id,)))

        # CS402 (3 Theory, 1 Practical [2h])
        for i in range(3):
            requirements.append(SessionRequirement(div_id, sub_ids[1], SessionType.THEORY, i, 1, (fac_ids[1],), classroom_ids))
        requirements.append(SessionRequirement(div_id, sub_ids[1], SessionType.PRACTICAL, 0, 2, (fac_ids[1],), (lab2_id,)))

        # CS403 (3 Theory, 1 Practical [2h])
        for i in range(3):
            requirements.append(SessionRequirement(div_id, sub_ids[2], SessionType.THEORY, i, 1, (fac_ids[2], fac_ids[5]), classroom_ids))
        requirements.append(SessionRequirement(div_id, sub_ids[2], SessionType.PRACTICAL, 0, 2, (fac_ids[2], fac_ids[5]), (lab1_id, lab3_id)))

        # CS404 (3 Theory, 1 Practical [2h])
        for i in range(3):
            requirements.append(SessionRequirement(div_id, sub_ids[3], SessionType.THEORY, i, 1, (fac_ids[3],), classroom_ids))
        requirements.append(SessionRequirement(div_id, sub_ids[3], SessionType.PRACTICAL, 0, 2, (fac_ids[3],), (lab3_id,)))

        # CS405 (4 Theory, 0 Practical)
        for i in range(4):
            requirements.append(SessionRequirement(div_id, sub_ids[4], SessionType.THEORY, i, 1, (fac_ids[4],), classroom_ids))

    solver_input = SolverInput(
        days=["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"],
        periods_per_day=7,
        theory_duration_minutes=60,
        practical_duration_minutes=120,
        college_start_time="09:00",
        college_end_time="17:00",
        lunch_break_start="13:00",
        lunch_break_end="14:00",
        period_slots=slots,
        divisions=divisions,
        subjects=subjects,
        faculty=faculty,
        rooms=rooms,
        requirements=requirements,
    )

    builder = CPSATModelBuilder(solver_input)
    model = builder.build()

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15
    solver.parameters.num_search_workers = 4
    status_code = solver.Solve(model)

    reqs_by_key = {r.key: r for r in requirements}
    assignments: list[AssignmentRecord] = []
    for key, var in builder.assignment_vars.items():
        if solver.Value(var) == 1:
            req = reqs_by_key[key.requirement_key]
            st, et = get_session_time_range(key.start_period, req.duration_periods, slots)
            assignments.append(
                AssignmentRecord(
                    requirement_key=req.key,
                    division_id=req.division_id,
                    subject_id=req.subject_id,
                    faculty_id=key.faculty_id,
                    room_id=key.room_id,
                    day=solver_input.days[key.day_idx],
                    period_index=key.start_period,
                    duration_periods=req.duration_periods,
                    session_type=req.session_type.value,
                    start_time=st,
                    end_time=et,
                )
            )

    metrics = validate_generated_timetable(solver_input, assignments, slots)

    # 1. Subject Reconciliation Table
    # (Subject, Division, Req Sessions, Req Hours, Sched Sessions, Sched Hours, Diff)
    reconciliation = []
    for div_id, div in divisions.items():
        for sub_id, sub in subjects.items():
            req_theory = sub.theory_sessions_per_week
            req_pract = sub.practical_sessions_per_week
            req_sessions = req_theory + req_pract
            req_hours = req_theory * 1 + req_pract * 2

            sched_assigns = [a for a in assignments if a.division_id == div_id and a.subject_id == sub_id]
            sched_sessions = len(sched_assigns)
            sched_hours = sum(a.duration_periods for a in sched_assigns)
            diff_hours = sched_hours - req_hours

            reconciliation.append({
                "division": div.name,
                "code": sub.code,
                "name": sub.name,
                "req_sessions": req_sessions,
                "req_hours": req_hours,
                "sched_sessions": sched_sessions,
                "sched_hours": sched_hours,
                "diff_hours": diff_hours,
            })

    # 2. Division Daily Loads
    div_loads = {}
    for div_id, div in divisions.items():
        day_map = {d: 0 for d in solver_input.days}
        for a in assignments:
            if a.division_id == div_id:
                day_map[a.day] += a.duration_periods
        div_loads[div.name] = day_map

    # 3. Faculty detailed schedules & gaps
    fac_details = {}
    for fac_id, fac in faculty.items():
        day_hours = {d: 0 for d in solver_input.days}
        earliest_m = None
        latest_m = None
        teaching_days = 0
        fac_gaps = 0

        for d in solver_input.days:
            fac_d_assigns = [a for a in assignments if a.faculty_id == fac_id and a.day == d]
            if fac_d_assigns:
                teaching_days += 1
                day_hours[d] = sum(a.duration_periods for a in fac_d_assigns)

                occupied_periods = []
                for a in fac_d_assigns:
                    for off in range(a.duration_periods):
                        occupied_periods.append(a.period_index + off)
                occupied_periods.sort()

                if len(occupied_periods) >= 2:
                    span = max(occupied_periods) - min(occupied_periods) + 1
                    gaps = span - len(occupied_periods)
                    fac_gaps += max(0, gaps)

                first_slot = slots[min(occupied_periods)]
                last_slot = slots[max(occupied_periods)]
                if earliest_m is None or first_slot.start_time < earliest_m:
                    earliest_m = first_slot.start_time
                if latest_m is None or last_slot.end_time > latest_m:
                    latest_m = last_slot.end_time

        fac_details[fac.full_name] = {
            "day_hours": day_hours,
            "weekly_hours": sum(day_hours.values()),
            "teaching_days": teaching_days,
            "earliest_class": earliest_m or "N/A",
            "latest_class": latest_m or "N/A",
            "idle_gaps": fac_gaps,
        }

    # 4. Room utilization
    room_usage = {r.room_number: {"type": r.room_type, "capacity": r.capacity, "hours": 0} for r in rooms.values()}
    for a in assignments:
        rm = rooms[a.room_id]
        room_usage[rm.room_number]["hours"] += a.duration_periods

    return {
        "status": "OPTIMAL" if status_code == cp_model.OPTIMAL else "FEASIBLE",
        "solver_input": solver_input,
        "assignments": assignments,
        "metrics": metrics,
        "reconciliation": reconciliation,
        "div_loads": div_loads,
        "fac_details": fac_details,
        "room_usage": room_usage,
    }


if __name__ == "__main__":
    data = run_audit()
    print("Audit run successful. Status:", data["status"])
    print("Total assignments:", len(data["assignments"]))
