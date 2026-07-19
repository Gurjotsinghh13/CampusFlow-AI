import { z } from "zod";

import { trimmedString } from "@/lib/validators/shared";

export const roomFormSchema = z.object({
  room_number: trimmedString().min(1, "Room number is required").max(20),
  capacity: z.coerce.number().int().min(1, "Must be at least 1").max(1000),
  room_type: z.enum(["CLASSROOM", "LAB"]),
});

export type RoomFormValues = z.infer<typeof roomFormSchema>;
