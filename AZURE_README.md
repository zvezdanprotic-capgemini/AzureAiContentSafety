# Azure Deployment Guide

This guide walks you through deploying the Safe LLM Bot FastAPI application to Azure Web App using Azure Container Registry.

## Prerequisites

- Azure CLI installed and configured
- Azure subscription with appropriate permissions
- Application configured with Azure OpenAI and Content Safety services

**Optional**: 
- Docker environment (see `DOCKER_README.md`) - only needed for local testing
- The deployment method in this guide uses Azure's cloud build, so local Docker is not required

## Required Azure Services

1. **Azure Container Registry (ACR)** - Store Docker images
2. **Azure Web App** - Host the containerized application
3. **Azure OpenAI Service** - AI chat functionality
4. **Azure Content Safety** - Content moderation

## Step-by-Step Deployment

### 1. Create Azure Container Registry

```bash
# Create resource group (if needed)
az group create --name <your-resource-group> --location <region>

# Create Azure Container Registry
az acr create --resource-group <your-resource-group> \
  --name <your-registry-name> \
  --sku Basic \
  --admin-enabled true
```

**Example**:
```bash
az group create --name rg-bh-nl-prz-01 --location westus2
az acr create --resource-group rg-bh-nl-prz-01 \
  --name acrcontentsafety2 \
  --sku Basic \
  --admin-enabled true
```

### 2. Build and Push Docker Image

**Important**: Use Azure Container Registry's cloud build to ensure x86_64 compatibility.

**Note**: This method builds the image entirely in Azure's cloud - **no local Docker setup required** for this step. However, if you want to test locally first, see `DOCKER_README.md` for local Docker setup.

```bash
# Login to Azure Container Registry
az acr login --name <your-registry-name>

# Build and push image directly in ACR (ensures x86_64 compatibility)
# This uploads your source code and builds in Azure's cloud
az acr build --registry <your-registry-name> \
  --image safebotapi:latest \
  --platform linux/amd64 .
```

**What this does**:
- Uploads your source code to Azure
- Builds the Docker image on Azure's x86_64 infrastructure
- Stores the built image directly in your container registry
- No local Docker daemon required

**Example**:
```bash
az acr login --name acrcontentsafety2
az acr build --registry acrcontentsafety2 \
  --image safebotapi:latest \
  --platform linux/amd64 .
```

### 3. Create Azure Web App

```bash
# Create App Service Plan (B1 tier recommended for production)
az appservice plan create --name <plan-name> \
  --resource-group <your-resource-group> \
  --sku B1 \
  --is-linux

# Create Web App with container
az webapp create --resource-group <your-resource-group> \
  --plan <plan-name> \
  --name <app-name> \
  --deployment-container-image-name <your-registry-name>.azurecr.io/safebotapi:latest
```

**Example**:
```bash
az appservice plan create --name asp-contentsafety \
  --resource-group rg-bh-nl-prz-01 \
  --sku B1 \
  --is-linux

az webapp create --resource-group rg-bh-nl-prz-01 \
  --plan asp-contentsafety \
  --name testcontentsafety \
  --deployment-container-image-name acrcontentsafety2.azurecr.io/safebotapi:latest
```

### 4. Configure Container Registry Authentication

```bash
# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name <your-registry-name> --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name <your-registry-name> --query "passwords[0].value" -o tsv)

# Configure Web App to use ACR
az webapp config container set --name <app-name> \
  --resource-group <your-resource-group> \
  --docker-custom-image-name <your-registry-name>.azurecr.io/safebotapi:latest \
  --docker-registry-server-url https://<your-registry-name>.azurecr.io \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD
```

### 5. Configure Application Settings (Environment Variables)

```bash
# Set application environment variables
az webapp config appsettings set --resource-group <your-resource-group> \
  --name <app-name> \
  --settings \
    AZURE_OPENAI_API_KEY="<your-openai-key>" \
    AZURE_OPENAI_ENDPOINT="<your-openai-endpoint>" \
    AZURE_OPENAI_API_VERSION="2024-12-01-preview" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini" \
    AZURE_CONTENT_SAFETY_ENDPOINT="<your-content-safety-endpoint>" \
    AZURE_CONTENT_SAFETY_KEY="<your-content-safety-key>"
```

### 6. Restart and Test Application

```bash
# Restart the web app to apply changes
az webapp restart --name <app-name> --resource-group <your-resource-group>

# Test health endpoint
curl -X GET "https://<app-name>.azurewebsites.net/api/health"

# Test chat endpoint
curl -X POST "https://<app-name>.azurewebsites.net/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

## Complete Example Commands

Here's a complete example using our deployment:

```bash
# 1. Create resources
az login

az acr create --resource-group rg-bh-nl-prz-01 --name acrcontentsafety2 --sku Basic --admin-enabled true

# 2. Build and push image
az acr login --name acrcontentsafety2
az acr build --registry acrcontentsafety2 --image safebotapi:latest --platform linux/amd64 .

# 3. Create web app
az appservice plan create --name asp-contentsafety --resource-group rg-bh-nl-prz-01 --sku B1 --is-linux
az webapp create --resource-group rg-bh-nl-prz-01 --plan asp-contentsafety --name testcontentsafety --deployment-container-image-name acrcontentsafety2.azurecr.io/safebotapi:latest

