"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, Menu, X } from "lucide-react";

import { cn } from "@/lib/utils";
import { clearToken } from "@/lib/auth";
import { NAV_ITEMS } from "@/components/layout/nav-items";
import { Button } from "@/components/ui/button";

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto scrollbar-thin px-3 py-2">
      {NAV_ITEMS.map((item) => {
        const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

function LogoutButton() {
  const router = useRouter();
  return (
    <Button
      variant="ghost"
      className="w-full justify-start gap-2.5 text-muted-foreground hover:text-foreground"
      onClick={() => {
        clearToken();
        router.replace("/login");
      }}
    >
      <LogOut className="h-4 w-4" />
      Logout
    </Button>
  );
}

export function Sidebar() {
  const [mobileOpen, setMobileOpen] = React.useState(false);

  return (
    <>
      {/* Desktop */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-card md:flex">
        <div className="flex h-14 items-center gap-2 border-b border-border px-5">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-sm font-bold text-primary-foreground">
            C
          </div>
          <span className="text-sm font-semibold">CampusFlow AI</span>
        </div>
        <NavLinks />
        <div className="border-t border-border p-3">
          <LogoutButton />
        </div>
      </aside>

      {/* Mobile top bar trigger */}
      <div className="flex h-14 items-center justify-between border-b border-border bg-card px-4 md:hidden">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-sm font-bold text-primary-foreground">
            C
          </div>
          <span className="text-sm font-semibold">CampusFlow AI</span>
        </div>
        <Button variant="ghost" size="icon" onClick={() => setMobileOpen(true)}>
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-foreground/40" onClick={() => setMobileOpen(false)} />
          <aside className="absolute left-0 top-0 flex h-full w-72 flex-col bg-card shadow-lg">
            <div className="flex h-14 items-center justify-between border-b border-border px-5">
              <span className="text-sm font-semibold">CampusFlow AI</span>
              <Button variant="ghost" size="icon" onClick={() => setMobileOpen(false)}>
                <X className="h-5 w-5" />
              </Button>
            </div>
            <NavLinks onNavigate={() => setMobileOpen(false)} />
            <div className="border-t border-border p-3">
              <LogoutButton />
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
