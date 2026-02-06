# Azure Deploy (Simple GitHub Push)

This guide sets up a **Code-based** Azure App Service deploy (no Docker). Once configured, every push to `main` deploys automatically.

## Prerequisites

- Azure App Service (Basic B1 plan is fine)
- GitHub repo connected to this project
- MongoDB Atlas connection string (recommended)

## 1. Create the Web App (Code, not Docker)

1. Azure Portal → **Create resource** → **Web App**
2. **Publish**: `Code`
3. **Runtime stack**: `Python 3.11`
4. **Operating system**: `Linux`
5. **Region**: pick your region
6. **Plan**: your **Basic B1** plan

## 2. Configure App Settings

Azure Portal → your Web App → **Configuration** → **Application settings**

Add:
- `MONGO_URI` = your MongoDB connection string
- `SECRET_KEY` = any strong random string
- `PORT` = `8000`

Click **Save** (this restarts the app).

## 3. Set the Startup Command

Azure Portal → your Web App → **Configuration** → **General settings**

Set **Startup Command** to:
```
python -m src.cli.main web --host 0.0.0.0 --port 8000
```

## 4. Add the GitHub Actions Workflow

Create a GitHub secret:
- `AZURE_WEBAPP_PUBLISH_PROFILE`
  - Azure Portal → your Web App → **Get publish profile**
  - Copy the entire XML contents into the secret

Then add this workflow (already included in this repo):
- `.github/workflows/azure-webapp.yml`

## 5. Deploy

Push to `main`:
```
git push origin main
```

Your app will deploy automatically.

## Troubleshooting

- **Application Error**: check **Log stream** in Azure Portal.
- **Build fails**: verify `AZURE_WEBAPP_PUBLISH_PROFILE` is correct and complete.
- **MongoDB connection errors**: confirm `MONGO_URI` is set and the Atlas IP allowlist includes Azure.
