# DawaiRx Backend (Spring Boot)

Pharmacy Audit & Reconciliation - Java/Spring Boot backend.

## Requirements

- Java 17
- Maven 3.8+
- MongoDB (local or Atlas)

## Configuration

**Important:** Use the same MongoDB URI and database name as your Python app so existing users can log in.

In `application.yml`:
- `spring.data.mongodb.uri` - e.g. `mongodb://localhost:27017/dawai_rx` or your Atlas URI
- `spring.data.mongodb.database` - e.g. `dawai_rx` or `DawaiRx` (case-sensitive!)
- `JWT_SECRET_KEY` - Secret for JWT tokens (required in production)
- `UPLOAD_DIR` - Directory for uploads (default: `/tmp/dawai-rx/uploads`)
- `OUTPUT_DIR` - Directory for report outputs (default: `/tmp/dawai-rx/output`)
- `CORS_ORIGINS` - Allowed CORS origins (default: `http://localhost:5173,http://localhost:3000`)

## Run

```bash
# From project root
cd backend
mvn spring-boot:run

# Or build and run the JAR
mvn clean package
java -jar target/dawai-rx-backend-1.0.0.jar
```

Server runs on `http://localhost:8080` by default.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/auth/login | Login |
| POST | /api/auth/register | Register |
| POST | /api/upload | Upload files (requires auth) |
| POST | /api/run | Run reconciliation (requires auth) |
| GET | /api/runs | List runs (requires auth) |
| GET | /api/runs/{id} | Get run details (requires auth) |
| DELETE | /api/runs/{id} | Delete run (requires auth) |
| GET | /api/download/{runId}/{fileType} | Download report (requires auth) |
| GET | /api/admin/is-admin | Returns `{ "is_admin": true/false }` (requires auth) |

## Admin identification

Admins are identified by the **MongoDB `admins` collection** (same as the Python app):

- Each document has a `user_id` field. If the logged-in user’s `user_id` is in this collection, they are treated as an admin.
- The React app calls **GET /api/admin/is-admin** with the JWT; the backend reads the user from the token and checks `admins` → the sidebar shows “Admin Panel” only when `is_admin` is true.
- **To make a user an admin:** insert a document into the `admins` collection with that user’s `user_id`, e.g. in MongoDB Shell or Compass:
  ```js
  db.admins.insertOne({ user_id: "your_admin_username" })
  ```
- The `admins` collection uses the same database as `users` (e.g. `DawaiRx` or `dawai_rx`).

## MongoDB Collections

- `users` - User accounts
- `admins` - Admin user IDs (documents with `user_id`; presence = admin)
- `runs` - Run metadata
- `run_items` - Per-medicine reconciliation rows
- `run_issues` - Audit issues from rules engine
