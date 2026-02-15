# DawaiRx Frontend (React)

Pharmacy Audit & Reconciliation - React SPA.

## Requirements

- Node.js 18+
- npm or yarn

## Configuration

Create `.env` in frontend directory:

```
VITE_API_URL=http://localhost:8080
```

For local dev with Vite proxy, you can leave this empty (proxy in vite.config.js forwards /api to backend).

## Run

```bash
# From project root
cd frontend
npm install
npm run dev
```

App runs on `http://localhost:5173`.

## Build

```bash
npm run build
```

Output in `dist/`. Serve with any static file server.

## Pages

- **Login** - Login / Register
- **Dashboard** - Overview and quick actions
- **New Report** - Upload files and run reconciliation
- **Runs** - List previous runs, download reports
- **Settings** - Profile (basic)
