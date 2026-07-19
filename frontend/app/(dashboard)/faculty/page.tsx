"use client";

import * as React from "react";
import { type ColumnDef } from "@tanstack/react-table";
import { MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/data-table/data-table";
import { ConfirmDeleteDialog } from "@/components/data-table/confirm-delete-dialog";
import { FacultyFormDialog } from "@/components/modules/faculty-form-dialog";
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
import { apiErrorMessage, apiPut } from "@/lib/api-client";
import type { Department, Faculty } from "@/lib/types";

export default function FacultyPage() {
  const { items, total, totalPages, page, setPage, search, setSearch, isLoading, create, update, remove, refetch } =
    useCrudResource<Faculty>("/faculty");

  const { items: departments } = useOptionsList<Department>("/departments");
  const departmentById = React.useMemo(() => new Map(departments.map((d) => [d.id, d])), [departments]);

  const [formOpen, setFormOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Faculty | null>(null);
  const [deleteTarget, setDeleteTarget] = React.useState<Faculty | null>(null);
  const [isDeleting, setIsDeleting] = React.useState(false);

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(faculty: Faculty) {
    setEditing(faculty);
    setFormOpen(true);
  }

  async function assignSubjects(id: string, subjectIds: string[]) {
    const result = await apiPut<Faculty>(`/faculty/${id}/subjects`, { subject_ids: subjectIds });
    refetch();
    return result;
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await remove(deleteTarget.id);
      toast.success("Faculty deleted");
      setDeleteTarget(null);
    } catch (error) {
      toast.error(apiErrorMessage(error));
    } finally {
      setIsDeleting(false);
    }
  }

  const columns: ColumnDef<Faculty>[] = [
    { accessorKey: "full_name", header: "Faculty" },
    {
      accessorKey: "employee_id",
      header: "Employee ID",
      cell: ({ row }) => <span className="font-mono text-xs">{row.original.employee_id}</span>,
    },
    {
      id: "department",
      header: "Department",
      cell: ({ row }) => departmentById.get(row.original.department_id)?.name ?? "-",
    },
    {
      id: "subjects",
      header: "Subjects",
      cell: ({ row }) => (
        <div className="flex max-w-xs flex-wrap gap-1">
          {row.original.subjects.length === 0 ? (
            <span className="text-sm text-muted-foreground">None assigned</span>
          ) : (
            row.original.subjects.map((s) => (
              <Badge key={s.id} variant="secondary">
                {s.code}
              </Badge>
            ))
          )}
        </div>
      ),
    },
    {
      id: "workload",
      header: "Max Daily / Weekly",
      cell: ({ row }) => `${row.original.max_daily_lectures} / ${row.original.max_weekly_lectures}`,
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
        title="Faculty"
        description="Faculty members, their workload limits, and teachable subjects"
        action={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Add Faculty
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={items}
        isLoading={isLoading}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search faculty..."
        page={page}
        totalPages={totalPages}
        totalItems={total}
        onPageChange={setPage}
        emptyTitle="No faculty yet"
        emptyDescription="Add your first faculty member to get started."
      />

      <FacultyFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        faculty={editing}
        onCreate={create}
        onUpdate={update}
        onAssignSubjects={assignSubjects}
      />

      <ConfirmDeleteDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete faculty member?"
        description={`This will permanently delete "${deleteTarget?.full_name}".`}
        onConfirm={handleDelete}
        isPending={isDeleting}
      />
    </div>
  );
}
