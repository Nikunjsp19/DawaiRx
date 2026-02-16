# DawaiRx – Pharmacy Audit & Reconciliation

A pharmacy audit and reconciliation application for comparing ordered and sold medication reports. Built with **Spring Boot** (Java 17) and **React** (Vite).

## Features

- **Ingest** pharmacy reports (CSV, XLSX)
- **Normalize** data (NDC codes, drug names, quantities)
- **Reconcile** inventory (ordered vs sold)
- **Flag** audit issues with rule-based detection
- **Generate** reports (CSV, Excel, PDF)
- **Persist** run history and user data in MongoDB

## Requirements

- **Java 17**
- **Maven** 3.8+
- **Node.js** 18+
- **MongoDB** (local or Atlas)

## Quick Start

### 1. Clone and install

```bash
cd DawaiRx

# Install frontend dependencies
make install-frontend
# OR: cd frontend && npm ci
```

### 2. Configure MongoDB

Set your MongoDB connection in the backend:

- Edit `backend/src/main/resources/application.yml`, or
- Set environment variable: `SPRING_DATA_MONGODB_URI=mongodb://localhost:27017/dawai_rx`  
  (or your Atlas URI)

### 3. Run the application

Use two terminals:

**Terminal 1 – Backend (port 8080):**
```bash
make run-backend
# OR: cd backend && mvn spring-boot:run
```

**Terminal 2 – Frontend (port 5173):**
```bash
make run-frontend
# OR: cd frontend && npm run dev
```

Then open **http://localhost:5173** in your browser. The frontend proxies API requests to the backend in development.

### 4. Admin users

Admins are stored in MongoDB. Add an admin in the `admins` collection:

```javascript
db.admins.insertOne({ "user_id": "your-admin@email.com" })
```

## Project structure

```
DawaiRx/
├── backend/          # Spring Boot API (Java 17)
│   └── src/main/java/com/dawai/
├── frontend/         # React SPA (Vite)
│   └── src/
├── scripts/          # E2E and test helpers (optional)
├── Makefile
└── README.md
```

## Makefile commands

| Command            | Description                          |
|--------------------|--------------------------------------|
| `make help`        | Show available commands              |
| `make install-frontend` | Install frontend dependencies   |
| `make run-backend` | Start Spring Boot (port 8080)         |
| `make run-frontend`| Start Vite dev server (port 5173)     |
| `make build`       | Build backend JAR + frontend dist    |
| `make test-backend`| Run backend unit tests               |
| `make clean`       | Remove build artifacts               |

## Backend API

- **Health:** `GET /health`
- **Auth:** `POST /api/auth/login`, `POST /api/auth/register`
- **Runs:** `GET /api/runs`, `GET /api/runs/{id}`, `DELETE /api/runs/{id}`
- **Upload & run:** `POST /api/upload`, `POST /api/run`
- **Download:** `GET /api/download/{runId}/{fileType}` (e.g. `inventory_report`, `audit_report`, `audit_report_pdf`)
- **Admin:** `GET /api/admin/is-admin`

See `backend/README.md` for full API and configuration details.

## Frontend

See `frontend/README.md` for run, build, and environment configuration.

## CI

GitHub Actions workflow `.github/workflows/java-react-ci.yml` runs on changes to `backend/` and `frontend/`:

- Builds the backend with Maven
- Installs and builds the frontend with npm

## Azure Deployment (GitHub Actions)

This repo now has separate deployment workflows:

- Frontend (Azure Static Web Apps): `.github/workflows/azure-static-web-apps-happy-sky-0bcb5e90f.yml`
- Backend (Azure App Service): `.github/workflows/backend-azure-appservice-deploy.yml`

Required GitHub configuration:

- Repository `Variables`:
  - `VITE_API_URL` = your backend URL (example: `https://DawaiRxApp.azurewebsites.net`)
  - `AZURE_BACKEND_APP_NAME` = your backend App Service name (example: `DawaiRxApp`)
- Repository `Secrets`:
  - `AZURE_STATIC_WEB_APPS_API_TOKEN_HAPPY_SKY_0BCB5E90F` (already auto-created by Azure SWA)
  - `AZURE_CLIENT_ID`
  - `AZURE_TENANT_ID`
  - `AZURE_SUBSCRIPTION_ID`

Backend App Service application settings in Azure:

- `SPRING_DATA_MONGODB_URI`
- `SPRING_DATA_MONGODB_DATABASE`
- `JWT_SECRET`
- `CORS_ALLOWED_ORIGINS` = your frontend URL (example: `https://happy-sky-0bcb5e90f.4.azurestaticapps.net`)

## License

MIT
