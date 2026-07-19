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
import { departmentFormSchema, type DepartmentFormValues } from "@/lib/validators/department";
import type { Department } from "@/lib/types";

interface DepartmentFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  department: Department | null;
  onCreate: (values: DepartmentFormValues) => Promise<unknown>;
  onUpdate: (id: string, values: DepartmentFormValues) => Promise<unknown>;
}

export function DepartmentFormDialog({
  open,
  onOpenChange,
  department,
  onCreate,
  onUpdate,
}: DepartmentFormDialogProps) {
  const isEditing = department !== null;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<DepartmentFormValues>({
    resolver: zodResolver(departmentFormSchema),
    defaultValues: { name: "", code: "" },
  });

  useEffect(() => {
    if (open) {
      reset(department ? { name: department.name, code: department.code } : { name: "", code: "" });
    }
  }, [open, department, reset]);

  async function onSubmit(values: DepartmentFormValues) {
    try {
      if (isEditing) {
        await onUpdate(department.id, values);
        toast.success("Department updated");
      } else {
        await onCreate(values);
        toast.success("Department created");
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
          <DialogTitle>{isEditing ? "Edit Department" : "New Department"}</DialogTitle>
          <DialogDescription>
            {isEditing ? "Update the department's details." : "Add a new academic department."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Department Name</Label>
            <Input id="name" placeholder="Computer Engineering" {...register("name")} />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="code">Department Code</Label>
            <Input id="code" placeholder="CE" {...register("code")} />
            {errors.code && <p className="text-xs text-destructive">{errors.code.message}</p>}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isEditing ? "Save Changes" : "Create Department"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
