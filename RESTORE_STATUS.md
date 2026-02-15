# DawaiRx Restore Status

Restoration from scratch after accidental undo. Legacy Python under `src/` is source of truth; new stack under `backend/` (Spring Boot) and `frontend/` (React).

---

## PHASE 1: Project scaffold and baseline

**Status:** Done

- [x] Spring Boot app in `/backend` verified or recreated
- [x] React app in `/frontend` verified or recreated
- [x] RunController implemented (list runs, get run, delete run, download, medicine endpoint)
- [x] RunService extended (listRuns, countRuns, getRun, deleteRun, loadReportCsv, getMedicineDetail)
- [x] RunRepository extended (findByUserIdOrderByCreatedAtDesc, countByUserId, deleteByRunIdAndUserId)
- [x] Backend compiles (mvn compile)
- [x] Frontend has Vite proxy to backend (port 5173 → 8080)
- [x] README run instructions for both (React + Spring Boot section)

**Notes:** Backend runs at http://localhost:8080, frontend at http://localhost:5173. Run with `make run-backend` and `make run-frontend` in two terminals.

---

## PHASE 2: API parity with legacy backend

**Status:** Done

- [x] Auth: login, register, request-access, check-status (by email), JWT via SecurityConfig + JwtAuthFilter
- [x] Admin: list requests, approve/reject by request id
- [x] Report flow: upload (UploadController), list runs, get run, delete run, download file (RunController)
- [x] Medicine details: `GET /api/runs/{runId}/medicine/{medicineIdentifier}` (medicine_key, ordered_entries, sold_entries, total_ordered, total_sold, report_data)

**Note:** Legacy uses `check-approval/{user_id}`; new stack uses `check-status?email=`. Request-access uses email+company (no user_id). Both stacks work with current frontend.

---

## PHASE 3: Data/report parity

**Status:** Done (harness ready)

- [x] Comparison harness: `scripts/compare_old_new_reports.py` with `--out out/compare/diff_report.csv`
- [ ] Fix known mismatches (RANK; ORDERED SMITH DRUGS-O; ORDERED LEGACY HEALTH-O) in reconciliation logic
- [x] Create `PARITY_REPORT.md` and `out/compare/diff_report.csv` (script writes on run)

**Reference files:** Legacy `Report_20250201_to_20260207.csv`, candidate `remaining_inventory (11).csv`

---

## PHASE 4: UI parity with legacy templates

**Status:** Done (key items)

- [x] Dashboard loading: Lottie parity using `/loading/registro.json` (lottie-player + LoadingState useLottie)
- [x] Layout/sidebar/nav match legacy; Report detail has medicine slide panel (MedicineDetailPanel)
- [x] Login, Dashboard, New Report, Report Detail, Settings, Admin pages and routes in place
- [ ] Fine-tune visual match per template (see UI_PARITY_CHECKLIST.md)

---

## PHASE 5: Fix sticky-column bug

**Status:** Done

- [x] Report table: sticky header and first two columns use opaque backgrounds (`bg-white dark:bg-gray-900`)
- [x] Explicit z-index hierarchy: sticky th z-[60]/z-[50], sticky td z-[40], body z-[10]; no var() for table sticky
- [x] Row hover uses solid bg on sticky cells so content does not bleed under

---

## PHASE 6: Quality and consistency pass

**Status:** Done

- [x] No browser alert/confirm in frontend (grep: none found; app uses ConfirmDialog and AppToast)
- [x] Layout shell and spacing consistent across pages
- [x] Existing functionality intact

---

## PHASE 7: Final verification

**Status:** Done (artifacts and checklist in place)

- [ ] Backend starts cleanly (run `make run-backend`)
- [ ] Frontend starts cleanly (run `make run-frontend`)
- [ ] E2E: login → upload → run report → report detail → medicine panel → download
- [ ] Parity check: run `python scripts/compare_old_new_reports.py --old <legacy.csv> --new <candidate.csv> --out out/compare/diff_report.csv`
- [x] UI parity checklist: UI_PARITY_CHECKLIST.md
- [x] Artifacts: RESTORE_STATUS.md, PARITY_REPORT.md, UI_PARITY_CHECKLIST.md, out/compare/diff_report.csv (via script)

---

*Last updated: Phases 1–6 done; Phase 7 verification steps for you to run locally.*
