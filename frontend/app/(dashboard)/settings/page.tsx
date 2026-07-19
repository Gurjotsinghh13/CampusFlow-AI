"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { API_BASE_URL } from "@/lib/api-client";
import { clearToken, getTokenSubject } from "@/lib/auth";

export default function SettingsPage() {
  const router = useRouter();
  const [email, setEmail] = React.useState<string | null>(null);

  React.useEffect(() => {
    setEmail(getTokenSubject());
  }, []);

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  return (
    <div>
      <PageHeader title="Settings" description="Session and connection details" />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Account</CardTitle>
            <CardDescription>CampusFlow AI has a single administrator account.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Signed in as</p>
              <p className="mt-1 text-sm">{email ?? "-"}</p>
            </div>
            <Button variant="outline" className="w-fit" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
              Sign out
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>API Connection</CardTitle>
            <CardDescription>The backend this dashboard is talking to.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Base URL</p>
            <p className="mt-1 break-all font-mono text-sm">{API_BASE_URL}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
