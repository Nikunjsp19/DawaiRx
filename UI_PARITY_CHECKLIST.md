# UI Parity Checklist (Legacy templates → React)

*(Phase 4 / Phase 7 artifact.)*

## Legacy templates (source of truth)

- `src/web/templates/login.html`
- `src/web/templates/index.html`
- `src/web/templates/new-report.html`
- `src/web/templates/settings.html`
- `src/web/templates/runs.html`
- `src/web/templates/admin.html`

## Requirements

- [ ] **Login** – Same layout, card, fields, links (Request Access, Check status), footer. No alert/confirm.
- [ ] **Dashboard (index)** – "Report History", "Your Reports" section, table columns, pagination, empty state, New Report CTA.
- [ ] **New Report** – Multi-step wizard (date range → report name → upload), step indicators, loading animation parity using `src/web/static/loading/registro.json`.
- [ ] **Report detail / runs** – Report header, table with sticky header/columns, "Showing X rows" footer, download/delete. Medicine detail **right-side slide panel** on row click (same behavior as legacy new-report).
- [ ] **Settings** – Same structure and fields as settings.html.
- [ ] **Admin** – List requests, approve/reject, same table and actions as admin.html.
- [ ] **Loading** – Use `registro.json` Lottie where legacy uses it.
- [ ] **Layout** – Sidebar, nav items, theme toggle, consistent shell and spacing.

## Status

- [x] Login (structure and flows match; optional visual polish)
- [x] Dashboard (Report History, Your Reports, table, pagination, empty state)
- [x] New Report (multi-step wizard)
- [x] Report detail + medicine panel (slide-out on row click)
- [x] Settings (page and layout)
- [x] Admin (list, approve/reject)
- [x] Loading animation (registro.json via lottie-player on Dashboard)
- [x] Layout shell (sidebar, nav, theme)
