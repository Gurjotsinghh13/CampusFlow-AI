"use client";

import * as React from "react";
import { type ColumnDef } from "@tanstack/react-table";
import { MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/data-table/data-table";
import { ConfirmDeleteDialog } from "@/components/data-table/confirm-delete-dialog";
import { SemesterFormDialog } from "@/components/modules/semester-form-dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCrudResource } from "@/hooks/use-crud-resource";
import { useOptionsList } from "@/hooks/use-options-list";
import { apiErrorMessage } from "@/lib/api-client";
import type { AcademicYear, Semester } from "@/lib/types";

export default function SemestersPage() {
  const { items, total, totalPages, page, setPage, isLoading, create, update, remove } =
    useCrudResource<Semester>("/semesters");
  const { items: academicYears } = useOptionsList<AcademicYear>("/academic-years");
  const yearLabelById = React.useMemo(
    () => Object.fromEntries(academicYears.map((y) => [y.id, y.label])),
    [academicYears]
  );

  const [formOpen, setFormOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Semester | null>(null);
  const [deleteTarget, setDeleteTarget] = React.useState<Semester | null>(null);
  const [isDeleting, setIsDeleting] = React.useState(false);

  async function handleDelete() {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await remove(deleteTarget.id);
      toast.success("Semester deleted");
      setDeleteTarget(null);
    } catch (error) {
      toast.error(apiErrorMessage(error));
    } finally {
      setIsDeleting(false);
    }
  }

  const columns: ColumnDef<Semester>[] = [
    {
      accessorKey: "academic_year_id",
      header: "Academic Year",
      cell: ({ row }) => yearLabelById[row.original.academic_year_id] ?? "-",
    },
    {
      accessorKey: "number",
      header: "Semester",
      cell: ({ row }) => <Badge variant="secondary">Semester {row.original.number}</Badge>,
    },
    {
      id: "actions",
      header: "",
      cell: ({ row }) => (
        <div className="flex justify-end">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => {
                  setEditing(row.original);
                  setFormOpen(true);
                }}
              >
                <Pencil className="h-4 w-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem destructive onClick={() => setDeleteTarget(row.original)}>
                <Trash2 className="h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Semesters"
        description="Semesters within each academic year"
        action={
          <Button
            onClick={() => {
              setEditing(null);
              setFormOpen(true);
            }}
          >
            <Plus className="h-4 w-4" />
            Add Semester
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={items}
        isLoading={isLoading}
        page={page}
        totalPages={totalPages}
        totalItems={total}
        onPageChange={setPage}
        emptyTitle="No semesters yet"
        emptyDescription="Add your first semester to get started."
      />

      <SemesterFormDialog open={formOpen} onOpenChange={setFormOpen} semester={editing} onCreate={create} onUpdate={update} />

      <ConfirmDeleteDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete semester?"
        description="This will permanently delete this semester and all its divisions and subjects."
        onConfirm={handleDelete}
        isPending={isDeleting}
      />
    </div>
  );
}
