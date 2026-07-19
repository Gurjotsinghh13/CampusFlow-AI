"use client";

import * as React from "react";
import { type ColumnDef } from "@tanstack/react-table";
import { MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/data-table/data-table";
import { ConfirmDeleteDialog } from "@/components/data-table/confirm-delete-dialog";
import { SubjectFormDialog } from "@/components/modules/subject-form-dialog";
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
import type { Department, Subject } from "@/lib/types";

export default function SubjectsPage() {
  const { items, total, totalPages, page, setPage, search, setSearch, isLoading, create, update, remove } =
    useCrudResource<Subject>("/subjects");

  const { items: departments } = useOptionsList<Department>("/departments");
  const departmentById = React.useMemo(() => new Map(departments.map((d) => [d.id, d])), [departments]);

  const [formOpen, setFormOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Subject | null>(null);
  const [deleteTarget, setDeleteTarget] = React.useState<Subject | null>(null);
  const [isDeleting, setIsDeleting] = React.useState(false);

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(subject: Subject) {
    setEditing(subject);
    setFormOpen(true);
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await remove(deleteTarget.id);
      toast.success("Subject deleted");
      setDeleteTarget(null);
    } catch (error) {
      toast.error(apiErrorMessage(error));
    } finally {
      setIsDeleting(false);
    }
  }

  const columns: ColumnDef<Subject>[] = [
    { accessorKey: "name", header: "Subject" },
    {
      accessorKey: "code",
      header: "Code",
      cell: ({ row }) => <Badge variant="secondary">{row.original.code}</Badge>,
    },
    {
      id: "department",
      header: "Department",
      cell: ({ row }) => departmentById.get(row.original.department_id)?.name ?? "-",
    },
    { accessorKey: "credits", header: "Credits" },
    {
      id: "hours",
      header: "Theory / Practical",
      cell: ({ row }) => `${row.original.theory_hours_per_week}h / ${row.original.practical_hours_per_week}h`,
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
        title="Subjects"
        description="Subjects taught within each department and semester"
        action={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Add Subject
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={items}
        isLoading={isLoading}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search subjects..."
        page={page}
        totalPages={totalPages}
        totalItems={total}
        onPageChange={setPage}
        emptyTitle="No subjects yet"
        emptyDescription="Add your first subject to get started."
      />

      <SubjectFormDialog open={formOpen} onOpenChange={setFormOpen} subject={editing} onCreate={create} onUpdate={update} />

      <ConfirmDeleteDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete subject?"
        description={`This will permanently delete "${deleteTarget?.name}".`}
        onConfirm={handleDelete}
        isPending={isDeleting}
      />
    </div>
  );
}
