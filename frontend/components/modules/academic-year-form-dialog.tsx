"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiErrorMessage } from "@/lib/api-client";
import { academicYearFormSchema, type AcademicYearFormValues } from "@/lib/validators/academic-year";
import type { AcademicYear } from "@/lib/types";

interface AcademicYearFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  academicYear: AcademicYear | null;
  onCreate: (values: AcademicYearFormValues) => Promise<unknown>;
  onUpdate: (id: string, values: AcademicYearFormValues) => Promise<unknown>;
}

export function AcademicYearFormDialog({
  open,
  onOpenChange,
  academicYear,
  onCreate,
  onUpdate,
}: AcademicYearFormDialogProps) {
  const isEditing = academicYear !== null;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AcademicYearFormValues>({
    resolver: zodResolver(academicYearFormSchema),
    defaultValues: { label: "", is_active: true },
  });

  useEffect(() => {
    if (open) {
      reset(academicYear ? { label: academicYear.label, is_active: academicYear.is_active } : { label: "", is_active: true });
    }
  }, [open, academicYear, reset]);

  async function onSubmit(values: AcademicYearFormValues) {
    try {
      if (isEditing) {
        await onUpdate(academicYear.id, values);
        toast.success("Academic year updated");
      } else {
        await onCreate(values);
        toast.success("Academic year created");
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
          <DialogTitle>{isEditing ? "Edit Academic Year" : "New Academic Year"}</DialogTitle>
          <DialogDescription>
            {isEditing ? "Update the academic year's details." : "Add a new academic year, e.g. 2025-2026."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="label">Label</Label>
            <Input id="label" placeholder="2025-2026" {...register("label")} />
            {errors.label && <p className="text-xs text-destructive">{errors.label.message}</p>}
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" className="h-4 w-4 rounded border-input" {...register("is_active")} />
            Active
          </label>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isEditing ? "Save Changes" : "Create Academic Year"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
