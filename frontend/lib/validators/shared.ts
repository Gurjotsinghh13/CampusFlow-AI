import { z } from "zod";

export function trimmedString() {
  return z.string().trim();
}
