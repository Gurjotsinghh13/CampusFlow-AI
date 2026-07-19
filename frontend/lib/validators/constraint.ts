import { z } from "zod";

import { trimmedString } from "@/lib/validators/shared";

const TIME_RE = /^([01]\d|2[0-3]):[0-5]\d$/;

export const DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"] as const;

function timeToMinutes(value: string) {
  const [hours, minutes] = value.split(":").map(Number);
  return hours * 60 + minutes;
}

export const constraintFormSchema = z
  .object({
    working_days: z
      .array(z.enum(DAYS))
      .min(1, "Select at least one working day")
      .refine((value) => new Set(value).size === value.length, "Working days cannot contain duplicates"),
    college_start_time: trimmedString().regex(TIME_RE, "Use HH:MM 24-hour format"),
    college_end_time: trimmedString().regex(TIME_RE, "Use HH:MM 24-hour format"),
    lunch_break_start: trimmedString().regex(TIME_RE, "Use HH:MM 24-hour format"),
    lunch_break_end: trimmedString().regex(TIME_RE, "Use HH:MM 24-hour format"),
    number_of_periods: z.coerce.number().int().min(1).max(20),
    theory_duration_minutes: z.coerce.number().int().min(15).max(180),
    practical_duration_minutes: z.coerce.number().int().min(30).max(300),
  })
  .refine((data) => data.college_start_time < data.college_end_time, {
    message: "College start time must be before end time",
    path: ["college_end_time"],
  })
  .refine((data) => data.lunch_break_start < data.lunch_break_end, {
    message: "Lunch break start must be before its end",
    path: ["lunch_break_end"],
  })
  .refine(
    (data) => data.college_start_time <= data.lunch_break_start && data.lunch_break_end <= data.college_end_time,
    { message: "Lunch break must fall within college hours", path: ["lunch_break_start"] }
  )
  .refine(
    (data) => {
      const teachingMinutes =
        timeToMinutes(data.college_end_time) -
        timeToMinutes(data.college_start_time) -
        (timeToMinutes(data.lunch_break_end) - timeToMinutes(data.lunch_break_start));
      return data.number_of_periods * data.theory_duration_minutes <= teachingMinutes;
    },
    {
      message: "Periods and theory duration exceed available teaching time",
      path: ["number_of_periods"],
    }
  );

export type ConstraintFormValues = z.infer<typeof constraintFormSchema>;
