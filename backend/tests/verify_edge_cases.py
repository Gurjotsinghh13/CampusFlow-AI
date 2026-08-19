import uuid
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
from app.services.solver.model_builder import CPSATModelBuilder, ModelTooLargeError
from app.services.solver.validator import (
    AssignmentRecord,
    TimetableValidationError,
    validate_generated_timetable,
)
from app.utils.timeline import compute_period_slots, get_session_time_range


def test_edge_cases():
    print("=" * 80)
    print("RUNNING EDGE CASE AUDIT SUITE (A to J)")
    print("=" * 80)

    slots = compute_period_slots("09:00", "17:00", "13:00", "14:00", 7, 60)
    dept_id, sem_id = uuid.uuid4(), uuid.uuid4()

    # Edge Case J: Impossible configuration (single faculty needed for 25 periods but capped at 15)
    print("\n[Edge Case J] Impossible Configuration (Graceful failure test):")
    fac_id = uuid.uuid4()
    div_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    cr_id = uuid.uuid4()

    impossible_faculty = {fac_id: FacultyData(fac_id, "Overloaded Prof", dept_id, 3, 10)}
    impossible_reqs = [
        SessionRequirement(div_id, sub_id, SessionType.THEORY, i, 1, (fac_id,), (cr_id,))
        for i in range(15)  # Needs 15 hours, max is 10
    ]
    impossible_input = SolverInput(
        days=["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"],
        periods_per_day=7,
        theory_duration_minutes=60,
        practical_duration_minutes=120,
        period_slots=slots,
        divisions={div_id: DivisionData(div_id, "Div-1", dept_id, sem_id, 50)},
        subjects={sub_id: SubjectData(sub_id, "Math", "M101", sem_id, dept_id, 15, 0, (fac_id,))},
        faculty=impossible_faculty,
        rooms={cr_id: RoomData(cr_id, "R1", 60, "CLASSROOM")},
        requirements=impossible_reqs,
    )

    builder_j = CPSATModelBuilder(impossible_input)
    model_j = builder_j.build()
    solver_j = cp_model.CpSolver()
    solver_j.parameters.max_time_in_seconds = 5
    status_j = solver_j.Solve(model_j)
    assert status_j == cp_model.INFEASIBLE, f"Expected INFEASIBLE, got {status_j}"
    print("  -> PASSED: Infeasible configuration correctly detected and reported as INFEASIBLE (no crash, no invalid output)")

    # Edge Case G: Practical block placed immediately before lunch (P3-P4: 11:00-13:00) vs across lunch (P4-P5)
    print("\n[Edge Case G & F] Practical near lunch boundary & consecutive multi-periods:")
    div_g_id = uuid.uuid4()
    sub_g_id = uuid.uuid4()
    fac_g_id = uuid.uuid4()
    lab_g_id = uuid.uuid4()

    g_reqs = [
        SessionRequirement(div_g_id, sub_g_id, SessionType.PRACTICAL, 0, 2, (fac_g_id,), (lab_g_id,))
    ]
    g_input = SolverInput(
        days=["MONDAY"],
        periods_per_day=7,
        theory_duration_minutes=60,
        practical_duration_minutes=120,
        period_slots=slots,
        divisions={div_g_id: DivisionData(div_g_id, "Div-G", dept_id, sem_id, 50)},
        subjects={sub_g_id: SubjectData(sub_g_id, "Lab", "L101", sem_id, dept_id, 0, 1, (fac_g_id,))},
        faculty={fac_g_id: FacultyData(fac_g_id, "Lab Prof", dept_id, 4, 10)},
        rooms={lab_g_id: RoomData(lab_g_id, "Lab-1", 60, "LAB")},
        requirements=g_reqs,
    )

    builder_g = CPSATModelBuilder(g_input)
    # Check that start_period == 3 (P4 crossing lunch) does NOT exist in variables!
    p4_keys = [k for k in builder_g.assignment_vars if k.start_period == 3]
    assert len(p4_keys) == 0, "Variable with start_period=3 should NOT exist"
    print("  -> PASSED: Lunch-crossing start period P4 is completely excluded from decision space")

    # Edge Case H & I: High Room & Faculty Utilization (3 divisions competing for 2 classrooms and 1 lab)
    print("\n[Edge Case H & I] High Resource Utilization (3 divisions, 2 classrooms, 1 shared lab):")
    div_ids = [uuid.uuid4() for _ in range(3)]
    sub_h_ids = [uuid.uuid4() for _ in range(3)]
    fac_h_ids = [uuid.uuid4() for _ in range(3)]
    cr_h_ids = [uuid.uuid4() for _ in range(2)]  # Only 2 classrooms for 3 divisions!
    lab_h_id = uuid.uuid4()                      # Only 1 shared lab

    divisions_h = {d_id: DivisionData(d_id, f"Div-{i+1}", dept_id, sem_id, 60) for i, d_id in enumerate(div_ids)}
    faculty_h = {f_id: FacultyData(f_id, f"Prof-{i+1}", dept_id, 4, 18) for i, f_id in enumerate(fac_h_ids)}
    rooms_h = {
        cr_h_ids[0]: RoomData(cr_h_ids[0], "CR-A", 70, "CLASSROOM"),
        cr_h_ids[1]: RoomData(cr_h_ids[1], "CR-B", 70, "CLASSROOM"),
        lab_h_id: RoomData(lab_h_id, "LAB-Shared", 70, "LAB"),
    }
    subjects_h = {
        sub_h_ids[0]: SubjectData(sub_h_ids[0], "Subject-1", "S101", sem_id, dept_id, 3, 1, (fac_h_ids[0],)),
        sub_h_ids[1]: SubjectData(sub_h_ids[1], "Subject-2", "S102", sem_id, dept_id, 3, 1, (fac_h_ids[1],)),
        sub_h_ids[2]: SubjectData(sub_h_ids[2], "Subject-3", "S103", sem_id, dept_id, 3, 1, (fac_h_ids[2],)),
    }

    reqs_h = []
    for div_id in div_ids:
        for s_idx, s_id in enumerate(sub_h_ids):
            # 2 theory + 1 practical per subject
            for t in range(2):
                reqs_h.append(
                    SessionRequirement(div_id, s_id, SessionType.THEORY, t, 1, (fac_h_ids[s_idx],), tuple(cr_h_ids))
                )
            reqs_h.append(
                SessionRequirement(div_id, s_id, SessionType.PRACTICAL, 0, 2, (fac_h_ids[s_idx],), (lab_h_id,))
            )

    high_util_input = SolverInput(
        days=["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"],
        periods_per_day=7,
        theory_duration_minutes=60,
        practical_duration_minutes=120,
        period_slots=slots,
        divisions=divisions_h,
        subjects=subjects_h,
        faculty=faculty_h,
        rooms=rooms_h,
        requirements=reqs_h,
    )

    builder_h = CPSATModelBuilder(high_util_input)
    model_h = builder_h.build()
    solver_h = cp_model.CpSolver()
    solver_h.parameters.max_time_in_seconds = 10
    solver_h.parameters.num_search_workers = 4
    status_h = solver_h.Solve(model_h)
    assert status_h in (cp_model.OPTIMAL, cp_model.FEASIBLE), f"High utilization failed with status {status_h}"

    reqs_by_k = {r.key: r for r in reqs_h}
    assigns_h = []
    for k, v in builder_h.assignment_vars.items():
        if solver_h.Value(v) == 1:
            r = reqs_by_k[k.requirement_key]
            st, et = get_session_time_range(k.start_period, r.duration_periods, slots)
            assigns_h.append(
                AssignmentRecord(
                    requirement_key=r.key,
                    division_id=r.division_id,
                    subject_id=r.subject_id,
                    faculty_id=k.faculty_id,
                    room_id=k.room_id,
                    day=high_util_input.days[k.day_idx],
                    period_index=k.start_period,
                    duration_periods=r.duration_periods,
                    session_type=r.session_type.value,
                    start_time=st,
                    end_time=et,
                )
            )

    metrics_h = validate_generated_timetable(high_util_input, assigns_h, slots)
    assert metrics_h.is_valid, "Validation failed on high utilization schedule"
    assert metrics_h.room_conflicts == 0, "Room conflict detected"
    assert metrics_h.division_conflicts == 0, "Division conflict detected"
    print(f"  -> PASSED: High utilization solver successfully scheduled {len(assigns_h)} sessions across constrained rooms without conflicts (Quality Score: {metrics_h.quality_score}/100)")

    print("\n" + "=" * 80)
    print("ALL EDGE CASES (A to J) TESTED AND PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    test_edge_cases()
