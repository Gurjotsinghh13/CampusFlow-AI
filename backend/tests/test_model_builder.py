import unittest
import uuid

from ortools.sat.python import cp_model

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
from app.utils.timeline import compute_period_slots, get_session_time_range


def get_base_solver_input():
    slots = compute_period_slots(
        college_start_time="09:00",
        college_end_time="17:00",
        lunch_break_start="13:00",
        lunch_break_end="14:00",
        number_of_periods=7,
        theory_duration_minutes=60,
    )

    dept_id = uuid.uuid4()
    sem_id = uuid.uuid4()
    div_id = uuid.uuid4()
    fac1_id = uuid.uuid4()
    fac2_id = uuid.uuid4()
    sub1_id = uuid.uuid4()
    sub2_id = uuid.uuid4()
    classroom_id = uuid.uuid4()
    lab_id = uuid.uuid4()

    divisions = {
        div_id: DivisionData(
            id=div_id,
            name="Div-A",
            department_id=dept_id,
            semester_id=sem_id,
            student_count=60,
        )
    }

    subjects = {
        sub1_id: SubjectData(
            id=sub1_id,
            name="Data Structures",
            code="CS201",
            semester_id=sem_id,
            department_id=dept_id,
            theory_sessions_per_week=3,
            practical_sessions_per_week=1,
            eligible_faculty_ids=(fac1_id,),
        ),
        sub2_id: SubjectData(
            id=sub2_id,
            name="Database Systems",
            code="CS202",
            semester_id=sem_id,
            department_id=dept_id,
            theory_sessions_per_week=3,
            practical_sessions_per_week=1,
            eligible_faculty_ids=(fac2_id,),
        ),
    }

    faculty = {
        fac1_id: FacultyData(
            id=fac1_id,
            full_name="Prof. Alan Turing",
            department_id=dept_id,
            max_daily_lectures=4,
            max_weekly_lectures=16,
        ),
        fac2_id: FacultyData(
            id=fac2_id,
            full_name="Prof. Grace Hopper",
            department_id=dept_id,
            max_daily_lectures=4,
            max_weekly_lectures=16,
        ),
    }

    rooms = {
        classroom_id: RoomData(
            id=classroom_id,
            room_number="CR-101",
            capacity=70,
            room_type="CLASSROOM",
        ),
        lab_id: RoomData(
            id=lab_id,
            room_number="LAB-201",
            capacity=70,
            room_type="LAB",
        ),
    }

    requirements = [
        SessionRequirement(
            division_id=div_id,
            subject_id=sub1_id,
            session_type=SessionType.THEORY,
            session_index=0,
            duration_periods=1,
            eligible_faculty_ids=(fac1_id,),
            eligible_room_ids=(classroom_id,),
        ),
        SessionRequirement(
            division_id=div_id,
            subject_id=sub1_id,
            session_type=SessionType.THEORY,
            session_index=1,
            duration_periods=1,
            eligible_faculty_ids=(fac1_id,),
            eligible_room_ids=(classroom_id,),
        ),
        SessionRequirement(
            division_id=div_id,
            subject_id=sub1_id,
            session_type=SessionType.THEORY,
            session_index=2,
            duration_periods=1,
            eligible_faculty_ids=(fac1_id,),
            eligible_room_ids=(classroom_id,),
        ),
        SessionRequirement(
            division_id=div_id,
            subject_id=sub1_id,
            session_type=SessionType.PRACTICAL,
            session_index=0,
            duration_periods=2,
            eligible_faculty_ids=(fac1_id,),
            eligible_room_ids=(lab_id,),
        ),
        SessionRequirement(
            division_id=div_id,
            subject_id=sub2_id,
            session_type=SessionType.THEORY,
            session_index=0,
            duration_periods=1,
            eligible_faculty_ids=(fac2_id,),
            eligible_room_ids=(classroom_id,),
        ),
        SessionRequirement(
            division_id=div_id,
            subject_id=sub2_id,
            session_type=SessionType.THEORY,
            session_index=1,
            duration_periods=1,
            eligible_faculty_ids=(fac2_id,),
            eligible_room_ids=(classroom_id,),
        ),
        SessionRequirement(
            division_id=div_id,
            subject_id=sub2_id,
            session_type=SessionType.THEORY,
            session_index=2,
            duration_periods=1,
            eligible_faculty_ids=(fac2_id,),
            eligible_room_ids=(classroom_id,),
        ),
        SessionRequirement(
            division_id=div_id,
            subject_id=sub2_id,
            session_type=SessionType.PRACTICAL,
            session_index=0,
            duration_periods=2,
            eligible_faculty_ids=(fac2_id,),
            eligible_room_ids=(lab_id,),
        ),
    ]

    return SolverInput(
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


class TestModelBuilderAndValidator(unittest.TestCase):
    def test_solver_model_build_and_solve(self):
        solver_input = get_base_solver_input()
        builder = CPSATModelBuilder(solver_input)
        model = builder.build()

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        solver.parameters.num_search_workers = 4

        status = solver.Solve(model)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))

        requirements_by_key = {r.key: r for r in solver_input.requirements}
        assignments: list[AssignmentRecord] = []

        for key, var in builder.assignment_vars.items():
            if solver.Value(var) == 1:
                req = requirements_by_key[key.requirement_key]
                start_time, end_time = get_session_time_range(
                    key.start_period,
                    req.duration_periods,
                    solver_input.period_slots,
                )
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
                        start_time=start_time,
                        end_time=end_time,
                    )
                )

        # Validate generated timetable with 16 automated integrity checks
        metrics = validate_generated_timetable(
            solver_input=solver_input,
            assignments=assignments,
            period_slots=solver_input.period_slots,
        )

        self.assertTrue(metrics.is_valid)
        self.assertEqual(metrics.total_generated_sessions, len(solver_input.requirements))
        self.assertEqual(metrics.division_conflicts, 0)
        self.assertEqual(metrics.faculty_conflicts, 0)
        self.assertEqual(metrics.room_conflicts, 0)
        self.assertGreaterEqual(metrics.quality_score, 80.0)

        # Ensure NO practical session starts at period index 3 (12:00-14:00 across lunch)
        for a in assignments:
            if a.session_type == "PRACTICAL":
                self.assertNotEqual(a.period_index, 3, "Practical must NEVER cross lunch break (P4)")

    def test_validator_rejects_conflicts(self):
        solver_input = get_base_solver_input()
        div_id = list(solver_input.divisions.keys())[0]
        fac_ids = list(solver_input.faculty.keys())
        sub_ids = list(solver_input.subjects.keys())
        room_ids = list(solver_input.rooms.keys())

        invalid_assignments = [
            AssignmentRecord(
                requirement_key=solver_input.requirements[0].key,
                division_id=div_id,
                subject_id=sub_ids[0],
                faculty_id=fac_ids[0],
                room_id=room_ids[0],
                day="MONDAY",
                period_index=0,
                duration_periods=1,
                session_type="THEORY",
                start_time="09:00",
                end_time="10:00",
            ),
            # Overlapping period 0 on MONDAY for same division
            AssignmentRecord(
                requirement_key=solver_input.requirements[1].key,
                division_id=div_id,
                subject_id=sub_ids[1],
                faculty_id=fac_ids[1],
                room_id=room_ids[1],
                day="MONDAY",
                period_index=0,
                duration_periods=1,
                session_type="THEORY",
                start_time="09:00",
                end_time="10:00",
            ),
        ]

        with self.assertRaises(TimetableValidationError) as ctx:
            validate_generated_timetable(
                solver_input=solver_input,
                assignments=invalid_assignments,
                period_slots=solver_input.period_slots,
            )

        self.assertTrue(
            "simultaneous classes" in str(ctx.exception) or "Expected" in str(ctx.exception)
        )


if __name__ == "__main__":
    unittest.main()
