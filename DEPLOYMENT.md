# Docker Deployment to Azure Free Tier - Step by Step Guide

> **📱 Prefer using the Azure Portal UI?** See **[DEPLOYMENT-UI.md](./DEPLOYMENT-UI.md)** for a complete step-by-step guide using the web interface (no command line needed)!

## Prerequisites

1. **Azure Account** (Free tier available at https://azure.microsoft.com/free/)
2. **Azure CLI** installed ([Install guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
3. **Docker** installed locally (optional, for testing)
4. **Git** installed

---

## Step 1: Test Docker Locally (Optional but Recommended)

```bash
# Build the Docker image
docker build -t dawairx:latest .

# Run locally to test
docker run -p 8000:8000 \
  -e MONGODB_URI="your_mongodb_connection_string" \
  -e SECRET_KEY="your_secret_key" \
  dawairx:latest

# Test in browser: http://localhost:8000
```

---

## Step 2: Login to Azure

```bash
# Login to Azure
az login

# Verify you're logged in
az account show
```

---

## Step 3: Create Azure Resources

```bash
# Create resource group (free)
az group create \
  --name DawaiRxRG \
  --location eastus

# Create Azure Container Registry (to store your Docker image)
# Note: Basic tier is free for first 30 days, then ~$5/month
az acr create \
  --resource-group DawaiRxRG \
  --name dawairxregistry \
  --sku Basic \
  --admin-enabled true

# Login to your container registry
az acr login --name dawairxregistry
```

---

## Step 4: Build and Push Docker Image to Azure

```bash
# Build and push image to Azure Container Registry
# MUST use az acr build - it builds for linux/amd64 (Azure's architecture)
# If you use "docker build" + "docker push" on Mac M1/M2, you'll get "exec format error"
az acr build \
  --registry dawairxregistry \
  --image dawairx:latest \
  --file Dockerfile . \
  --platform linux/amd64
```

**Important:** Always use `az acr build` (not `docker build` + `docker push`). On Mac with Apple Silicon, a locally-built image is arm64 and will fail on Azure with "exec format error".

---

## Step 5: Deploy to Azure App Service (Free Tier)

### Option A: App Service with Docker (Recommended for Free Tier)

```bash
# Create FREE App Service Plan
az appservice plan create \
  --name DawaiRxFreePlan \
  --resource-group DawaiRxRG \
  --sku FREE \
  --is-linux

# Create Web App with Docker image
az webapp create \
  --resource-group DawaiRxRG \
  --plan DawaiRxFreePlan \
  --name dawairx-app \
  --deployment-container-image-name dawairxregistry.azurecr.io/dawairx:latest

# Configure container registry authentication
az webapp config container set \
  --name dawairx-app \
  --resource-group DawaiRxRG \
  --docker-custom-image-name dawairxregistry.azurecr.io/dawairx:latest \
  --docker-registry-server-url https://dawairxregistry.azurecr.io \
  --docker-registry-server-user dawairxregistry \
  --docker-registry-server-password $(az acr credential show --name dawairxregistry --query "passwords[0].value" --output tsv)

# Set environment variables
az webapp config appsettings set \
  --resource-group DawaiRxRG \
  --name dawairx-app \
  --settings \
    MONGODB_URI="your_mongodb_connection_string" \
    SECRET_KEY="your_secret_key" \
    PORT=8000 \
    WEBSITES_PORT=8000 \
    UPLOAD_DIR="/tmp/uploads" \
    OUTPUT_DIR="/tmp/outputs"
```

**Your app will be available at:** `https://dawairx-app.azurewebsites.net`

---

## Step 6: Configure MongoDB

### Option A: MongoDB Atlas (Free Tier - Recommended)

1. Go to https://www.mongodb.com/cloud/atlas
2. Create free account (512 MB free)
3. Create cluster
4. Get connection string
5. Update `MONGODB_URI` in Azure:

```bash
az webapp config appsettings set \
  --resource-group DawaiRxRG \
  --name dawairx-app \
  --settings MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/dawai_rx?retryWrites=true&w=majority"
```

**Important:** In MongoDB Atlas, add Azure IP ranges to Network Access:
- Go to Network Access → Add IP Address → Allow Access from Anywhere (0.0.0.0/0) for testing

---

## Step 7: Update Your App (When You Make Changes)

```bash
# Rebuild and push new image
az acr build \
  --registry dawairxregistry \
  --image dawairx:latest \
  --file Dockerfile .

# Restart the web app to pick up new image
az webapp restart \
  --resource-group DawaiRxRG \
  --name dawairx-app
```

---

## Step 8: View Logs (Troubleshooting)

```bash
# View live logs
az webapp log tail \
  --resource-group DawaiRxRG \
  --name dawairx-app

# Or view in Azure Portal:
# Go to your Web App → Log stream
```

---

## Important Notes for Free Tier

### Limitations:
1. **App Sleeps**: After 20 minutes of inactivity, app goes to sleep
   - **Solution**: Use free ping service like UptimeRobot to ping every 5 minutes
   - Or accept 10-30 second cold start delay

2. **Limited Resources**: 165 MB RAM, 60 minutes CPU/day
   - May be slow with large files
   - Monitor usage in Azure Portal

3. **Shared Infrastructure**: May experience occasional slowness

### Prevent App Sleep (Optional):
1. Sign up at https://uptimerobot.com (free)
2. Add monitor: URL = `https://dawairx-app.azurewebsites.net`
3. Set interval to 5 minutes
4. This keeps your app awake

---

## Alternative: Azure Container Instances (Very Limited Free Tier)

If App Service doesn't work, try Container Instances:

```bash
# Create container instance (very limited - 0.1 CPU, 0.1 GB RAM)
az container create \
  --resource-group DawaiRxRG \
  --name dawairx-container \
  --image dawairxregistry.azurecr.io/dawairx:latest \
  --registry-login-server dawairxregistry.azurecr.io \
  --registry-username dawairxregistry \
  --registry-password $(az acr credential show --name dawairxregistry --query "passwords[0].value" --output tsv) \
  --cpu 0.1 \
  --memory 0.1 \
  --ip-address Public \
  --ports 8000 \
  --environment-variables \
    MONGODB_URI="your_mongodb_uri" \
    SECRET_KEY="your_secret_key" \
    PORT=8000

# Get public IP
az container show \
  --resource-group DawaiRxRG \
  --name dawairx-container \
  --query ipAddress.ip \
  --output tsv
```

**Note:** Container Instances free tier is VERY limited and may not work well for your app.

---

## Cost Summary

| Service | Free Tier | After Free Tier |
|---------|-----------|-----------------|
| App Service (F1) | **FREE** | $0/month (always free) |
| Container Registry (Basic) | Free 30 days | ~$5/month |
| MongoDB Atlas | **FREE** (512 MB) | Free tier available |
| **Total** | **FREE** | **~$5/month** |

---

## Quick Commands Reference

```bash
# View your app
az webapp browse --resource-group DawaiRxRG --name dawairx-app

# Check app status
az webapp show --resource-group DawaiRxRG --name dawairx-app --query state

# View all settings
az webapp config appsettings list --resource-group DawaiRxRG --name dawairx-app

# Delete everything (when done testing)
az group delete --name DawaiRxRG --yes --no-wait
```

---

## Troubleshooting

### App not starting?
1. Check logs: `az webapp log tail --resource-group DawaiRxRG --name dawairx-app`
2. Check MongoDB connection string
3. Verify environment variables are set

### Can't access from mobile?
1. Check CORS is enabled (already in code)
2. Verify app is running (not sleeping)
3. Check firewall/network settings

### App is slow?
1. Free tier has limited resources
2. Consider upgrading to Basic tier ($13/month) for better performance

---

## Next Steps

1. ✅ Test locally with Docker
2. ✅ Deploy to Azure
3. ✅ Configure MongoDB Atlas
4. ✅ Test from mobile/other devices
5. ✅ Set up ping service (optional)
6. ✅ Monitor usage

**Your app is now accessible from anywhere!** 🎉



