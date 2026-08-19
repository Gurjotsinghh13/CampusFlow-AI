export interface APIResponse<T> {
  success: boolean;
  message: string;
  data: T | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Department {
  id: string;
  name: string;
  code: string;
  created_at: string;
  updated_at: string;
}

export interface AcademicYear {
  id: string;
  label: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Semester {
  id: string;
  number: number;
  academic_year_id: string;
  created_at: string;
  updated_at: string;
}

export interface Division {
  id: string;
  name: string;
  student_count: number;
  department_id: string;
  semester_id: string;
  created_at: string;
  updated_at: string;
}

export interface SubjectSummary {
  id: string;
  name: string;
  code: string;
}

export interface Subject {
  id: string;
  name: string;
  code: string;
  credits: number;
  theory_hours_per_week: number;
  practical_hours_per_week: number;
  semester_id: string;
  department_id: string;
  created_at: string;
  updated_at: string;
}

export interface Faculty {
  id: string;
  full_name: string;
  employee_id: string;
  max_daily_lectures: number;
  max_weekly_lectures: number;
  department_id: string;
  subjects: SubjectSummary[];
  created_at: string;
  updated_at: string;
}

export type RoomType = "CLASSROOM" | "LAB";

export interface Room {
  id: string;
  room_number: string;
  capacity: number;
  room_type: RoomType;
  created_at: string;
  updated_at: string;
}

export interface Constraint {
  id: string;
  working_days: string[];
  college_start_time: string;
  college_end_time: string;
  lunch_break_start: string;
  lunch_break_end: string;
  number_of_periods: number;
  theory_duration_minutes: number;
  practical_duration_minutes: number;
  created_at: string;
  updated_at: string;
}

export interface PeriodSlot {
  period_index: number;
  label: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  is_before_lunch: boolean;
  is_after_lunch: boolean;
}

export type GenerationStatus = "PENDING" | "RUNNING" | "SUCCESS" | "INFEASIBLE" | "FAILED";

export interface GeneratedTimetable {
  id: string;
  academic_year_id: string;
  academic_year_label: string;
  status: GenerationStatus;
  solver_wall_time_seconds: number | null;
  objective_value: number | null;
  message: string | null;
  working_days: string[];
  periods_per_day: number;
  theory_duration_minutes: number;
  practical_duration_minutes: number;
  period_slots?: PeriodSlot[];
  created_at: string;
}

export type SessionType = "THEORY" | "PRACTICAL";

export interface TimetableEntry {
  id: string;
  day: string;
  period_index: number;
  start_time?: string;
  end_time?: string;
  session_type: SessionType;
  division_id: string;
  subject_id: string;
  faculty_id: string;
  room_id: string;
  division_name: string;
  subject_name: string;
  subject_code: string;
  faculty_name: string;
  room_number: string;
}
