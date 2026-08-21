# PRODUCTION_LOGIN_AUDIT

## 1. Root cause
- The frontend API client silently fell back to `http://localhost:8000/api/v1` when `NEXT_PUBLIC_API_URL` is not present at build time.
- In a production browser session this causes login requests to target the end-user machine (`localhost`) instead of Railway, which surfaces as Axios `"Network Error"`.

## 2. Evidence
- Frontend API base URL resolution:
  - `frontend/lib/api-client.ts` previously used:
    - `process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"`
- Login request call site:
  - `frontend/app/login/page.tsx` line with `client.post("/auth/login", values)`
- URL composition:
  - Missing `NEXT_PUBLIC_API_URL` in production build => request URL becomes `http://localhost:8000/api/v1/auth/login`
  - Correct production target should be `https://campusflow-ai-production.up.railway.app/api/v1/auth/login`
- Backend route verification (local route test):
  - `POST /api/v1/auth/login` returns auth response path (401 for wrong password as expected)
  - `POST /auth/login` returns 404

## 3. Files inspected
- `frontend/lib/api-client.ts`
- `frontend/lib/auth.ts`
- `frontend/.env.local.example`
- `frontend/next.config.ts`
- `frontend/package.json`
- `frontend/app/login/page.tsx`
- `backend/app/main.py`
- `backend/app/routers/auth.py`
- `backend/app/core/config.py`
- `backend/app/schemas/auth.py`
- `backend/.env.example`

## 4. Files changed
- `frontend/lib/api-client.ts`
- `PRODUCTION_LOGIN_AUDIT.md`

## 5. Exact fix
- Updated frontend API base URL fallback logic in `frontend/lib/api-client.ts`:
  - In production mode (`NODE_ENV=production`), fallback is now `https://campusflow-ai-production.up.railway.app/api/v1`
  - In non-production, fallback remains `http://localhost:8000/api/v1`
  - Added trailing slash normalization to prevent malformed concatenation

## 6. Production API URL
- `https://campusflow-ai-production.up.railway.app/api/v1`

## 7. Production frontend URL
- `https://campus-flow-ai-scheduler.vercel.app`

## 8. Login endpoint
- Registered backend route: `POST /api/v1/auth/login`
- Final expected production request URL:
  - `https://campusflow-ai-production.up.railway.app/api/v1/auth/login`

## 9. CORS status
- CORS middleware is enabled in `backend/app/main.py` with:
  - `allow_origins=settings.CORS_ORIGINS`
  - `allow_credentials=True`
- `CORS_ORIGINS` parsing supports:
  - JSON array string (`["https://campus-flow-ai-scheduler.vercel.app"]`)
  - Comma-separated string (`https://campus-flow-ai-scheduler.vercel.app`)
- No wildcard loosening was introduced.

## 10. Environment variable status
- Frontend uses `NEXT_PUBLIC_API_URL` (build-time in Next.js).
- If unset during Vercel build, prior behavior caused localhost fallback and login network failure.
- Fix adds a safe production fallback URL to avoid this failure mode.

## 11. Authentication status
- Frontend sends JSON `{ email, password }`.
- Backend `LoginRequest` expects JSON body with `email` + `password`.
- Request/response schema is compatible.

## 12. Backend health status
- Direct production health/docs checks from this sandbox were blocked by DNS resolution restrictions:
  - `Could not resolve host: campusflow-ai-production.up.railway.app`
- Therefore external runtime verification from this environment is blocked.

## 13. Test results
- Backend compile check: `python -m compileall .` ✅
- Backend unit tests command: `python -m unittest discover -s tests -p "test_*.py"` ❌
  - Repository has no importable `backend/tests` directory in this checkout (`ImportError: Start directory is not importable: 'tests'`).
- Frontend typecheck: `npm run typecheck` ✅

## 14. Build results
- Frontend lint: `npm run lint` ✅
- Frontend build: `npm run build` ✅

## 15. Final production verification
- Route mapping and URL composition were traced end-to-end in code.
- A minimal fix was applied to prevent production login requests from resolving to localhost when `NEXT_PUBLIC_API_URL` is missing at build.
- Actual live production request validation from this sandbox is blocked by DNS restrictions.

## Final classification
- **BLOCKED**
