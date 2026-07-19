"use client";

import { useMemo } from "react";

import { cn } from "@/lib/utils";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { TimetableEntry } from "@/lib/types";

export type GridViewType = "STUDENT" | "FACULTY" | "ROOM";

interface TimetableGridProps {
  entries: TimetableEntry[];
  days: string[];
  periodsPerDay: number;
  practicalBlockPeriods: number;
  viewType: GridViewType;
}

export function TimetableGrid({
  entries,
  days,
  periodsPerDay,
  practicalBlockPeriods,
  viewType,
}: TimetableGridProps) {
  const entriesByCell = useMemo(() => {
    const index = new Map<string, TimetableEntry[]>();
    for (const entry of entries) {
      const span = entry.session_type === "PRACTICAL" ? practicalBlockPeriods : 1;
      for (let offset = 0; offset < span; offset += 1) {
        const period = entry.period_index + offset;
        if (period < 0 || period >= periodsPerDay) continue;
        const key = `${entry.day}:${period}`;
        const existing = index.get(key);
        if (existing) {
          existing.push(entry);
        } else {
          index.set(key, [entry]);
        }
      }
    }
    return index;
  }, [entries, periodsPerDay, practicalBlockPeriods]);

  function cellEntriesFor(day: string, period: number) {
    return entriesByCell.get(`${day}:${period}`) ?? [];
  }

  function entryContent(entry: TimetableEntry) {
    const abbrev = entry.session_type === "PRACTICAL" ? "P" : "T";

    const secondaryLines =
      viewType === "STUDENT"
        ? [entry.faculty_name, entry.room_number]
        : viewType === "FACULTY"
          ? [entry.division_name, entry.room_number]
          : [entry.division_name, entry.faculty_name];

    return (
      <div className="flex flex-col gap-0.5">
        <span className="text-xs font-semibold">
          {entry.subject_code} <span className="font-normal text-muted-foreground">({abbrev})</span>
        </span>
        {secondaryLines.filter(Boolean).map((line, i) => (
          <span key={i} className="text-xs text-muted-foreground">
            {line}
          </span>
        ))}
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-28">Day / Period</TableHead>
            {Array.from({ length: periodsPerDay }).map((_, i) => (
              <TableHead key={i} className="text-center">
                P{i + 1}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {days.map((day) => (
            <TableRow key={day}>
              <TableCell className="font-medium">{day.charAt(0) + day.slice(1).toLowerCase()}</TableCell>
              {Array.from({ length: periodsPerDay }).map((_, period) => (
                <TableCell key={period} className={cn("min-w-[140px] align-top")}>
                  <div className="flex flex-col gap-3">
                    {cellEntriesFor(day, period).map((entry) => (
                      <div key={entry.id}>{entryContent(entry)}</div>
                    ))}
                  </div>
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
