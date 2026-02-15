# Migration Map: Python/FastAPI → Java/React

This document maps the original Python/FastAPI codebase to the new Java (Spring Boot) and React implementation.

## Directory Layout

| Python (existing) | Java/React (new) |
|-------------------|------------------|
| `src/` | `backend/src/main/java/com/dawai/` |
| `src/web/templates/` | `frontend/src/pages/` |
| - | `frontend/src/components/` |

## Backend Mapping

### Application Entry

| Python | Java |
|--------|------|
| `src/cli/main.py` (web command) | `backend/.../DawaiRxApplication.java` |
| `src/web/app.py` | `backend/.../controller/*.java` |

### Authentication

| Python | Java |
|--------|------|
| `src/auth/utils.py` (JWT, bcrypt) | `backend/.../security/JwtService.java` |
| `src/auth/middleware.py` | `backend/.../security/JwtAuthFilter.java` |
| `src/auth/user_store.py` | `backend/.../repository/UserRepository.java` + `AuthService.java` |
| `src/auth/admin_store.py` | `backend/.../repository/AdminRepository.java` |
| `src/auth/models.py` | `backend/.../dto/LoginRequest.java`, `RegisterRequest.java`, `TokenResponse.java` |

### Persistence

| Python | Java |
|--------|------|
| `src/persistence/config.py` | `backend/.../resources/application.yml` |
| `src/persistence/models.py` | `backend/.../document/RunDocument.java`, `RunItemDocument.java`, `RunIssueDocument.java` |
| `src/persistence/store.py` | `backend/.../repository/RunRepository.java` + `RunService.java` |

### Ingestion

| Python | Java |
|--------|------|
| `src/ingestion/loaders.py` | `backend/.../ingestion/FileLoader.java` |
| `src/ingestion/mapper.py` | `backend/.../ingestion/ColumnMapper.java` |
| `src/ingestion/validator.py` | Validation in `RunService.uploadFiles()` |
| `src/ingestion/processor.py` | `RunService.runReconciliation()` + `FileLoader` + `ColumnMapper` |

### Normalization

| Python | Java |
|--------|------|
| `src/normalization/ndc.py` | `backend/.../normalization/NdcNormalizer.java` |
| `src/normalization/medicine_key.py` | `backend/.../normalization/MedicineKeyGenerator.java` |
| `src/normalization/processor.py` | `backend/.../normalization/NormalizationService.java` |
| `src/normalization/text.py`, `dates.py`, `quantities.py` | Inlined in `NormalizationService.java` |

### Reconciliation

| Python | Java |
|--------|------|
| `src/reconciliation/engine.py` | `backend/.../reconciliation/ReconciliationService.java` |

### Rules Engine

| Python | Java |
|--------|------|
| `src/rules/base.py` | `backend/.../rules/RuleEngine.java` |
| `src/rules/implementations.py` | Rules R002, R003, R005 in `RuleEngine.java` |

### Reporting

| Python | Java |
|--------|------|
| `src/reporting/excel.py` | `backend/.../reporting/ReportService.java` (Apache POI) |
| `src/reporting/pdf.py` | `backend/.../reporting/ReportService.java` (OpenPDF) |
| CSV (pandas) | `ReportService.writeCsv()` (OpenCSV) |

### REST Endpoints

| Python Route | Java Controller Method |
|--------------|------------------------|
| `POST /api/auth/login` | `AuthController.login()` |
| `POST /api/auth/register` | `AuthController.register()` |
| `POST /api/upload` | `UploadController.upload()` |
| `POST /api/run` | `RunController.run()` |
| `GET /api/runs` | `RunController.listRuns()` |
| `GET /api/runs/{id}` | `RunController.getRun()` |
| `DELETE /api/runs/{id}` | `RunController.deleteRun()` |
| `GET /api/download/{runId}/{fileType}` | `RunController.download()` |

## Frontend Mapping

### Pages

| Python Template | React Page |
|-----------------|------------|
| `login.html` | `frontend/src/pages/Login.jsx` |
| `index.html` | `frontend/src/pages/Dashboard.jsx` |
| `new-report.html` | `frontend/src/pages/NewReport.jsx` |
| `runs.html` | `frontend/src/pages/Runs.jsx` |
| `settings.html` | `frontend/src/pages/Settings.jsx` |

### API Client

| Python (server-side) | React |
|---------------------|-------|
| FastAPI routes | `frontend/src/api/client.js` (fetch) |

## Dependencies

| Python | Java |
|--------|------|
| FastAPI | Spring Boot Web |
| pymongo | Spring Data MongoDB |
| pandas, openpyxl | Apache POI, OpenCSV |
| bcrypt | Spring Security Crypto |
| PyJWT | jjwt |
| reportlab | OpenPDF |

## Features Not Yet Ported

- Registration request flow (request-access, approve, reject)
- Admin panel
- Settings update (PUT /api/auth/settings)
- Extended rules (`implementations_extended.py`)
- DawaiRx format report (`dawairx_format.py`)
- Date filtering in run (partially: params accepted, filtering logic simplified)
- Run detail page with items/issues (Runs list only for MVP)
