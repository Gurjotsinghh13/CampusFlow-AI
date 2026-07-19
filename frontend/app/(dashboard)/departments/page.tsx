"use client";

import * as React from "react";
import { type ColumnDef } from "@tanstack/react-table";
import { format } from "date-fns";
import { MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/data-table/data-table";
import { ConfirmDeleteDialog } from "@/components/data-table/confirm-delete-dialog";
import { DepartmentFormDialog } from "@/components/modules/department-form-dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCrudResource } from "@/hooks/use-crud-resource";
import { apiErrorMessage } from "@/lib/api-client";
import type { Department } from "@/lib/types";

export default function DepartmentsPage() {
  const { items, total, totalPages, page, setPage, search, setSearch, isLoading, create, update, remove } =
    useCrudResource<Department>("/departments");

  const [formOpen, setFormOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Department | null>(null);
  const [deleteTarget, setDeleteTarget] = React.useState<Department | null>(null);
  const [isDeleting, setIsDeleting] = React.useState(false);

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(dept: Department) {
    setEditing(dept);
    setFormOpen(true);
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await remove(deleteTarget.id);
      toast.success("Department deleted");
      setDeleteTarget(null);
    } catch (error) {
      toast.error(apiErrorMessage(error));
    } finally {
      setIsDeleting(false);
    }
  }

  const columns: ColumnDef<Department>[] = [
    { accessorKey: "name", header: "Name" },
    {
      accessorKey: "code",
      header: "Code",
      cell: ({ row }) => <Badge variant="secondary">{row.original.code}</Badge>,
    },
    {
      accessorKey: "created_at",
      header: "Created",
      cell: ({ row }) => format(new Date(row.original.created_at), "MMM d, yyyy"),
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
        title="Departments"
        description="Academic departments within your institution"
        action={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Add Department
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={items}
        isLoading={isLoading}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search departments..."
        page={page}
        totalPages={totalPages}
        totalItems={total}
        onPageChange={setPage}
        emptyTitle="No departments yet"
        emptyDescription="Add your first department to get started."
      />

      <DepartmentFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        department={editing}
        onCreate={create}
        onUpdate={update}
      />

      <ConfirmDeleteDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete department?"
        description={`This will permanently delete "${deleteTarget?.name}". Faculty, subjects, and divisions linked to it will also be removed.`}
        onConfirm={handleDelete}
        isPending={isDeleting}
      />
    </div>
  );
}
