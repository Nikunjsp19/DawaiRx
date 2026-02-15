# Python Dashboard Design Spec (Main Dashboard – index.html)

Single source of truth extracted from `src/web/templates/index.html` for colors, typography, spacing, and structure. Use this to match the React dashboard exactly.

---

## 1. Global / Root

| Token | Value | Usage |
|-------|--------|--------|
| **Body** | `bg-background-light dark:bg-background-dark` | Page background |
| **Text** | `text-[#110c1d] dark:text-gray-100` | Default text |
| **Transition** | `transition-colors duration-200` | Theme switch |
| **Layout** | `min-h-screen flex` | Body layout |
| **Font** | Inter 300, 400, 500, 600, 700, 900 | `font-display: ["Inter", "sans-serif"]` |

---

## 2. Color Palette (Tailwind config in template)

| Name | Light | Dark | Hex (light) |
|------|--------|------|-------------|
| **primary** | `#2387e5` | same | Blue (links, icons, active) |
| **primary-dark** | `#1964c8` | hover | Darker blue |
| **background-light** | `#f6f5f8` | — | Page background |
| **background-dark** | — | `#150f23` | Dark page bg |
| **surface-light** | `#ffffff` | — | Cards, sidebar |
| **surface-dark** | — | `#1e1b2e` | Dark cards/sidebar |
| **card-blue** | `#eff4ff` | — | (optional accent) |
| **card-blue-dark** | — | `#1c2236` | (optional dark) |

**Border colors**

- `border-gray-200/50` (light), `dark:border-gray-800/50` – sidebar, dividers
- `border-gray-100` (light), `dark:border-gray-800` – card inner borders, table
- `border-gray-200` (light), `dark:border-gray-600` – pagination buttons

**Text colors**

- Primary text: `text-[#110c1d] dark:text-white`
- Secondary / muted: `text-gray-500 dark:text-gray-400`, `text-gray-600 dark:text-gray-400`
- Table body numbers: `text-gray-700 dark:text-gray-300`
- Small label (e.g. timestamp): `text-gray-500` (light), `text-xs`

---

## 3. Border Radius (Tailwind config)

- **DEFAULT:** `0.25rem` (4px)
- **lg:** `0.5rem` (8px)
- **xl:** `0.75rem` (12px)
- **2xl:** `1rem` (16px)
- **full:** `9999px` (pills/circles)

---

## 4. Sidebar (Left Nav)

**Container**

- `fixed inset-y-0 left-0 z-50 w-56`
- `bg-surface-light dark:bg-surface-dark`
- `border-r border-gray-200/50 dark:border-gray-800/50`
- `flex flex-col`; mobile: `-translate-x-full lg:translate-x-0`, `transition-transform duration-300`

**Logo block**

- Container: `flex items-center gap-3 px-4 py-4 border-b border-gray-200/50 dark:border-gray-800/50`
- Icon box: `size-10 bg-primary/10 rounded-md text-primary`
- Icon: `material-symbols-outlined text-lg` → `local_pharmacy`
- Title: `text-base font-semibold tracking-tight text-slate-900 dark:text-white` → "DawaiRx"

**Nav links**

- Wrapper: `flex-1 px-3 py-4 space-y-1`
- **Active (Dashboard):** `flex items-center gap-3 px-3 py-2.5 rounded-md bg-primary/10 text-primary font-medium transition-colors text-sm`
- **Inactive:** `flex items-center gap-3 px-3 py-2.5 rounded-md text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-primary transition-colors text-sm`
- Icons: `material-symbols-outlined text-lg`
- Items: dashboard, add_circle (New Report), settings, admin_panel_settings (Admin Panel, hidden by default)

**Sign out block**

- Wrapper: `px-3 py-3 border-t border-gray-200/50 dark:border-gray-800/50`
- Button: `w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-red-600 dark:hover:text-red-400 transition-colors text-sm`
- Icon: `logout`

**Spacing**

