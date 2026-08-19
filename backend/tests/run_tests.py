import sys
import uuid

from app.utils.timeline import (
    compute_period_slots,
    is_block_continuous,
    get_valid_start_periods_for_duration,
    get_session_time_range,
    time_to_minutes,
    minutes_to_time,
)
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
    TimetableValidationError,
    validate_generated_timetable,
)
from app.models.timetable import TimetableEntry
from app.services.export.grid_builder import ViewType, build_grid
from app.services.export.pdf_export import build_pdf
from app.services.export.excel_export import build_excel
from ortools.sat.python import cp_model


def run_all_tests():
    passed = 0
    failed = 0

    def check(name, condition, msg=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name}: {msg}")

    print("\n=== RUNNING TIMELINE TESTS ===")
    check("time_to_minutes('09:00')", time_to_minutes("09:00") == 540)
    check("time_to_minutes('13:00')", time_to_minutes("13:00") == 780)
    check("minutes_to_time(840)", minutes_to_time(840) == "14:00")

    slots = compute_period_slots("09:00", "17:00", "13:00", "14:00", 7, 60)
    check("Slot count is 7", len(slots) == 7)
    check("P1 start/end", slots[0].start_time == "09:00" and slots[0].end_time == "10:00")
    check("P4 before lunch", slots[3].start_time == "12:00" and slots[3].end_time == "13:00" and slots[3].is_before_lunch)
    check("P5 after lunch", slots[4].start_time == "14:00" and slots[4].end_time == "15:00" and slots[4].is_after_lunch)

    check("P1 1-period continuous", is_block_continuous(0, 1, slots))
    check("P1-P2 continuous", is_block_continuous(0, 2, slots))
    check("P4-P5 lunch crossing REJECTED", not is_block_continuous(3, 2, slots), "Must not allow crossing lunch")
    check("P5-P6 continuous", is_block_continuous(4, 2, slots))
    check("Valid 2-period starts", get_valid_start_periods_for_duration(2, slots) == [0, 1, 2, 4, 5])

    print("\n=== RUNNING SOLVER MODEL & VALIDATION TESTS ===")
    dept_id, sem_id, div_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    fac1_id, fac2_id = uuid.uuid4(), uuid.uuid4()
    sub1_id, sub2_id = uuid.uuid4(), uuid.uuid4()
    cr_id, lab_id = uuid.uuid4(), uuid.uuid4()

    divisions = {div_id: DivisionData(div_id, "Div-A", dept_id, sem_id, 60)}
    subjects = {
        sub1_id: SubjectData(sub1_id, "DS", "CS201", sem_id, dept_id, 3, 1, (fac1_id,)),
        sub2_id: SubjectData(sub2_id, "DB", "CS202", sem_id, dept_id, 3, 1, (fac2_id,)),
    }
    faculty = {
        fac1_id: FacultyData(fac1_id, "Prof. Alan Turing", dept_id, 4, 16),
        fac2_id: FacultyData(fac2_id, "Prof. Grace Hopper", dept_id, 4, 16),
    }
    rooms = {
        cr_id: RoomData(cr_id, "CR-101", 70, "CLASSROOM"),
        lab_id: RoomData(lab_id, "LAB-201", 70, "LAB"),
    }
    requirements = [
        # CS201: 3 theory + 1 practical (2h)
        SessionRequirement(div_id, sub1_id, SessionType.THEORY, 0, 1, (fac1_id,), (cr_id,)),
        SessionRequirement(div_id, sub1_id, SessionType.THEORY, 1, 1, (fac1_id,), (cr_id,)),
        SessionRequirement(div_id, sub1_id, SessionType.THEORY, 2, 1, (fac1_id,), (cr_id,)),
        SessionRequirement(div_id, sub1_id, SessionType.PRACTICAL, 0, 2, (fac1_id,), (lab_id,)),
        # CS202: 3 theory + 1 practical (2h)
        SessionRequirement(div_id, sub2_id, SessionType.THEORY, 0, 1, (fac2_id,), (cr_id,)),
        SessionRequirement(div_id, sub2_id, SessionType.THEORY, 1, 1, (fac2_id,), (cr_id,)),
        SessionRequirement(div_id, sub2_id, SessionType.THEORY, 2, 1, (fac2_id,), (cr_id,)),
        SessionRequirement(div_id, sub2_id, SessionType.PRACTICAL, 0, 2, (fac2_id,), (lab_id,)),
    ]
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
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.num_search_workers = 4
    status = solver.Solve(model)
    check("CP-SAT finds solution", status in (cp_model.OPTIMAL, cp_model.FEASIBLE))

    reqs_by_key = {r.key: r for r in requirements}
    assignments = []
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
    check("Validation passed", metrics.is_valid)
    check("All 8 sessions generated", metrics.total_generated_sessions == 8)
    check("Zero division conflicts", metrics.division_conflicts == 0)
    check("Zero faculty conflicts", metrics.faculty_conflicts == 0)
    check("Zero room conflicts", metrics.room_conflicts == 0)
    check("Quality score >= 80", metrics.quality_score >= 80.0, f"Score was {metrics.quality_score}")

    no_lunch_cross = all(a.period_index != 3 for a in assignments if a.session_type == "PRACTICAL")
    check("No practical crosses lunch (P4 start)", no_lunch_cross)

    print("\n=== RUNNING EXPORT TESTS ===")
    entries = [
        TimetableEntry(
            id=uuid.uuid4(),
            timetable_id=uuid.uuid4(),
            division_id=div_id,
            subject_id=sub1_id,
            faculty_id=fac1_id,
            room_id=cr_id,
            day="MONDAY",
            period_index=0,
            session_type="THEORY",
            division_name="Div-A",
            subject_name="Data Structures",
            subject_code="CS201",
            faculty_name="Prof. Alan Turing",
            room_number="CR-101",
        )
    ]
    grid = build_grid(entries, solver_input.days, 7, ViewType.STUDENT, 2, slots)
    check("Grid cell contains time", "09:00–10:00" in grid["MONDAY"][0])
    check("Grid cell contains code", "CS201 (T)" in grid["MONDAY"][0])

    pdf_bytes = build_pdf("Student Timetable", solver_input.days, 7, slots, grid)
    check("PDF export bytes valid", isinstance(pdf_bytes, bytes) and pdf_bytes.startswith(b"%PDF"))

    excel_bytes = build_excel("Student Timetable", solver_input.days, 7, slots, grid)
    check("Excel export bytes valid", isinstance(excel_bytes, bytes) and len(excel_bytes) > 500)

    print(f"\n==========================================")
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print(f"==========================================")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
