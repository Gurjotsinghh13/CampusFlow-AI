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
import { subjectFormSchema, type SubjectFormValues } from "@/lib/validators/subject";
import { useOptionsList } from "@/hooks/use-options-list";
import type { AcademicYear, Department, Semester, Subject } from "@/lib/types";

interface SubjectFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  subject: Subject | null;
  onCreate: (values: SubjectFormValues) => Promise<unknown>;
  onUpdate: (id: string, values: SubjectFormValues) => Promise<unknown>;
}

export function SubjectFormDialog({ open, onOpenChange, subject, onCreate, onUpdate }: SubjectFormDialogProps) {
  const isEditing = subject !== null;
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
  } = useForm<SubjectFormValues>({
    resolver: zodResolver(subjectFormSchema),
    defaultValues: {
      name: "",
      code: "",
      credits: 3,
      theory_hours_per_week: 3,
      practical_hours_per_week: 0,
      semester_id: "",
      department_id: "",
    },
  });

  useEffect(() => {
    if (open) {
      reset(
        subject
          ? {
              name: subject.name,
              code: subject.code,
              credits: subject.credits,
              theory_hours_per_week: subject.theory_hours_per_week,
              practical_hours_per_week: subject.practical_hours_per_week,
              semester_id: subject.semester_id,
              department_id: subject.department_id,
            }
          : {
              name: "",
              code: "",
              credits: 3,
              theory_hours_per_week: 3,
              practical_hours_per_week: 0,
              semester_id: "",
              department_id: "",
            }
      );
    }
  }, [open, subject, reset]);

  async function onSubmit(values: SubjectFormValues) {
    try {
      if (isEditing) {
        await onUpdate(subject.id, values);
        toast.success("Subject updated");
      } else {
        await onCreate(values);
        toast.success("Subject created");
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
          <DialogTitle>{isEditing ? "Edit Subject" : "New Subject"}</DialogTitle>
          <DialogDescription>
            {isEditing ? "Update the subject's details." : "Add a subject to a semester and department."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="name">Subject Name</Label>
              <Input id="name" placeholder="Data Structures" {...register("name")} />
              {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="code">Subject Code</Label>
              <Input id="code" placeholder="CS201" {...register("code")} />
              {errors.code && <p className="text-xs text-destructive">{errors.code.message}</p>}
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

          <div className="grid grid-cols-3 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="credits">Credits</Label>
              <Input id="credits" type="number" min={1} max={10} {...register("credits")} />
              {errors.credits && <p className="text-xs text-destructive">{errors.credits.message}</p>}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="theory_hours_per_week">Theory Hrs/Wk</Label>
              <Input id="theory_hours_per_week" type="number" min={0} max={20} {...register("theory_hours_per_week")} />
              {errors.theory_hours_per_week && (
                <p className="text-xs text-destructive">{errors.theory_hours_per_week.message}</p>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="practical_hours_per_week">Practical Hrs/Wk</Label>
              <Input
                id="practical_hours_per_week"
                type="number"
                min={0}
                max={20}
                {...register("practical_hours_per_week")}
              />
              {errors.practical_hours_per_week && (
                <p className="text-xs text-destructive">{errors.practical_hours_per_week.message}</p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isEditing ? "Save Changes" : "Create Subject"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
