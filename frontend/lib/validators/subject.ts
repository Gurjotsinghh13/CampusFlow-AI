import { z } from "zod";

import { trimmedString } from "@/lib/validators/shared";

export const subjectFormSchema = z
  .object({
    name: trimmedString().min(2, "Subject name is required").max(150),
    code: trimmedString().min(2, "Subject code is required").max(20),
    credits: z.coerce.number().int().min(1).max(10),
    theory_hours_per_week: z.coerce.number().int().min(0).max(20),
    practical_hours_per_week: z.coerce.number().int().min(0).max(20),
    semester_id: z.string().uuid("Select a semester"),
    department_id: z.string().uuid("Select a department"),
  })
  .refine((value) => value.theory_hours_per_week + value.practical_hours_per_week > 0, {
    message: "Add at least one theory or practical hour per week",
    path: ["theory_hours_per_week"],
  });

export type SubjectFormValues = z.infer<typeof subjectFormSchema>;
