"use client";

import { useMemo } from "react";

import { cn } from "@/lib/utils";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { PeriodSlot, TimetableEntry } from "@/lib/types";

export type GridViewType = "STUDENT" | "FACULTY" | "ROOM";

interface TimetableGridProps {
  entries: TimetableEntry[];
  days: string[];
  periodsPerDay: number;
  practicalBlockPeriods: number;
  viewType: GridViewType;
  periodSlots?: PeriodSlot[];
}

export function TimetableGrid({
  entries,
  days,
  periodsPerDay,
  practicalBlockPeriods,
  viewType,
  periodSlots,
}: TimetableGridProps) {
  const slotsMap = useMemo(() => {
    const map = new Map<number, PeriodSlot>();
    if (periodSlots) {
      for (const slot of periodSlots) {
        map.set(slot.period_index, slot);
      }
    }
    return map;
  }, [periodSlots]);

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
    const isPractical = entry.session_type === "PRACTICAL";
    const abbrev = isPractical ? "P" : "T";

    const secondaryLines =
      viewType === "STUDENT"
        ? [entry.faculty_name, entry.room_number]
        : viewType === "FACULTY"
          ? [entry.division_name, entry.room_number]
          : [entry.division_name, entry.faculty_name];

    const sessionTime =
      entry.start_time && entry.end_time
        ? `${entry.start_time} – ${entry.end_time}`
        : slotsMap.has(entry.period_index)
          ? `${slotsMap.get(entry.period_index)?.start_time} – ${slotsMap.get(entry.period_index)?.end_time}`
          : null;

    return (
      <div
        className={cn(
          "flex flex-col gap-1 rounded-md border p-2 text-left transition-colors shadow-xs",
          isPractical
            ? "border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"
            : "border-slate-200 bg-slate-50/70 dark:border-slate-800 dark:bg-slate-900/40"
        )}
      >
        <div className="flex items-center justify-between gap-1">
          <span className="font-semibold text-xs text-foreground tracking-tight">
            {entry.subject_code}
          </span>
          <span
            className={cn(
              "rounded px-1.5 py-0.2 text-[10px] font-semibold uppercase tracking-wider",
              isPractical
                ? "bg-amber-200/70 text-amber-900 dark:bg-amber-900/60 dark:text-amber-200"
                : "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200"
            )}
          >
            {abbrev}
          </span>
        </div>

        {sessionTime && (
          <span className="text-[11px] font-medium text-emerald-700 dark:text-emerald-400">
            {sessionTime}
          </span>
        )}

        <div className="flex flex-col text-[11px] text-muted-foreground leading-tight">
          {secondaryLines.filter(Boolean).map((line, i) => (
            <span key={i} className="truncate">
              {line}
            </span>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-card overflow-x-auto shadow-xs">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/40 hover:bg-muted/40">
            <TableHead className="w-32 font-semibold text-foreground py-3">DAY / TIME</TableHead>
            {Array.from({ length: periodsPerDay }).map((_, i) => {
              const slot = slotsMap.get(i);
              return (
                <TableHead key={i} className="text-center py-2.5 px-2 min-w-[150px]">
                  <div className="flex flex-col items-center justify-center gap-0.5">
                    <span className="font-bold text-xs text-foreground tracking-wide">
                      {slot?.label ?? `P${i + 1}`}
                    </span>
                    {slot && (
                      <span className="text-[11px] font-normal text-muted-foreground">
                        {slot.start_time} – {slot.end_time}
                      </span>
                    )}
                  </div>
                </TableHead>
              );
            })}
          </TableRow>
        </TableHeader>
        <TableBody>
          {days.map((day) => (
            <TableRow key={day} className="hover:bg-muted/20">
              <TableCell className="font-semibold text-xs text-foreground align-middle bg-muted/10">
                {day.charAt(0) + day.slice(1).toLowerCase()}
              </TableCell>
              {Array.from({ length: periodsPerDay }).map((_, period) => (
                <TableCell key={period} className="min-w-[150px] p-2 align-top">
                  <div className="flex flex-col gap-2">
                    {cellEntriesFor(day, period).map((entry) => (
                      <div key={`${entry.id}-${period}`}>{entryContent(entry)}</div>
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
