"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { toast } from "sonner";
import { Download, FileSpreadsheet, FileText } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TimetableGrid } from "@/components/modules/timetable-grid";
import { useOptionsList } from "@/hooks/use-options-list";
import { apiDownload, apiErrorMessage, apiGet } from "@/lib/api-client";
import { triggerBlobDownload } from "@/lib/download";
import type { GeneratedTimetable, Room, TimetableEntry } from "@/lib/types";

type TabKey = "student" | "faculty" | "classroom" | "laboratory";

export default function TimetableDetailPage() {
  const params = useParams<{ id: string }>();
  const timetableId = params.id;

  const [timetable, setTimetable] = React.useState<GeneratedTimetable | null>(null);
  const [tab, setTab] = React.useState<TabKey>("student");
  const [divisionId, setDivisionId] = React.useState<string>("");
  const [facultyId, setFacultyId] = React.useState<string>("");
  const [roomId, setRoomId] = React.useState<string>("");
  const [allEntries, setAllEntries] = React.useState<TimetableEntry[]>([]);
  const [isLoadingEntries, setIsLoadingEntries] = React.useState(false);
  const [isExporting, setIsExporting] = React.useState<"pdf" | "excel" | null>(null);

  const { items: rooms } = useOptionsList<Room>("/rooms");

  const roomById = React.useMemo(() => new Map(rooms.map((r) => [r.id, r])), [rooms]);
  const divisionOptions = React.useMemo(
    () => uniqueEntryOptions(allEntries, "division_id", "division_name"),
    [allEntries]
  );
  const facultyOptions = React.useMemo(
    () => uniqueEntryOptions(allEntries, "faculty_id", "faculty_name"),
    [allEntries]
  );
  const classroomOptions = React.useMemo(
    () =>
      uniqueEntryOptions(allEntries, "room_id", "room_number").filter(
        (room) => roomById.get(room.value)?.room_type === "CLASSROOM"
      ),
    [allEntries, roomById]
  );
  const laboratoryOptions = React.useMemo(
    () =>
      uniqueEntryOptions(allEntries, "room_id", "room_number").filter(
        (room) => roomById.get(room.value)?.room_type === "LAB"
      ),
    [allEntries, roomById]
  );
  const entries = React.useMemo(() => {
    if (tab === "student") {
      return divisionId ? allEntries.filter((entry) => entry.division_id === divisionId) : [];
    }
    if (tab === "faculty") {
      return facultyId ? allEntries.filter((entry) => entry.faculty_id === facultyId) : [];
    }
    if (tab === "classroom" || tab === "laboratory") {
      return roomId ? allEntries.filter((entry) => entry.room_id === roomId) : [];
    }
    return [];
  }, [allEntries, divisionId, facultyId, roomId, tab]);

  React.useEffect(() => {
    setTimetable(null);
    setDivisionId("");
    setFacultyId("");
    setRoomId("");
    setAllEntries([]);
  }, [timetableId]);

  React.useEffect(() => {
    apiGet<GeneratedTimetable>(`/timetables/${timetableId}`)
      .then(setTimetable)
      .catch((e) => toast.error(apiErrorMessage(e)));
  }, [timetableId]);

  React.useEffect(() => {
    let cancelled = false;
    setIsLoadingEntries(true);
    apiGet<TimetableEntry[]>(`/timetables/${timetableId}/entries`)
      .then((data) => {
        if (!cancelled) setAllEntries(data);
      })
      .catch((e) => toast.error(apiErrorMessage(e)))
      .finally(() => {
        if (!cancelled) setIsLoadingEntries(false);
      });
    return () => {
      cancelled = true;
    };
  }, [timetableId]);

  async function handleExport(format: "pdf" | "excel") {
    const queryParams: Record<string, string> = {};
    if (tab === "student") queryParams.division_id = divisionId;
    if (tab === "faculty") queryParams.faculty_id = facultyId;
    if (tab === "classroom" || tab === "laboratory") queryParams.room_id = roomId;

    setIsExporting(format);
    try {
      const blob = await apiDownload(`/timetables/${timetableId}/export/${format}`, { params: queryParams });
      const ext = format === "pdf" ? "pdf" : "xlsx";
      triggerBlobDownload(blob, `timetable-${tab}-${timetableId}.${ext}`);
    } catch (error) {
      toast.error(apiErrorMessage(error));
    } finally {
      setIsExporting(null);
    }
  }

  const practicalBlockPeriods = timetable
    ? Math.max(1, Math.ceil(timetable.practical_duration_minutes / timetable.theory_duration_minutes))
    : 1;

  const canExport =
    (tab === "student" && Boolean(divisionId)) ||
    (tab === "faculty" && Boolean(facultyId)) ||
    ((tab === "classroom" || tab === "laboratory") && Boolean(roomId));

  return (
    <div>
      <PageHeader
        title="Timetable"
        description={timetable ? `Generated on ${new Date(timetable.created_at).toLocaleString()}` : "Loading..."}
      />

      <Tabs
        value={tab}
        onValueChange={(v) => {
          setTab(v as TabKey);
          setRoomId("");
        }}
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <TabsList>
            <TabsTrigger value="student">Student</TabsTrigger>
            <TabsTrigger value="faculty">Faculty</TabsTrigger>
            <TabsTrigger value="classroom">Classroom</TabsTrigger>
            <TabsTrigger value="laboratory">Laboratory</TabsTrigger>
          </TabsList>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={!canExport || isExporting !== null}
              onClick={() => handleExport("pdf")}
            >
              {isExporting === "pdf" ? (
                <Download className="h-4 w-4 animate-bounce" />
              ) : (
                <FileText className="h-4 w-4" />
              )}
              PDF
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={!canExport || isExporting !== null}
              onClick={() => handleExport("excel")}
            >
              {isExporting === "excel" ? (
                <Download className="h-4 w-4 animate-bounce" />
              ) : (
                <FileSpreadsheet className="h-4 w-4" />
              )}
              Excel
            </Button>
          </div>
        </div>

        <TabsContent value="student">
          <SelectorRow
            label="Division"
            value={divisionId}
            onChange={setDivisionId}
            options={divisionOptions}
            placeholder="Select a division"
          />
        </TabsContent>
        <TabsContent value="faculty">
          <SelectorRow
            label="Faculty"
            value={facultyId}
            onChange={setFacultyId}
            options={facultyOptions}
            placeholder="Select a faculty member"
          />
        </TabsContent>
        <TabsContent value="classroom">
          <SelectorRow
            label="Classroom"
            value={roomId}
            onChange={setRoomId}
            options={classroomOptions}
            placeholder="Select a classroom"
          />
        </TabsContent>
        <TabsContent value="laboratory">
          <SelectorRow
            label="Laboratory"
            value={roomId}
            onChange={setRoomId}
            options={laboratoryOptions}
            placeholder="Select a laboratory"
          />
        </TabsContent>

        <div className="mt-4">
          {!timetable ? (
            <Skeleton className="h-64 w-full" />
          ) : isLoadingEntries ? (
            <Skeleton className="h-64 w-full" />
          ) : entries.length === 0 ? (
            <Card>
              <CardContent className="flex h-40 items-center justify-center text-sm text-muted-foreground">
                {tab === "student" && !divisionId
                  ? "Select a division to view its timetable."
                  : tab === "faculty" && !facultyId
                    ? "Select a faculty member to view their timetable."
                    : (tab === "classroom" || tab === "laboratory") && !roomId
                      ? `Select a ${tab} to view its timetable.`
                      : "No sessions found for this view."}
              </CardContent>
            </Card>
          ) : (
            <TimetableGrid
              entries={entries}
              days={timetable.working_days}
              periodsPerDay={timetable.periods_per_day}
              practicalBlockPeriods={practicalBlockPeriods}
              viewType={tab === "student" ? "STUDENT" : tab === "faculty" ? "FACULTY" : "ROOM"}
            />
          )}
        </div>
      </Tabs>
    </div>
  );
}

function uniqueEntryOptions(
  entries: TimetableEntry[],
  idKey: "division_id" | "faculty_id" | "room_id",
  labelKey: "division_name" | "faculty_name" | "room_number"
) {
  const seen = new Set<string>();
  const options: { value: string; label: string }[] = [];
  for (const entry of entries) {
    const value = entry[idKey];
    if (seen.has(value)) continue;
    seen.add(value);
    options.push({ value, label: entry[labelKey] });
  }
  return options.sort((a, b) => a.label.localeCompare(b.label));
}

function SelectorRow({
  label,
  value,
  onChange,
  options,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  placeholder: string;
}) {
  return (
    <div className="flex max-w-xs flex-col gap-1.5 py-3">
      <span className="text-sm font-medium text-muted-foreground">{label}</span>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem key={o.value} value={o.value}>
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
