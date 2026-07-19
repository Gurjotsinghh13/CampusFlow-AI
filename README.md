# CampusFlow AI

AI-powered academic timetable generation platform. An enterprise-style
admin SaaS: enter departments, faculty, subjects, rooms and constraints,
click **Generate Timetable**, and get a conflict-free schedule computed by
Google OR-Tools CP-SAT - with Student, Faculty, Classroom, and Laboratory
views, each exportable to PDF and Excel.

## Status: feature-complete

Every module in the spec is implemented on both backend and frontend, end
to end, with no stubs or placeholders.

**Backend** (FastAPI + SQLAlchemy + PostgreSQL + OR-Tools CP-SAT):
- 8 CRUD modules: Departments, Academic Years, Semesters, Divisions,
  Subjects, Faculty (with subject-assignment endpoint), Rooms &
  Laboratories (one `rooms` table filtered by `room_type` - see design
  note below), Constraints (singleton scheduling config)
- JWT admin authentication
- **CP-SAT optimization engine** (`app/services/solver/`): precondition
  validation -> boolean-assignment model with hard no-overlap constraints
  on faculty/room/division and faculty daily/weekly workload caps -> a
  time-boxed solve -> persistence of the result
- **Generated Timetables API**, including a single filterable
  `/timetables/{id}/entries` endpoint that serves all four required views
- **PDF/Excel export** for every view, styled to match the UI theme

**Frontend** (Next.js 15 App Router + TypeScript + Tailwind + shadcn-style
components on Radix + React Hook Form + Zod + TanStack Table):
- Enterprise theme matching the brief exactly: dark navy primary, light
  gray background, white cards, medium radius, no gradients/glassmorphism
- Auth-guarded dashboard shell with responsive sidebar (all 13 nav items)
- Full CRUD pages for all 8 modules - search, server-side pagination,
  sorting via TanStack Table, create/edit dialogs, delete confirmation,
  loading skeletons, empty states, toast notifications
- Faculty page includes the subject multi-assignment checklist
- Generate Timetable page (select academic year -> run solver -> see
  status/issues/result)
- Generated Timetables list + detail page with Student/Faculty/Classroom/
  Laboratory tabs, a live Day x Period grid, and PDF/Excel export buttons

### Design note: Rooms vs Laboratories
The spec's own **Room Model** has a `room_type` field ("Lab or
Classroom"), so one `rooms` table serves both - the "Rooms" and
"Laboratories" sidebar pages filter by `room_type`. This avoids
duplicating an identical schema in two tables while still giving two
distinct nav items and two distinct CRUD screens.

### Modeling assumptions (documented, not hidden)
- `Constraint.number_of_periods` is treated as the number of *teaching*
  periods in a day - the lunch break is already excluded by whoever
  configures it; the solver does not additionally carve lunch out of the
  period grid.
- `Subject.theory_hours_per_week` is converted to a count of individual
  one-period theory sessions using `theory_duration_minutes` as the
  reference period length.
- `Subject.practical_hours_per_week` is converted to a count of practical
  *blocks*, each `practical_duration_minutes` long (possibly spanning
  multiple periods), using `ceil(hours / block_hours)`.

## Quickest start: Docker Compose

```bash
docker compose up --build
```

This starts Postgres, runs Alembic migrations, and boots the backend on
`:8000` and frontend on `:3000`. One manual step is required before you
can log in: generate and provide an admin password hash. There is no
default admin password baked in for security.

```bash
# 1. Generate a bcrypt hash for your chosen admin password
docker compose run --rm backend python scripts/create_admin_hash.py "YourStrongPassword"

# 2. Export the printed hash for Compose, or put it in a local .env file
export ADMIN_PASSWORD_HASH='paste-the-printed-hash-here'

# 3. Restart
docker compose up -d backend
```

Then visit `http://localhost:3000`, sign in with `admin@campusflow.ai`
(or whatever `ADMIN_EMAIL` you set) and the password you just hashed.

## Manual setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set DATABASE_URL to your Postgres instance

python scripts/create_admin_hash.py "YourStrongPassword"
# paste the printed hash into .env as ADMIN_PASSWORD_HASH

alembic upgrade head

uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs` - Health check: `http://localhost:8000/health`

### Frontend

