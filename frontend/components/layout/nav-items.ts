import type { LucideIcon } from "lucide-react";
import {
  Building2,
  CalendarRange,
  ClipboardList,
  FlaskConical,
  GraduationCap,
  LayoutDashboard,
  LayoutList,
  Settings,
  SlidersHorizontal,
  Sparkles,
  Users,
  Layers,
  DoorOpen,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Departments", href: "/departments", icon: Building2 },
  { label: "Academic Years", href: "/academic-years", icon: CalendarRange },
  { label: "Semesters", href: "/semesters", icon: Layers },
  { label: "Divisions", href: "/divisions", icon: LayoutList },
  { label: "Faculty", href: "/faculty", icon: Users },
  { label: "Subjects", href: "/subjects", icon: GraduationCap },
  { label: "Rooms", href: "/rooms", icon: DoorOpen },
  { label: "Laboratories", href: "/laboratories", icon: FlaskConical },
  { label: "Constraints", href: "/constraints", icon: SlidersHorizontal },
  { label: "Generate Timetable", href: "/generate", icon: Sparkles },
  { label: "Generated Timetables", href: "/timetables", icon: ClipboardList },
  { label: "Settings", href: "/settings", icon: Settings },
];
