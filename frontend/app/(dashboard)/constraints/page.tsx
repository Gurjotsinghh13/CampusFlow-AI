"use client";

import * as React from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import axios from "axios";

import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { MultiSelectChecklist } from "@/components/ui/multi-select-checklist";
import { apiErrorMessage, apiGet, apiPut } from "@/lib/api-client";
import { DAYS, constraintFormSchema, type ConstraintFormValues } from "@/lib/validators/constraint";
import type { Constraint } from "@/lib/types";

type WorkingDay = (typeof DAYS)[number];

const DAY_SET = new Set<string>(DAYS);

const DEFAULT_VALUES: ConstraintFormValues = {
  working_days: ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"],
  college_start_time: "09:00",
  college_end_time: "17:00",
  lunch_break_start: "13:00",
  lunch_break_end: "14:00",
  number_of_periods: 7,
  theory_duration_minutes: 60,
  practical_duration_minutes: 120,
};

function normalizeWorkingDays(days: string[]): WorkingDay[] {
  return days.filter((day): day is WorkingDay => DAY_SET.has(day));
}

export default function ConstraintsPage() {
  const [isLoading, setIsLoading] = React.useState(true);
  const [hasExisting, setHasExisting] = React.useState(false);

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors, isSubmitting },
  } = useForm<ConstraintFormValues>({
    resolver: zodResolver(constraintFormSchema),
    defaultValues: DEFAULT_VALUES,
  });

  React.useEffect(() => {
    let cancelled = false;
    apiGet<Constraint>("/constraints")
      .then((data) => {
        if (cancelled) return;
        setHasExisting(true);
        reset({
          working_days: normalizeWorkingDays(data.working_days),
          college_start_time: data.college_start_time,
          college_end_time: data.college_end_time,
          lunch_break_start: data.lunch_break_start,
          lunch_break_end: data.lunch_break_end,
          number_of_periods: data.number_of_periods,
          theory_duration_minutes: data.theory_duration_minutes,
          practical_duration_minutes: data.practical_duration_minutes,
        });
      })
      .catch((error) => {
        if (!axios.isAxiosError(error) || error.response?.status !== 404) {
          toast.error(apiErrorMessage(error));
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reset]);

  async function onSubmit(values: ConstraintFormValues) {
    try {
      await apiPut("/constraints", values);
      setHasExisting(true);
      toast.success("Scheduling constraints saved");
    } catch (error) {
      toast.error(apiErrorMessage(error));
    }
  }

  return (
    <div>
      <PageHeader
        title="Constraints"
        description="Institution-wide scheduling rules used by the timetable generator"
      />

      <Card className="max-w-3xl">
        <CardHeader>
          <CardTitle>Scheduling Configuration</CardTitle>
          <CardDescription>
            {hasExisting
              ? "These rules apply to every timetable you generate."
              : "Not configured yet - set these before generating your first timetable."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex flex-col gap-4">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
              <div className="flex flex-col gap-1.5">
                <Label>Working Days</Label>
                <Controller
                  control={control}
                  name="working_days"
                  render={({ field }) => (
                    <MultiSelectChecklist
                      options={DAYS.map((d) => ({ value: d, label: d.charAt(0) + d.slice(1).toLowerCase() }))}
                      selected={field.value}
                      onChange={field.onChange}
                      className="max-h-none"
                    />
                  )}
                />
                {errors.working_days && <p className="text-xs text-destructive">{errors.working_days.message}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="college_start_time">College Start Time</Label>
                  <Input id="college_start_time" type="time" {...register("college_start_time")} />
                  {errors.college_start_time && (
                    <p className="text-xs text-destructive">{errors.college_start_time.message}</p>
                  )}
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="college_end_time">College End Time</Label>
                  <Input id="college_end_time" type="time" {...register("college_end_time")} />
                  {errors.college_end_time && (
                    <p className="text-xs text-destructive">{errors.college_end_time.message}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="lunch_break_start">Lunch Break Start</Label>
                  <Input id="lunch_break_start" type="time" {...register("lunch_break_start")} />
                  {errors.lunch_break_start && (
                    <p className="text-xs text-destructive">{errors.lunch_break_start.message}</p>
                  )}
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="lunch_break_end">Lunch Break End</Label>
                  <Input id="lunch_break_end" type="time" {...register("lunch_break_end")} />
                  {errors.lunch_break_end && (
                    <p className="text-xs text-destructive">{errors.lunch_break_end.message}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="number_of_periods">Periods / Day</Label>
                  <Input id="number_of_periods" type="number" min={1} max={20} {...register("number_of_periods")} />
                  {errors.number_of_periods && (
                    <p className="text-xs text-destructive">{errors.number_of_periods.message}</p>
                  )}
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="theory_duration_minutes">Theory Duration (min)</Label>
                  <Input
                    id="theory_duration_minutes"
                    type="number"
                    min={15}
                    max={180}
                    {...register("theory_duration_minutes")}
                  />
                  {errors.theory_duration_minutes && (
                    <p className="text-xs text-destructive">{errors.theory_duration_minutes.message}</p>
                  )}
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="practical_duration_minutes">Practical Duration (min)</Label>
                  <Input
                    id="practical_duration_minutes"
                    type="number"
                    min={30}
                    max={300}
                    {...register("practical_duration_minutes")}
                  />
                  {errors.practical_duration_minutes && (
                    <p className="text-xs text-destructive">{errors.practical_duration_minutes.message}</p>
                  )}
                </div>
              </div>

              <div className="flex justify-end">
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  Save Constraints
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