- Horizontal: `px-4` (logo), `px-3` (nav/sign out)
- Vertical: `py-4` (logo, nav), `py-3` (sign out block, nav item padding `py-2.5`)
- Gap: `gap-3` (logo, nav items)

---

## 5. Main Content Area

**Wrapper**

- `flex-1 flex flex-col lg:ml-56 min-w-0`

**Content container (main)**

- `flex-1 w-full px-4 sm:px-6 lg:px-8 py-4 lg:py-6 overflow-auto`

So:

- Padding horizontal: `16px` → `24px` (sm) → `32px` (lg)
- Padding vertical: `16px` → `24px` (lg)

---

## 6. Page Header (Report History)

**Block**

- `mb-6`
- Inner: `flex flex-col gap-1`

**Title**

- "Report History"
- `text-2xl md:text-3xl font-bold tracking-tight text-[#110c1d] dark:text-white`

**Subtitle**

- "View and manage your reconciliation reports."
- `text-gray-500 dark:text-gray-400 text-sm max-w-2xl`

So: **~24–30px bold** title, **14px** gray subtitle, **4px** gap between them, **24px** margin below block.

---

## 7. “Your Reports” Card

**Outer card**

- `flex flex-col bg-surface-light dark:bg-surface-dark rounded-lg border border-gray-100/50 dark:border-gray-800/50 overflow-hidden`

**Card header**

- `flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800`
- Heading: `text-base font-semibold text-[#110c1d] dark:text-white flex items-center gap-2`
- Icon: `material-symbols-outlined text-primary text-base` → `description`
- Label: "Your Reports"

So: **16px** font, semibold; **16px** horizontal padding, **12px** vertical; **8px** gap between icon and text.

---

## 8. Loading State

- Wrapper: `p-6 text-center`
- Inner: `flex flex-col items-center justify-center`
- Lottie: `width: 200px; height: 250px`, `background="transparent"`, `speed="1"`, loop, autoplay
- Asset: `/static/loading/registro.json`
- Line 1: `text-gray-500 dark:text-gray-400 text-sm font-medium mt-2` → "Loading reports...."
- Line 2: `text-gray-400 dark:text-gray-500 text-xs mt-1` → "Analyzing inventory data"

So: **24px** padding, **8px** margin above first line, **4px** above second.

---

## 9. Empty State

- Wrapper: `p-6 text-center`
- Icon circle: `inline-flex items-center justify-center size-10 rounded-full bg-primary/10 text-primary mb-2`
- Icon: `material-symbols-outlined text-xl` → `description`
- Title: `text-base font-semibold text-[#110c1d] dark:text-white mb-1` → "No reports yet"
- Description: `text-gray-500 dark:text-gray-400 mb-4 text-sm` → "Get started by creating your first reconciliation report"
- CTA: `inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-primary hover:bg-primary-dark text-white text-sm font-semibold transition-all`
- CTA icon: `material-symbols-outlined text-base` → `add`
- CTA text: "Start New Report"

Spacing: **8px** below icon, **4px** below title, **16px** below description.

---

## 10. Error State (replaces loading content)

- Icon circle: `inline-flex items-center justify-center size-12 rounded-full bg-red-100 text-red-600 mb-4`
- Icon: `material-symbols-outlined` → `error`
- Title: `text-red-600 dark:text-red-400 font-semibold` → "Error loading reports"
- Message: `text-sm text-gray-600 dark:text-gray-400 mt-2`
- Button: `mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors` → "Retry"

---

## 11. Table

**Wrapper**

- `overflow-x-auto`

**Table**

- `w-full text-left text-sm whitespace-nowrap`

**Header**

- `bg-gray-50/30 dark:bg-gray-800/30 text-gray-500 dark:text-gray-400 font-medium border-b border-gray-100 dark:border-gray-800`
- Cells: `px-4 py-3 text-sm`; right-aligned columns: `text-right`
- Columns: Run ID, Created, Medicines, Ordered, Sold, Issues, Action (last five right-aligned)