```bash
cd frontend
npm ci
cp .env.local.example .env.local
# edit .env.local if your backend isn't on http://localhost:8000

npm run dev
```

App: `http://localhost:3000` - you'll be redirected to `/login`.

## Using it end to end

1. Sign in.
2. Add at least one Department, Academic Year, Semester, and Division.
3. Add Subjects (theory/practical hours) and Faculty, assigning subjects
   to faculty who can teach them.
4. Add Rooms and Laboratories with capacities.
5. Configure Constraints (working days, hours, lunch, period count).
6. Go to **Generate Timetable**, pick the academic year, and generate.
   If data is missing (no faculty for a subject, no lab configured, etc.)
   you'll get a precise list of what to fix instead of a generic failure.
7. Open the generated timetable and browse the Student / Faculty /
   Classroom / Laboratory tabs, or export any of them to PDF or Excel.

## Architecture

```
backend/
  app/
    core/          # config, db session, security, auth dependency
    models/        # SQLAlchemy ORM models (full schema)
    schemas/        # Pydantic request/response schemas
    repositories/   # data-access layer (BaseRepository + per-entity)
    services/       # business logic / validation layer
      solver/         # CP-SAT: data_loader, model_builder, solver_service
      export/          # grid_builder, pdf_export, excel_export
    routers/        # FastAPI route handlers (thin, delegate to services)
    utils/          # shared helpers
    main.py         # app factory, middleware, exception handlers
  alembic/          # migrations
  scripts/          # admin utilities
  Dockerfile
```

Every module follows: `router -> service -> repository -> model`. Routers
never touch the DB directly; services own business rules and raise
`HTTPException`s; repositories own querying via a shared generic base.

```
frontend/
  app/
    login/                  # public
    (dashboard)/             # auth-guarded route group
      layout.tsx              # sidebar shell + auth guard
      dashboard/
      departments/  academic-years/  semesters/  divisions/
      subjects/     faculty/         rooms/       laboratories/
      constraints/  generate/        timetables/  timetables/[id]/
      settings/
  components/
    ui/          # hand-written shadcn/ui-pattern primitives (Radix-based)
    layout/      # Sidebar, PageHeader, nav config
    data-table/  # generic DataTable + ConfirmDeleteDialog
    modules/     # per-module form dialogs + timetable grid/export UI
  hooks/
    use-crud-resource.ts   # shared list/search/paginate/create/update/delete
    use-options-list.ts    # shared FK dropdown data fetching
  lib/
    api-client.ts   # Axios instance, JWT interceptor, response unwrapping
    types.ts        # TS types mirroring backend Pydantic schemas
    validators/     # zod schemas per module
  Dockerfile
```

Every CRUD module page follows the same pattern: `useCrudResource(endpoint)`
for data -> `DataTable` for the table -> a per-module `*FormDialog` for
create/edit -> `ConfirmDeleteDialog` for delete. No page reimplements
fetch, pagination, or delete-confirmation logic.

## Deployment

- **Frontend -> Vercel**: point it at `frontend/`, set `NEXT_PUBLIC_API_URL`
  to your deployed backend's `/api/v1` URL. For Docker-based frontend
  deployments, pass the same value as the `NEXT_PUBLIC_API_URL` build arg
  because Next.js embeds public env vars during `next build`.
- **Backend -> Railway or Render**: point it at `backend/` (Dockerfile
  included), set `ENVIRONMENT=production`, `DATABASE_URL`,
  `JWT_SECRET_KEY` (at least 32 characters), `ADMIN_EMAIL`,
  `ADMIN_PASSWORD_HASH`, and explicit `CORS_ORIGINS` values without `"*"`.
  `CORS_ORIGINS` may be a JSON array such as
  `["https://app.example.com"]` or a comma-separated list.
  Optionally tune
  `LOGIN_RATE_LIMIT_ATTEMPTS`, `LOGIN_RATE_LIMIT_WINDOW_SECONDS`,
  `LOGIN_RATE_LIMIT_MAX_KEYS`, `SOLVER_MAX_TIME_SECONDS`, and
  `SOLVER_NUM_WORKERS`.
  Run `alembic upgrade head` as a release/start command before `uvicorn`.
- **Database**: any managed PostgreSQL (Railway/Render both offer one).
