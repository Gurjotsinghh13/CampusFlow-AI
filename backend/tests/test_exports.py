import unittest
import uuid

from app.models.timetable import TimetableEntry
from app.services.export.excel_export import build_excel
from app.services.export.grid_builder import ViewType, build_grid
from app.services.export.pdf_export import build_pdf
from app.utils.timeline import compute_period_slots


class TestExports(unittest.TestCase):
    def test_grid_builder_with_timeline(self):
        slots = compute_period_slots(
            college_start_time="09:00",
            college_end_time="17:00",
            lunch_break_start="13:00",
            lunch_break_end="14:00",
            number_of_periods=7,
            theory_duration_minutes=60,
        )

        entries = [
            TimetableEntry(
                id=uuid.uuid4(),
                timetable_id=uuid.uuid4(),
                division_id=uuid.uuid4(),
                subject_id=uuid.uuid4(),
                faculty_id=uuid.uuid4(),
                room_id=uuid.uuid4(),
                day="MONDAY",
                period_index=0,
                session_type="THEORY",
                division_name="Div-A",
                subject_name="Data Structures",
                subject_code="CS201",
                faculty_name="Prof. Alan Turing",
                room_number="CR-101",
            ),
            TimetableEntry(
                id=uuid.uuid4(),
                timetable_id=uuid.uuid4(),
                division_id=uuid.uuid4(),
                subject_id=uuid.uuid4(),
                faculty_id=uuid.uuid4(),
                room_id=uuid.uuid4(),
                day="WEDNESDAY",
                period_index=4,  # 14:00
                session_type="PRACTICAL",
                division_name="Div-A",
                subject_name="Data Structures Lab",
                subject_code="CS201",
                faculty_name="Prof. Alan Turing",
                room_number="LAB-201",
            ),
        ]

        days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
        grid = build_grid(
            entries=entries,
            days=days,
            periods_per_day=7,
            view_type=ViewType.STUDENT,
            practical_block_periods=2,
            period_slots=slots,
        )

        # Check Monday period 0 (09:00-10:00)
        self.assertIn("09:00–10:00", grid["MONDAY"][0])
        self.assertIn("CS201 (T)", grid["MONDAY"][0])

        # Check Wednesday practical (14:00-16:00) spanning period 4 and period 5
        self.assertIn("14:00–16:00", grid["WEDNESDAY"][4])
        self.assertIn("14:00–16:00", grid["WEDNESDAY"][5])
        self.assertIn("CS201 (P)", grid["WEDNESDAY"][4])

    def test_pdf_export_generation(self):
        slots = compute_period_slots(
            college_start_time="09:00",
            college_end_time="17:00",
            lunch_break_start="13:00",
            lunch_break_end="14:00",
            number_of_periods=7,
            theory_duration_minutes=60,
        )
        days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
        grid = {day: [""] * 7 for day in days}
        grid["MONDAY"][0] = "CS201 (T)\n09:00–10:00\nProf. Alan Turing\nCR-101"

        pdf_bytes = build_pdf(
            title="Student Timetable - Division A",
            days=days,
            periods_per_day=7,
            period_slots=slots,
            grid=grid,
        )

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_excel_export_generation(self):
        slots = compute_period_slots(
            college_start_time="09:00",
            college_end_time="17:00",
            lunch_break_start="13:00",
            lunch_break_end="14:00",
            number_of_periods=7,
            theory_duration_minutes=60,
        )
        days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
        grid = {day: [""] * 7 for day in days}
        grid["MONDAY"][0] = "CS201 (T)\n09:00–10:00\nProf. Alan Turing\nCR-101"

        excel_bytes = build_excel(
            title="Student Timetable - Division A",
            days=days,
            periods_per_day=7,
            period_slots=slots,
            grid=grid,
        )

        self.assertIsInstance(excel_bytes, bytes)
        self.assertGreater(len(excel_bytes), 1000)


if __name__ == "__main__":
    unittest.main()