**Body**

- `divide-y divide-gray-100 dark:divide-gray-800`
- Row: `hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors group/row`, `cursor: pointer`

**Cell padding**

- All cells: `px-4 py-3`

**Run ID cell**

- Inner: `flex items-center gap-2`
- Pill: `size-7 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-primary text-xs font-semibold` → "R"
- Text block: run ID `font-medium text-[#110c1d] dark:text-white text-sm`; below: `text-xs text-gray-500` (created string)

**Created cell**

- `text-gray-600 dark:text-gray-400 text-sm` (same created string)

**Numeric cells (Medicines, Ordered, Sold)**

- `text-right text-gray-700 dark:text-gray-300 text-sm` + `toLocaleString()`

**Issues cell**

- If > 0: `inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300`
- If 0: `inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300`

**Action cell**

- `flex items-center justify-end gap-2`
- Download: `text-primary font-medium text-sm hover:underline flex items-center gap-1.5 px-2 py-1.5 rounded hover:bg-primary/10 transition-colors`, icon `download` `text-base align-middle`
- Delete: `text-red-600 dark:text-red-400 font-medium text-sm hover:underline flex items-center gap-1.5 px-2 py-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors`, icon `delete` `text-base align-middle`

---

## 12. Pagination

**Container**

- `px-4 py-3 border-t border-gray-100 dark:border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-3`

**Summary text**

- `text-sm text-gray-500 dark:text-gray-400`
- "Showing " + **font-medium text-[#110c1d] dark:text-white** (from) + " to " + (to) + " of " + (total) + " results"

**Controls**

- Wrapper: `flex items-center gap-1.5`
- Prev: `flex items-center gap-2 px-4 py-2 rounded-md border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm`
  - Icon: `material-symbols-outlined text-base` → `chevron_left`
  - Text: "Prev"
- Page indicator: `px-3 py-1 text-sm font-medium text-[#110c1d] dark:text-white` (current), `text-sm text-gray-500 dark:text-gray-400` ("of"), same for total pages
- Next: same as Prev, icon `chevron_right` after "Next" text, `text-sm` on icon

---

## 13. Mobile Header (optional for parity)

- `lg:hidden sticky top-0 z-40 w-full border-b border-gray-200 dark:border-gray-800 bg-surface-light dark:bg-surface-dark px-4 py-3`
- Menu button: `size-10 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400`, icon `menu` `text-2xl`
- Center: logo icon `size-8 bg-primary/10 rounded-lg text-primary` + "DawaiRx" `text-base font-bold text-[#110c1d] dark:text-white`

---

## 14. Spacing Summary

| Area | Horizontal | Vertical | Gap |
|------|------------|----------|-----|
| Main content | px-4 sm:px-6 lg:px-8 | py-4 lg:py-6 | — |
| Page header | — | mb-6, gap-1 | 4px |
| Card | — | — | — |
| Card header | px-4 | py-3 | gap-2 |
| Loading / empty | p-6 | — | — |
| Table th/td | px-4 | py-3 | — |
| Pagination | px-4 | py-3 | gap-3, gap-1.5 (buttons) |
| Sidebar logo | px-4 | py-4 | gap-3 |
| Sidebar nav | px-3 | py-4, py-2.5 (item) | gap-3, space-y-1 |

---

## 15. Font Sizes (from classes)

- **text-2xl / md:text-3xl:** Page title (~24px / 30px)
- **text-base:** Card title, sidebar title, empty title
- **text-sm:** Subtitle, table, buttons, pagination, nav links, most UI
- **text-xs:** Timestamp under Run ID, badges (Issues), Lottie sub-message

---

## 16. Font Weights

- **font-bold:** Page title
- **font-semibold:** Card title, empty title, Run ID pill "R", CTA
- **font-medium:** Nav active, table Run ID text, pagination numbers, action buttons, loading first line

Use this spec when implementing or auditing the React dashboard so layout, colors, typography, and spacing match the Python app.
