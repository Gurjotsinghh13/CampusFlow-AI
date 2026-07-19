"use client";

import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiErrorMessage } from "@/lib/api-client";
import { semesterFormSchema, type SemesterFormValues } from "@/lib/validators/semester";
import { useOptionsList } from "@/hooks/use-options-list";
import type { AcademicYear, Semester } from "@/lib/types";

interface SemesterFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  semester: Semester | null;
  onCreate: (values: SemesterFormValues) => Promise<unknown>;
  onUpdate: (id: string, values: SemesterFormValues) => Promise<unknown>;
}

export function SemesterFormDialog({ open, onOpenChange, semester, onCreate, onUpdate }: SemesterFormDialogProps) {
  const isEditing = semester !== null;
  const { items: academicYears } = useOptionsList<AcademicYear>("/academic-years");

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors, isSubmitting },
  } = useForm<SemesterFormValues>({
    resolver: zodResolver(semesterFormSchema),
    defaultValues: { academic_year_id: "", number: 1 },
  });

  useEffect(() => {
    if (open) {
      reset(
        semester
          ? { academic_year_id: semester.academic_year_id, number: semester.number }
          : { academic_year_id: "", number: 1 }
      );
    }
  }, [open, semester, reset]);

  async function onSubmit(values: SemesterFormValues) {
    try {
      if (isEditing) {
        await onUpdate(semester.id, values);
        toast.success("Semester updated");
      } else {
        await onCreate(values);
        toast.success("Semester created");
      }
      onOpenChange(false);
    } catch (error) {
      toast.error(apiErrorMessage(error));
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit Semester" : "New Semester"}</DialogTitle>
          <DialogDescription>
            {isEditing ? "Update the semester's details." : "Add a semester to an academic year."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label>Academic Year</Label>
            <Controller
              control={control}
              name="academic_year_id"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select an academic year" />
                  </SelectTrigger>
                  <SelectContent>
                    {academicYears.map((y) => (
                      <SelectItem key={y.id} value={y.id}>
                        {y.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.academic_year_id && <p className="text-xs text-destructive">{errors.academic_year_id.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="number">Semester Number</Label>
            <Input id="number" type="number" min={1} max={12} {...register("number")} />
            {errors.number && <p className="text-xs text-destructive">{errors.number.message}</p>}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isEditing ? "Save Changes" : "Create Semester"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
