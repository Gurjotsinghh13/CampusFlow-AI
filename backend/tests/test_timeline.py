import unittest

from app.utils.timeline import (
    compute_period_slots,
    get_session_time_range,
    get_valid_start_periods_for_duration,
    is_block_continuous,
    minutes_to_time,
    time_to_minutes,
)


class TestTimeline(unittest.TestCase):
    def test_time_conversions(self):
        self.assertEqual(time_to_minutes("09:00"), 540)
        self.assertEqual(time_to_minutes("13:00"), 780)
        self.assertEqual(time_to_minutes("14:00"), 840)
        self.assertEqual(time_to_minutes("17:00"), 1020)

        self.assertEqual(minutes_to_time(540), "09:00")
        self.assertEqual(minutes_to_time(780), "13:00")
        self.assertEqual(minutes_to_time(840), "14:00")
        self.assertEqual(minutes_to_time(1020), "17:00")

    def test_compute_period_slots_standard_day(self):
        # 09:00 to 17:00, 7 periods of 60 mins, lunch 13:00-14:00
        slots = compute_period_slots(
            college_start_time="09:00",
            college_end_time="17:00",
            lunch_break_start="13:00",
            lunch_break_end="14:00",
            number_of_periods=7,
            theory_duration_minutes=60,
        )

        self.assertEqual(len(slots), 7)
        # Morning periods: P1..P4
        self.assertEqual(slots[0].period_index, 0)
        self.assertEqual(slots[0].start_time, "09:00")
        self.assertEqual(slots[0].end_time, "10:00")
        self.assertTrue(slots[0].is_before_lunch)

        self.assertEqual(slots[1].period_index, 1)
        self.assertEqual(slots[1].start_time, "10:00")
        self.assertEqual(slots[1].end_time, "11:00")

        self.assertEqual(slots[2].period_index, 2)
        self.assertEqual(slots[2].start_time, "11:00")
        self.assertEqual(slots[2].end_time, "12:00")

        self.assertEqual(slots[3].period_index, 3)
        self.assertEqual(slots[3].start_time, "12:00")
        self.assertEqual(slots[3].end_time, "13:00")
        self.assertTrue(slots[3].is_before_lunch)
        self.assertFalse(slots[3].is_after_lunch)

        # Afternoon periods: P5..P7
        self.assertEqual(slots[4].period_index, 4)
        self.assertEqual(slots[4].start_time, "14:00")
        self.assertEqual(slots[4].end_time, "15:00")
        self.assertFalse(slots[4].is_before_lunch)
        self.assertTrue(slots[4].is_after_lunch)

        self.assertEqual(slots[5].period_index, 5)
        self.assertEqual(slots[5].start_time, "15:00")
        self.assertEqual(slots[5].end_time, "16:00")

        self.assertEqual(slots[6].period_index, 6)
        self.assertEqual(slots[6].start_time, "16:00")
        self.assertEqual(slots[6].end_time, "17:00")

    def test_continuity_and_lunch_crossing(self):
        slots = compute_period_slots(
            college_start_time="09:00",
            college_end_time="17:00",
            lunch_break_start="13:00",
            lunch_break_end="14:00",
            number_of_periods=7,
            theory_duration_minutes=60,
        )

        # 1-period sessions are always continuous
        self.assertTrue(is_block_continuous(0, 1, slots))
        self.assertTrue(is_block_continuous(3, 1, slots))
        self.assertTrue(is_block_continuous(4, 1, slots))

        # 2-period practicals in morning:
        self.assertTrue(is_block_continuous(0, 2, slots))
        self.assertTrue(is_block_continuous(1, 2, slots))
        self.assertTrue(is_block_continuous(2, 2, slots))

        # P4+P5 (12:00-13:00 and 14:00-15:00) -> CROSSES LUNCH -> MUST BE FALSE!
        self.assertFalse(is_block_continuous(3, 2, slots))

        # 2-period practicals in afternoon:
        self.assertTrue(is_block_continuous(4, 2, slots))
        self.assertTrue(is_block_continuous(5, 2, slots))

        # Out of bounds
        self.assertFalse(is_block_continuous(6, 2, slots))

    def test_get_valid_start_periods_for_duration(self):
        slots = compute_period_slots(
            college_start_time="09:00",
            college_end_time="17:00",
            lunch_break_start="13:00",
            lunch_break_end="14:00",
            number_of_periods=7,
            theory_duration_minutes=60,
        )

        valid_2_period_starts = get_valid_start_periods_for_duration(2, slots)
        self.assertEqual(valid_2_period_starts, [0, 1, 2, 4, 5])

    def test_get_session_time_range(self):
        slots = compute_period_slots(
            college_start_time="09:00",
            college_end_time="17:00",
            lunch_break_start="13:00",
            lunch_break_end="14:00",
            number_of_periods=7,
            theory_duration_minutes=60,
        )

        start, end = get_session_time_range(0, 1, slots)
        self.assertEqual(start, "09:00")
        self.assertEqual(end, "10:00")

        start, end = get_session_time_range(4, 2, slots)
        self.assertEqual(start, "14:00")
        self.assertEqual(end, "16:00")


if __name__ == "__main__":
    unittest.main()
