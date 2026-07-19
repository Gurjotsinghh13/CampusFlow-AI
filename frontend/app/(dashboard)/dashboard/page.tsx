"use client";

import * as React from "react";
import Link from "next/link";
import { Building2, GraduationCap, Sparkles, Users } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { apiGet } from "@/lib/api-client";
import type { PaginatedResponse } from "@/lib/types";

interface CountCardConfig {
  label: string;
  endpoint: string;
  icon: React.ElementType;
}

const CARDS: CountCardConfig[] = [
  { label: "Departments", endpoint: "/departments", icon: Building2 },
  { label: "Faculty", endpoint: "/faculty", icon: Users },
  { label: "Subjects", endpoint: "/subjects", icon: GraduationCap },
];

export default function DashboardPage() {
  const [counts, setCounts] = React.useState<Record<string, number | null>>({});

  React.useEffect(() => {
    let cancelled = false;
    Promise.all(
      CARDS.map((c) =>
        apiGet<PaginatedResponse<unknown>>(c.endpoint, { params: { page: 1, page_size: 1 } })
          .then((res) => [c.label, res.total] as const)
          .catch(() => [c.label, null] as const)
      )
    ).then((results) => {
      if (cancelled) return;
      setCounts(Object.fromEntries(results));
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of your institution's academic data"
        action={
          <Button asChild>
            <Link href="/generate">
              <Sparkles className="h-4 w-4" />
              Generate Timetable
            </Link>
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {CARDS.map((card) => {
          const Icon = card.icon;
          const count = counts[card.label];
          return (
            <Card key={card.label}>
              <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{card.label}</CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {count === undefined ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <div className="text-2xl font-semibold">{count ?? "-"}</div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Getting started</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          <ol className="list-decimal space-y-1.5 pl-4">
            <li>Set up Departments, Academic Years, Semesters and Divisions</li>
            <li>Add Faculty and Subjects, then assign subjects to faculty</li>
            <li>Add Rooms and Laboratories</li>
            <li>Configure scheduling Constraints (working days, hours, lunch break)</li>
            <li>
              Go to{" "}
              <Link href="/generate" className="font-medium text-foreground underline underline-offset-2">
                Generate Timetable
              </Link>{" "}
              to run the solver
            </li>
          </ol>
        </CardContent>
      </Card>
    </div>
  );
}
