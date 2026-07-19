"use client";

import * as React from "react";
import { type ColumnDef } from "@tanstack/react-table";
import { MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/data-table/data-table";
import { ConfirmDeleteDialog } from "@/components/data-table/confirm-delete-dialog";
import { RoomFormDialog } from "@/components/modules/room-form-dialog";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCrudResource } from "@/hooks/use-crud-resource";
import { apiErrorMessage } from "@/lib/api-client";
import type { Room, RoomType } from "@/lib/types";

interface RoomsPageContentProps {
  roomType: RoomType;
  title: string;
  description: string;
  entityLabel: string;
}

export function RoomsPageContent({ roomType, title, description, entityLabel }: RoomsPageContentProps) {
  const { items, total, totalPages, page, setPage, search, setSearch, isLoading, create, update, remove } =
    useCrudResource<Room>("/rooms", { extraParams: { room_type: roomType } });

  const [formOpen, setFormOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Room | null>(null);
  const [deleteTarget, setDeleteTarget] = React.useState<Room | null>(null);
  const [isDeleting, setIsDeleting] = React.useState(false);

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(room: Room) {
    setEditing(room);
    setFormOpen(true);
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await remove(deleteTarget.id);
      toast.success(`${entityLabel} deleted`);
      setDeleteTarget(null);
    } catch (error) {
      toast.error(apiErrorMessage(error));
    } finally {
      setIsDeleting(false);
    }
  }

  const columns: ColumnDef<Room>[] = [
    { accessorKey: "room_number", header: "Room Number" },
    { accessorKey: "capacity", header: "Capacity" },
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
        title={title}
        description={description}
        action={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Add {entityLabel}
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={items}
        isLoading={isLoading}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder={`Search ${entityLabel.toLowerCase()}s...`}
        page={page}
        totalPages={totalPages}
        totalItems={total}
        onPageChange={setPage}
        emptyTitle={`No ${entityLabel.toLowerCase()}s yet`}
        emptyDescription={`Add your first ${entityLabel.toLowerCase()} to get started.`}
      />

      <RoomFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        room={editing}
        roomType={roomType}
        entityLabel={entityLabel}
        onCreate={create}
        onUpdate={update}
      />

      <ConfirmDeleteDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title={`Delete ${entityLabel.toLowerCase()}?`}
        description={`This will permanently delete "${deleteTarget?.room_number}".`}
        onConfirm={handleDelete}
        isPending={isDeleting}
      />
    </div>
  );
}
