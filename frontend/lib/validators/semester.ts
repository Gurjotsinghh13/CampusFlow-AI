import { z } from "zod";

export const semesterFormSchema = z.object({
  academic_year_id: z.string().uuid("Select an academic year"),
  number: z.coerce.number().int().min(1, "Must be at least 1").max(12, "Must be at most 12"),
});

export type SemesterFormValues = z.infer<typeof semesterFormSchema>;
