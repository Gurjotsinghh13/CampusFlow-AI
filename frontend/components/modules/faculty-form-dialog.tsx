"use client";

import { useEffect, useMemo } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MultiSelectChecklist } from "@/components/ui/multi-select-checklist";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiErrorMessage } from "@/lib/api-client";
import { facultyFormSchema, type FacultyFormValues } from "@/lib/validators/faculty";
import { useOptionsList } from "@/hooks/use-options-list";
import type { Department, Faculty, Subject } from "@/lib/types";

interface FacultyFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  faculty: Faculty | null;
  onCreate: (values: FacultyFormValues) => Promise<unknown>;
  onUpdate: (id: string, values: Omit<FacultyFormValues, "subject_ids">) => Promise<unknown>;
  onAssignSubjects: (id: string, subjectIds: string[]) => Promise<unknown>;
}

export function FacultyFormDialog({
  open,
  onOpenChange,
  faculty,
  onCreate,
  onUpdate,
  onAssignSubjects,
}: FacultyFormDialogProps) {
  const isEditing = faculty !== null;
  const { items: departments } = useOptionsList<Department>("/departments");
  const { items: subjects } = useOptionsList<Subject>("/subjects");

  const {
    register,
    handleSubmit,
    reset,
    control,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FacultyFormValues>({
    resolver: zodResolver(facultyFormSchema),
    defaultValues: {
      full_name: "",
      employee_id: "",
      max_daily_lectures: 4,
      max_weekly_lectures: 20,
      department_id: "",
      subject_ids: [],
    },
  });

  useEffect(() => {
    if (open) {
      reset(
        faculty
          ? {
              full_name: faculty.full_name,
              employee_id: faculty.employee_id,
              max_daily_lectures: faculty.max_daily_lectures,
              max_weekly_lectures: faculty.max_weekly_lectures,
              department_id: faculty.department_id,
              subject_ids: faculty.subjects.map((s) => s.id),
            }
          : {
              full_name: "",
              employee_id: "",
              max_daily_lectures: 4,
              max_weekly_lectures: 20,
              department_id: "",
              subject_ids: [],
            }
      );
    }
  }, [open, faculty, reset]);

  const selectedDepartmentId = useWatch({ control, name: "department_id" });
  const selectedSubjectIds = useWatch({ control, name: "subject_ids" });
  const departmentSubjects = useMemo(
    () => subjects.filter((subject) => subject.department_id === selectedDepartmentId),
    [subjects, selectedDepartmentId]
  );

  useEffect(() => {
    if (!selectedDepartmentId || selectedSubjectIds.length === 0) return;
    const validSubjectIds = new Set(departmentSubjects.map((subject) => subject.id));
    const nextSubjectIds = selectedSubjectIds.filter((id) => validSubjectIds.has(id));
    if (nextSubjectIds.length !== selectedSubjectIds.length) {
      setValue("subject_ids", nextSubjectIds, { shouldDirty: true, shouldValidate: true });
    }
  }, [departmentSubjects, selectedDepartmentId, selectedSubjectIds, setValue]);

  async function onSubmit(values: FacultyFormValues) {
    try {
      if (isEditing) {
        const { subject_ids, ...baseFields } = values;
        await onUpdate(faculty.id, baseFields);
        await onAssignSubjects(faculty.id, subject_ids);
        toast.success("Faculty updated");
      } else {
        await onCreate(values);
        toast.success("Faculty created");
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
          <DialogTitle>{isEditing ? "Edit Faculty" : "New Faculty"}</DialogTitle>
          <DialogDescription>
            {isEditing ? "Update this faculty member's details." : "Add a faculty member and their teachable subjects."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="full_name">Full Name</Label>
              <Input id="full_name" placeholder="Dr. Jane Smith" {...register("full_name")} />
              {errors.full_name && <p className="text-xs text-destructive">{errors.full_name.message}</p>}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="employee_id">Employee ID</Label>
              <Input id="employee_id" placeholder="EMP-1042" {...register("employee_id")} />
              {errors.employee_id && <p className="text-xs text-destructive">{errors.employee_id.message}</p>}
            </div>
          </div>

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

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="max_daily_lectures">Max Daily Lectures</Label>
              <Input id="max_daily_lectures" type="number" min={1} max={12} {...register("max_daily_lectures")} />
              {errors.max_daily_lectures && (
                <p className="text-xs text-destructive">{errors.max_daily_lectures.message}</p>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="max_weekly_lectures">Max Weekly Lectures</Label>
              <Input id="max_weekly_lectures" type="number" min={1} max={60} {...register("max_weekly_lectures")} />
              {errors.max_weekly_lectures && (
                <p className="text-xs text-destructive">{errors.max_weekly_lectures.message}</p>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Subjects They Can Teach</Label>
            <Controller
              control={control}
              name="subject_ids"
              render={({ field }) => (
                <MultiSelectChecklist
                  options={departmentSubjects.map((s) => ({ value: s.id, label: s.name, hint: s.code }))}
                  selected={field.value}
                  onChange={field.onChange}
                  emptyText={
                    selectedDepartmentId
                      ? "No subjects available for this department"
                      : "Select a department to choose subjects"
                  }
                />
              )}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isEditing ? "Save Changes" : "Create Faculty"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
