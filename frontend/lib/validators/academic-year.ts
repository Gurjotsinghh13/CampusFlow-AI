import { z } from "zod";

import { trimmedString } from "@/lib/validators/shared";

export const academicYearFormSchema = z
  .object({
    label: trimmedString()
      .length(9, "Use a format like 2025-2026")
      .regex(/^\d{4}-\d{4}$/, "Use a format like 2025-2026"),
    is_active: z.boolean(),
  })
  .refine(
    (value) => {
      const [startYear, endYear] = value.label.split("-").map(Number);
      return endYear === startYear + 1;
    },
    {
      message: "Academic year must span exactly one year",
      path: ["label"],
    }
  );

export type AcademicYearFormValues = z.infer<typeof academicYearFormSchema>;
