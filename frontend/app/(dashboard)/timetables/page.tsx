"use client";

import * as React from "react";
import Link from "next/link";
import { type ColumnDef } from "@tanstack/react-table";
import { format } from "date-fns";
import { Eye, MoreHorizontal, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/data-table/data-table";
import { ConfirmDeleteDialog } from "@/components/data-table/confirm-delete-dialog";
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
import type { AcademicYear, GeneratedTimetable, GenerationStatus } from "@/lib/types";

const STATUS_VARIANT: Record<GenerationStatus, "success" | "destructive" | "secondary"> = {
  SUCCESS: "success",
  INFEASIBLE: "destructive",
  FAILED: "destructive",
  RUNNING: "secondary",
  PENDING: "secondary",
};

export default function GeneratedTimetablesPage() {
  const { items, total, totalPages, page, setPage, isLoading, remove } =
    useCrudResource<GeneratedTimetable>("/timetables");

  const { items: academicYears } = useOptionsList<AcademicYear>("/academic-years");
  const academicYearById = React.useMemo(() => new Map(academicYears.map((y) => [y.id, y])), [academicYears]);

  const [deleteTarget, setDeleteTarget] = React.useState<GeneratedTimetable | null>(null);
  const [isDeleting, setIsDeleting] = React.useState(false);

  async function handleDelete() {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await remove(deleteTarget.id);
      toast.success("Generated timetable deleted");
      setDeleteTarget(null);
    } catch (error) {
      toast.error(apiErrorMessage(error));
    } finally {
      setIsDeleting(false);
    }
  }

  const columns: ColumnDef<GeneratedTimetable>[] = [
    {
      id: "academic_year",
      header: "Academic Year",
      cell: ({ row }) =>
        row.original.academic_year_label || academicYearById.get(row.original.academic_year_id)?.label || "-",
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => <Badge variant={STATUS_VARIANT[row.original.status]}>{row.original.status}</Badge>,
    },
    {
      id: "wall_time",
      header: "Solve Time",
      cell: ({ row }) =>
        row.original.solver_wall_time_seconds != null ? `${row.original.solver_wall_time_seconds.toFixed(2)}s` : "-",
    },
    {
      accessorKey: "created_at",
      header: "Generated",
      cell: ({ row }) => format(new Date(row.original.created_at), "MMM d, yyyy h:mm a"),
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
              {row.original.status === "SUCCESS" && (
                <DropdownMenuItem asChild>
                  <Link href={`/timetables/${row.original.id}`}>
                    <Eye className="h-4 w-4" />
                    View
                  </Link>
                </DropdownMenuItem>
              )}
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
        title="Generated Timetables"
        description="History of every timetable generation run"
        action={
          <Button asChild>
            <Link href="/generate">Generate New</Link>
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
        emptyTitle="No timetables generated yet"
        emptyDescription="Head to Generate Timetable to run your first schedule."
      />

      <ConfirmDeleteDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete generated timetable?"
        description="This will permanently delete this timetable and all of its schedule entries."
        onConfirm={handleDelete}
        isPending={isDeleting}
      />
    </div>
  );
}
