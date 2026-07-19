"use client";

import * as React from "react";
import { type ColumnDef } from "@tanstack/react-table";
import { format } from "date-fns";
import { MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/data-table/data-table";
import { ConfirmDeleteDialog } from "@/components/data-table/confirm-delete-dialog";
import { AcademicYearFormDialog } from "@/components/modules/academic-year-form-dialog";
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
import type { AcademicYear } from "@/lib/types";

export default function AcademicYearsPage() {
  const { items, total, totalPages, page, setPage, search, setSearch, isLoading, create, update, remove } =
    useCrudResource<AcademicYear>("/academic-years");

  const [formOpen, setFormOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<AcademicYear | null>(null);
  const [deleteTarget, setDeleteTarget] = React.useState<AcademicYear | null>(null);
  const [isDeleting, setIsDeleting] = React.useState(false);

  async function handleDelete() {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await remove(deleteTarget.id);
      toast.success("Academic year deleted");
      setDeleteTarget(null);
    } catch (error) {
      toast.error(apiErrorMessage(error));
    } finally {
      setIsDeleting(false);
    }
  }

  const columns: ColumnDef<AcademicYear>[] = [
    { accessorKey: "label", header: "Label" },
    {
      accessorKey: "is_active",
      header: "Status",
      cell: ({ row }) => (
        <Badge variant={row.original.is_active ? "success" : "secondary"}>
          {row.original.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
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
        title="Academic Years"
        description="Academic calendar years, e.g. 2025-2026"
        action={
          <Button
            onClick={() => {
              setEditing(null);
              setFormOpen(true);
            }}
          >
            <Plus className="h-4 w-4" />
            Add Academic Year
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={items}
        isLoading={isLoading}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search academic years..."
        page={page}
        totalPages={totalPages}
        totalItems={total}
        onPageChange={setPage}
        emptyTitle="No academic years yet"
        emptyDescription="Add your first academic year to get started."
      />

      <AcademicYearFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        academicYear={editing}
        onCreate={create}
        onUpdate={update}
      />

      <ConfirmDeleteDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete academic year?"
        description={`This will permanently delete "${deleteTarget?.label}" and all its semesters, divisions, and subjects.`}
        onConfirm={handleDelete}
        isPending={isDeleting}
      />
    </div>
  );
}
