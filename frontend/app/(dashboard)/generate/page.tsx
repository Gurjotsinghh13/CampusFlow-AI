"use client";

import * as React from "react";
import Link from "next/link";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { CheckCircle2, Loader2, Sparkles, XCircle } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useOptionsList } from "@/hooks/use-options-list";
import { apiErrorMessage, apiPost } from "@/lib/api-client";
import type { AcademicYear, GeneratedTimetable } from "@/lib/types";

interface FormValues {
  academic_year_id: string;
}

export default function GenerateTimetablePage() {
  const { items: academicYears, isLoading: yearsLoading } = useOptionsList<AcademicYear>("/academic-years");
  const [result, setResult] = React.useState<GeneratedTimetable | null>(null);
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [issues, setIssues] = React.useState<string[]>([]);

  const { control, handleSubmit, formState } = useForm<FormValues>({
    defaultValues: { academic_year_id: "" },
  });

  async function onSubmit(values: FormValues) {
    if (!values.academic_year_id) {
      toast.error("Select an academic year first");
      return;
    }
    setIsGenerating(true);
    setResult(null);
    setIssues([]);
    try {
      const timetable = await apiPost<GeneratedTimetable>("/timetables/generate", {
        academic_year_id: values.academic_year_id,
      });
      setResult(timetable);
      if (timetable.status === "SUCCESS") {
        toast.success("Timetable generated successfully");
      } else {
        toast.error(timetable.message ?? "No conflict-free timetable could be generated");
      }
    } catch (error) {
      const responseData = (error as {
        response?: { data?: { data?: { issues?: string[] }; detail?: { issues?: string[] } } };
      })?.response?.data;
      const nextIssues = responseData?.data?.issues ?? responseData?.detail?.issues;
      if (Array.isArray(nextIssues)) {
        setIssues(nextIssues);
        toast.error(apiErrorMessage(error));
      } else {
        toast.error(apiErrorMessage(error));
      }
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div>
      <PageHeader title="Generate Timetable" description="Run the CP-SAT solver to produce a conflict-free schedule" />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Run Generation</CardTitle>
            <CardDescription>Select the academic year to generate a timetable for.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <Label>Academic Year</Label>
                <Controller
                  control={control}
                  name="academic_year_id"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange} disabled={yearsLoading}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select an academic year" />
                      </SelectTrigger>
                      <SelectContent>
                        {academicYears.map((y) => (
                          <SelectItem key={y.id} value={y.id}>
                            {y.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>

              <Button type="submit" disabled={isGenerating || formState.isSubmitting} className="w-fit">
                {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {isGenerating ? "Generating..." : "Generate Timetable"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Result</CardTitle>
            <CardDescription>Status of the most recent generation run.</CardDescription>
          </CardHeader>
          <CardContent>
            {!result && issues.length === 0 && (
              <p className="text-sm text-muted-foreground">Run a generation to see results here.</p>
            )}

            {issues.length > 0 && (
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2 text-sm font-medium text-destructive">
                  <XCircle className="h-4 w-4" />
                  Data is incomplete
                </div>
                <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {issues.map((issue, i) => (
                    <li key={i}>{issue}</li>
                  ))}
                </ul>
              </div>
            )}

            {result && (
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  {result.status === "SUCCESS" ? (
                    <CheckCircle2 className="h-5 w-5 text-success" />
                  ) : (
                    <XCircle className="h-5 w-5 text-destructive" />
                  )}
                  <Badge variant={result.status === "SUCCESS" ? "success" : "destructive"}>{result.status}</Badge>
                </div>
                {result.message && <p className="text-sm text-muted-foreground">{result.message}</p>}
                {result.solver_wall_time_seconds != null && (
                  <p className="text-sm text-muted-foreground">
                    Solved in {result.solver_wall_time_seconds.toFixed(2)}s
                  </p>
                )}
                {result.status === "SUCCESS" && (
                  <Button asChild variant="outline" className="w-fit">
                    <Link href={`/timetables/${result.id}`}>View Timetable</Link>
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
