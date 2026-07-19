import { z } from "zod";

import { trimmedString } from "@/lib/validators/shared";

export const divisionFormSchema = z.object({
  name: trimmedString().min(1, "Division name is required").max(20, "Keep it under 20 characters"),
  student_count: z.coerce.number().int().min(1, "Enter at least one student"),
  department_id: z.string().uuid("Select a department"),
  semester_id: z.string().uuid("Select a semester"),
});

export type DivisionFormValues = z.infer<typeof divisionFormSchema>;