# 4. Configure ACR authentication
ACR_USERNAME=$(az acr credential show --name acrcontentsafety2 --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name acrcontentsafety2 --query "passwords[0].value" -o tsv)
az webapp config container set --name testcontentsafety --resource-group rg-bh-nl-prz-01 --docker-custom-image-name acrcontentsafety2.azurecr.io/safebotapi:latest --docker-registry-server-url https://acrcontentsafety2.azurecr.io --docker-registry-server-user $ACR_USERNAME --docker-registry-server-password $ACR_PASSWORD

# 5. Set environment variables (replace with your actual values)
az webapp config appsettings set --resource-group rg-bh-nl-prz-01 --name testcontentsafety --settings AZURE_OPENAI_API_KEY="your-key" AZURE_OPENAI_ENDPOINT="your-endpoint" AZURE_OPENAI_API_VERSION="2024-12-01-preview" AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini" AZURE_CONTENT_SAFETY_ENDPOINT="your-content-safety-endpoint" AZURE_CONTENT_SAFETY_KEY="your-content-safety-key"

# 6. Test deployment
az webapp restart --name testcontentsafety --resource-group rg-bh-nl-prz-01

curl -X GET "https://testcontentsafety.azurewebsites.net/api/health"
```

## Architecture Compatibility

### ⚠️ Important: ARM64 vs x86_64

**Problem**: Docker images built on Apple Silicon Macs (ARM64) are incompatible with Azure Web Apps (x86_64).

**Solution**: Always use Azure Container Registry's cloud build:

```bash
# ❌ Don't do this for Azure deployment (ARM64 incompatible)
docker build -t safebotapi .
docker push your-registry.azurecr.io/safebotapi:latest

# ✅ Do this instead (x86_64 compatible)
az acr build --registry your-registry --image safebotapi:latest --platform linux/amd64 .
```

### Error Symptoms

If you deploy an incompatible ARM64 image, you'll see:
- HTTP 503 Service Unavailable
- Container logs showing: `exec format error`
- Process exits with code 255

## Monitoring and Troubleshooting

### View Application Logs

```bash
# Stream live logs
az webapp log tail --name <app-name> --resource-group <your-resource-group>

# Download log files
az webapp log download --name <app-name> --resource-group <your-resource-group>
```

### Common Issues

1. **503 Service Unavailable**
   - Check container logs for startup errors
   - Verify environment variables are set correctly
   - Ensure image architecture is x86_64

2. **"exec format error"**
   - Image was built on ARM64 (Apple Silicon)
   - Rebuild using `az acr build` with `--platform linux/amd64`

3. **Authentication Errors**
   - Verify Azure OpenAI and Content Safety keys
   - Check endpoint URLs are correct
   - Ensure services are in the same region for best performance

### Health Checks

The application provides health endpoints:

- **Health Check**: `GET /api/health` → `{"status":"ok"}`
- **Main API**: `POST /api/chat` with JSON body `{"message": "text"}`

## Updating the Application

To deploy updates:

```bash
# 1. Build new image version
az acr build --registry <your-registry-name> \
  --image safebotapi:latest \
  --platform linux/amd64 .

# 2. Restart web app to pull new image
az webapp restart --name <app-name> --resource-group <your-resource-group>
```

## Security Considerations

1. **Environment Variables**: Store sensitive data in Azure Key Vault for production
2. **Network Security**: Configure virtual networks and private endpoints
3. **Authentication**: Implement proper authentication for the API endpoints
4. **HTTPS**: Azure Web Apps provide HTTPS by default
5. **Content Safety**: The app includes Azure Content Safety integration for message filtering

## Cost Optimization

- **App Service Plan**: Start with B1, scale as needed
- **Container Registry**: Basic tier sufficient for small projects
- **Resource Group**: Group related resources for easier management
- **Region**: Keep all services in the same region to reduce latency and data transfer costs

## Production Checklist

- [ ] Environment variables configured securely
- [ ] Health checks responding correctly
- [ ] Logging configured for monitoring
- [ ] Backup and disaster recovery planned
- [ ] SSL/TLS certificates configured
- [ ] Authentication and authorization implemented
- [ ] Rate limiting configured
- [ ] Content safety policies reviewed
- [ ] Performance testing completed
- [ ] Cost monitoring alerts set up

## Useful Commands

```bash
# Check app status
az webapp show --name <app-name> --resource-group <your-resource-group> --query "state"

# Scale app
az appservice plan update --name <plan-name> --resource-group <your-resource-group> --sku <new-sku>

# View app settings
az webapp config appsettings list --name <app-name> --resource-group <your-resource-group>

# View container settings
az webapp config container show --name <app-name> --resource-group <your-resource-group>

# Delete resources (cleanup)
az group delete --name <your-resource-group> --yes --no-wait
```

## Additional Resources

- [Azure Container Registry Documentation](https://docs.microsoft.com/azure/container-registry/)
- [Azure Web Apps Documentation](https://docs.microsoft.com/azure/app-service/)
- [Azure OpenAI Service Documentation](https://docs.microsoft.com/azure/cognitive-services/openai/)
- [Azure Content Safety Documentation](https://docs.microsoft.com/azure/cognitive-services/content-safety/)