"use client";

import { useEffect, useMemo } from "react";
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
import { divisionFormSchema, type DivisionFormValues } from "@/lib/validators/division";
import { useOptionsList } from "@/hooks/use-options-list";
import type { AcademicYear, Department, Division, Semester } from "@/lib/types";

interface DivisionFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  division: Division | null;
  onCreate: (values: DivisionFormValues) => Promise<unknown>;
  onUpdate: (id: string, values: DivisionFormValues) => Promise<unknown>;
}

export function DivisionFormDialog({ open, onOpenChange, division, onCreate, onUpdate }: DivisionFormDialogProps) {
  const isEditing = division !== null;
  const { items: departments } = useOptionsList<Department>("/departments");
  const { items: semesters } = useOptionsList<Semester>("/semesters");
  const { items: academicYears } = useOptionsList<AcademicYear>("/academic-years");

  const academicYearById = useMemo(() => new Map(academicYears.map((y) => [y.id, y])), [academicYears]);

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors, isSubmitting },
  } = useForm<DivisionFormValues>({
    resolver: zodResolver(divisionFormSchema),
    defaultValues: { name: "", student_count: 1, department_id: "", semester_id: "" },
  });

  useEffect(() => {
    if (open) {
      reset(
        division
          ? {
              name: division.name,
              student_count: division.student_count,
              department_id: division.department_id,
              semester_id: division.semester_id,
            }
          : { name: "", student_count: 1, department_id: "", semester_id: "" }
      );
    }
  }, [open, division, reset]);

  async function onSubmit(values: DivisionFormValues) {
    try {
      if (isEditing) {
        await onUpdate(division.id, values);
        toast.success("Division updated");
      } else {
        await onCreate(values);
        toast.success("Division created");
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
          <DialogTitle>{isEditing ? "Edit Division" : "New Division"}</DialogTitle>
          <DialogDescription>
            {isEditing ? "Update the division's details." : "Add a division to a department and semester."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label>Department</Label>
            <Controller
              control={control}
              name="department_id"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a department" />
                  </SelectTrigger>
                  <SelectContent>
                    {departments.map((d) => (
                      <SelectItem key={d.id} value={d.id}>
                        {d.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.department_id && <p className="text-xs text-destructive">{errors.department_id.message}</p>}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Semester</Label>
            <Controller
              control={control}
              name="semester_id"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a semester" />
                  </SelectTrigger>
                  <SelectContent>
                    {semesters.map((s) => {
                      const year = academicYearById.get(s.academic_year_id);
                      return (
                        <SelectItem key={s.id} value={s.id}>
                          {year ? `${year.label} - ` : ""}Semester {s.number}
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.semester_id && <p className="text-xs text-destructive">{errors.semester_id.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="name">Division Name</Label>
              <Input id="name" placeholder="A" {...register("name")} />
              {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="student_count">Student Count</Label>
              <Input id="student_count" type="number" min={1} {...register("student_count")} />
              {errors.student_count && <p className="text-xs text-destructive">{errors.student_count.message}</p>}
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isEditing ? "Save Changes" : "Create Division"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
