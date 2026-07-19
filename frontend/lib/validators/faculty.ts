import { z } from "zod";

import { trimmedString } from "@/lib/validators/shared";

export const facultyFormSchema = z.object({
  full_name: trimmedString().min(2, "Full name is required").max(150),
  employee_id: trimmedString().min(2, "Employee ID is required").max(30),
  max_daily_lectures: z.coerce.number().int().min(1).max(12),
  max_weekly_lectures: z.coerce.number().int().min(1).max(60),
  department_id: z.string().uuid("Select a department"),
  subject_ids: z.array(z.string().uuid()).default([]),
});

export type FacultyFormValues = z.infer<typeof facultyFormSchema>;
