import { z } from "zod";

import { trimmedString } from "@/lib/validators/shared";

export const departmentFormSchema = z.object({
  name: trimmedString().min(2, "Name must be at least 2 characters").max(150),
  code: trimmedString().min(2, "Code must be at least 2 characters").max(20),
});

export type DepartmentFormValues = z.infer<typeof departmentFormSchema>;
