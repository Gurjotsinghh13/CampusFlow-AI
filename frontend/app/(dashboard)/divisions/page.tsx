"use client";

import * as React from "react";
import { type ColumnDef } from "@tanstack/react-table";
import { MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/data-table/data-table";
import { ConfirmDeleteDialog } from "@/components/data-table/confirm-delete-dialog";
import { DivisionFormDialog } from "@/components/modules/division-form-dialog";
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
import type { AcademicYear, Department, Division, Semester } from "@/lib/types";

export default function DivisionsPage() {
  const { items, total, totalPages, page, setPage, search, setSearch, isLoading, create, update, remove } =
    useCrudResource<Division>("/divisions");

  const { items: departments } = useOptionsList<Department>("/departments");
  const { items: semesters } = useOptionsList<Semester>("/semesters");
  const { items: academicYears } = useOptionsList<AcademicYear>("/academic-years");

  const departmentById = React.useMemo(() => new Map(departments.map((d) => [d.id, d])), [departments]);
  const semesterById = React.useMemo(() => new Map(semesters.map((s) => [s.id, s])), [semesters]);
  const academicYearById = React.useMemo(() => new Map(academicYears.map((y) => [y.id, y])), [academicYears]);

  const [formOpen, setFormOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Division | null>(null);
  const [deleteTarget, setDeleteTarget] = React.useState<Division | null>(null);
  const [isDeleting, setIsDeleting] = React.useState(false);

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(division: Division) {
    setEditing(division);
    setFormOpen(true);
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await remove(deleteTarget.id);
      toast.success("Division deleted");
      setDeleteTarget(null);
    } catch (error) {
      toast.error(apiErrorMessage(error));
    } finally {
      setIsDeleting(false);
    }
  }

  const columns: ColumnDef<Division>[] = [
    { accessorKey: "name", header: "Division" },
    {
      id: "department",
      header: "Department",
      cell: ({ row }) => departmentById.get(row.original.department_id)?.name ?? "-",
    },
    {
      id: "semester",
      header: "Semester",
      cell: ({ row }) => {
        const sem = semesterById.get(row.original.semester_id);
        const year = sem ? academicYearById.get(sem.academic_year_id) : undefined;
        return sem ? (
          <Badge variant="secondary">
            {year ? `${year.label} - ` : ""}Sem {sem.number}
          </Badge>
        ) : (
          "-"
        );
      },
    },
    { accessorKey: "student_count", header: "Students" },
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
              <DropdownMenuItem onClick={() => openEdit(row.original)}>
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
        title="Divisions"
        description="Student divisions within each department and semester"
        action={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Add Division
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={items}
        isLoading={isLoading}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search divisions..."
        page={page}
        totalPages={totalPages}
        totalItems={total}
        onPageChange={setPage}
        emptyTitle="No divisions yet"
        emptyDescription="Add your first division to get started."
      />

      <DivisionFormDialog open={formOpen} onOpenChange={setFormOpen} division={editing} onCreate={create} onUpdate={update} />

      <ConfirmDeleteDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete division?"
        description={`This will permanently delete division "${deleteTarget?.name}".`}
        onConfirm={handleDelete}
        isPending={isDeleting}
      />
    </div>
  );
}
