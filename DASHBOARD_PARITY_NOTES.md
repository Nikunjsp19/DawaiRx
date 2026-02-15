# Dashboard Parity Notes

This document describes what was changed to align the React Dashboard with the legacy Python UI (`src/web/templates/index.html`) and any unavoidable deviations.

## Source of truth

- **Legacy template:** `src/web/templates/index.html`
- **Legacy loading asset:** `src/web/static/loading/registro.json` (copied to `frontend/public/loading/registro.json` for Vite)

## What was changed

### 1. **Dashboard.jsx** (full rebuild)

- **Page header:** Reduced to title and description only (no search bar, no header action buttons). Title: "Report History". Description: "View and manage your reconciliation reports."
- **Card structure:** Single card with border `border-gray-100/50 dark:border-gray-800/50`, rounded-lg, overflow-hidden. Header: "Your Reports" with `description` Material icon (primary color), and on the right: "Import CSV" button and "New Report" link (to preserve required actions without changing legacy layout).
- **Loading state:** Uses Lottie from `/loading/registro.json` at **200×250px** with message "Loading reports...." and sub-message "Analyzing inventory data". Wrapper uses `p-6 text-center` to match legacy.
- **Empty state:** Inlined to match legacy exactly: icon container `size-10 rounded-full bg-primary/10 text-primary`, icon `description`, title "No reports yet" (`text-base font-semibold`), description "Get started by creating your first reconciliation report", and primary button "Start New Report" with `add` icon (`px-5 py-2.5 rounded-md bg-primary hover:bg-primary-dark`).
- **Error state:** Red circle icon, "Error loading reports", error message text, and "Retry" button with legacy classes. Timeout message aligned with legacy wording (database connection / try again / internet).
- **Table columns:** Reordered and relabeled to match legacy: **Run ID**, **Created**, **Medicines**, **Ordered**, **Sold**, **Issues**, **Action**. Removed "Inventory Dates" and "RUN ID" / "CREATED" uppercase variants.
- **Run ID cell:** Blue "R" pill (`size-7 rounded-full bg-blue-100 dark:bg-blue-900/30 text-primary text-xs font-semibold`), run ID text, and created date as subtitle (`text-xs text-gray-500`).
- **Created column:** Same created date as `toLocaleString()`.
- **Numeric columns:** Right-aligned, `text-gray-700 dark:text-gray-300 text-sm`, `toLocaleString()`.
- **Issues column:** Red badge for count > 0, green "0" badge for zero, matching legacy classes.
- **Action column:** Download and Delete buttons with legacy styles (text-primary / text-red-600, hover:bg-primary/10 and hover:bg-red-50, material-symbols-outlined text-base).
- **Row behavior:** `hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors`, cursor-pointer, click navigates to report detail; button clicks use `stopPropagation`.
- **Pagination:** "Showing X to Y of Z results" (always "results"), Prev (chevron_left + "Prev"), "current of totalPages", Next ("Next" + chevron_right). Button styles and disabled logic match legacy.
- **Delete:** Confirm via in-app modal (`ConfirmDialog`), no `window.confirm`.
- **Toasts:** Success/error toasts for download, delete, and import (no `alert`).

### 2. **ui/index.jsx**

- **LoadingState:** When `useLottie` is true, wrapper uses `p-6` to match legacy; added optional `className` prop. Lottie remains 200×250, message/subMessage unchanged.
- **DataTable:** Supports `align: 'right'` for column headers and cells; supports both `header` and `label`, and both `cell` and `render`. Added `cellClassName` for per-column td classes. Table uses `whitespace-nowrap`; row class includes `group/row` and legacy hover/transition.

### 3. **Layout.jsx**

- No changes. Existing sidebar, logo (`local_pharmacy`), nav links (Dashboard, New Report, Settings, Admin when applicable), and Sign Out already match legacy structure.

### 4. **index.css**

- No changes required for dashboard parity.

## Design spec application (DASHBOARD_DESIGN_SPEC.md)

The following spec details were applied so the new app matches the Python dashboard:

- **Page header:** Title `text-2xl md:text-3xl font-bold`; subtitle `text-gray-500 dark:text-gray-400 text-sm`.
- **Card:** `bg-surface-light dark:bg-surface-dark`, `border border-gray-100/50 dark:border-gray-800/50`; header `flex items-center justify-between px-4 py-3 border-b border-gray-100`.
- **Run ID cell:** Run ID text `font-medium text-[#110c1d] dark:text-white text-sm`; timestamp `text-xs text-gray-500`.
- **Created column:** `text-gray-600 dark:text-gray-400 text-sm`.
- **Issues badges:** `bg-red-100 text-red-800` (and dark variants) for count > 0; green for 0.
- **Pagination:** Numbers use `font-medium` (not font-semibold).
- **DataTable thead:** `bg-gray-50/30 dark:bg-gray-800/30`, `text-gray-500`, `border-b border-gray-100 dark:border-gray-800`.

## What was matched exactly

- Page title and description text and typography.
- Card container and header layout (border, padding, "Your Reports" + icon).
- Loading: Lottie asset (registro.json), size 200×250, "Loading reports....", "Analyzing inventory data".
- Empty: icon size and style, "No reports yet", "Get started by creating your first reconciliation report", "Start New Report" button with add icon.
- Error: icon, "Error loading reports", message, Retry button and styling.
- Table: column order and names (Run ID, Created, Medicines, Ordered, Sold, Issues, Action).
- Run ID cell: "R" pill, run ID, created subtitle.
- Table header/body: bg-gray-50/30, border-b, divide-y, px-4 py-3, text-sm.
- Issues badges: red for > 0, green for 0.
- Action buttons: download and delete icon + hover styles.
- Pagination: "Showing X to Y of Z results", Prev/Next buttons and page indicator.
- Request timeout set to 8 seconds with legacy-style error message.

## Unavoidable deviations

1. **Report detail URL:** Legacy uses `/new-report?run_id=...`; React uses `/runs/:runId` for the report detail page. Behavior is equivalent (open report); only the route differs.
2. **Import CSV and New Report placement:** Legacy has no Import or "New Report" on the dashboard (only sidebar links and empty-state CTA). To preserve required actions, "Import CSV" and "New Report" were added in the card header next to "Your Reports". Styling uses the same button/link patterns as elsewhere in the legacy UI.
3. **Toast placement:** Legacy uses a fixed green/red banner for success/error. React uses a similar fixed toast (top-right) with the same intent; position is slightly different for consistency with the rest of the React app.
4. **Sticky table header:** Legacy does not use a sticky thead; React Dashboard does not enable `stickyHeader` on this table so behavior matches (no sticky header on dashboard).

## Functional requirements preserved

- Fetch runs with pagination (10 per page).
- Table columns: Run ID, Created, Medicines, Ordered, Sold, Issues, Action.
- Row click opens report detail.
- Download report (inventory_report).
- Delete report with confirm modal (no browser confirm).
- Import report CSV (file input + API).
- Create New Report (link to /new-report + empty state CTA).
- Loading state uses Lottie (registro.json) with matching size and text.
- Empty and error states match legacy wording and CTA/Retry.
- No `alert` or `confirm`; ConfirmDialog and toasts used instead.

## Files touched

- `frontend/src/pages/Dashboard.jsx` – rebuilt for parity.
- `frontend/src/components/ui/index.jsx` – LoadingState padding/className; DataTable align, header/label, cell/render, cellClassName.
- `DASHBOARD_PARITY_NOTES.md` – this file.

Layout, routes, and API usage (listRuns, deleteRun, downloadFile, importReportCsv) are unchanged.
