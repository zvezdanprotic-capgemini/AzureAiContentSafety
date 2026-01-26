# Phase 2 Runbook — Deploy to Azure Container Apps (ACR + Key Vault)

Goal:
- Build/push `frontend` + `backend` container images to Azure Container Registry (ACR)
- Run both as Azure Container Apps (ACA) in the same ACA Environment
- Frontend is **public** (external ingress)
- Backend is **private** (internal ingress)
- Frontend calls backend via Nginx reverse-proxy (`/api/*`) so browser traffic stays same-origin (no CORS problems)
- Secrets live in **Azure Key Vault**, accessed via **Managed Identity**
- Fixed replica count (demo): **min=1, max=1**

---

## 0) Prerequisites

- Azure CLI installed (`az version` works)
- You have access to:
  - An existing Resource Group
  - A Region (Azure location string like `swedencentral`)
  - An Azure Key Vault containing two secrets:
    - `azure-openai-api-key`
    - `azure-content-safety-key`
  - Azure OpenAI + Azure AI Content Safety endpoints/deployment name

This runbook uses bash-style variables. On macOS zsh, this works fine.

Important for your setup:

- Key Vault is in **East US**.
- Container Apps + ACR and the rest of the services are in **Sweden Central**.

This is supported. Identity/RBAC works cross-region. The main gotcha is **Key Vault networking** (firewall/private endpoints): the Container Apps runtime must be able to reach the Key Vault endpoint.

---

## 1) Azure CLI login + select subscription

```bash
# Login (interactive)
az login

# Optional: list subscriptions
az account list -o table

# Set the subscription you want to use
az account set --subscription "<subscription-id-or-name>"

# Confirm
az account show -o table
```

---

## 2) Set run variables

Fill these in (do not include secrets here):

```bash
# Required
export RG="rg-aiagentdemo"
export LOCATION="swedencentral"

# Names you choose
export ACR="crrdlyyaqgbvzus"        # globally unique, lowercase
export ACA_ENV="containerapps-env-rdlyyaqgbvzus"
# o get UAMI run az identity list -g $RG -o table and use Name column
export UAMI="id-api-rdlyyaqgbvzus"    # user assigned managed identity

export BACKEND_APP="safebot-backend"
export FRONTEND_APP="safebot-frontend"

# Key Vault
export KV="zvezdanprotic-kv1"
export KV_RG="rg-aiagentdemo"  # may differ from $RG
export KV_LOCATION="eastus"

# Non-secret runtime config
# IMPORTANT: Azure OpenAI endpoint should NOT include /openai/v1/ suffix
# The SDK adds this automatically. Use only the base URL:
export AZURE_OPENAI_ENDPOINT="https://zvezdanprotic-1427-resource.openai.azure.com/"
export AZURE_OPENAI_API_VERSION="2024-12-01-preview"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-5-mini"
export AZURE_CONTENT_SAFETY_ENDPOINT="https://zvezdanprotic-1427-resource.cognitiveservices.azure.com/"
```

---

## 3) Ensure Container Apps CLI extension is installed

```bash
az extension add --name containerapp --upgrade
```

---

## 4) Create (or verify) Azure Container Registry

Create:

```bash
az acr create \
  -g $RG -n $ACR \
  -l $LOCATION \
  --sku Basic \
  --admin-enabled false
```

Verify:

```bash
az acr show -g $RG -n $ACR -o table
export ACR_LOGIN_SERVER=$(az acr show -g $RG -n $ACR --query loginServer -o tsv)
echo $ACR_LOGIN_SERVER
```

---

## 5) Create (or verify) Azure Container Apps Environment

```bash
az containerapp env create \
  -g $RG -n $ACA_ENV \
  -l $LOCATION
```

Verify:

```bash
az containerapp env show -g $RG -n $ACA_ENV -o table
```

---

## 6) Create a User Assigned Managed Identity (UAMI)

```bash
az identity create -g $RG -n $UAMI -l $LOCATION

export UAMI_ID=$(az identity show -g $RG -n $UAMI --query id -o tsv)
export UAMI_PRINCIPAL_ID=$(az identity show -g $RG -n $UAMI --query principalId -o tsv)

echo $UAMI_ID
echo $UAMI_PRINCIPAL_ID
```

---

## 7) Grant the identity access to ACR (AcrPull)

```bash
export ACR_ID=$(az acr show -g $RG -n $ACR --query id -o tsv)

az role assignment create \
  --assignee-object-id $UAMI_PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal \
  --role AcrPull \
  --scope $ACR_ID
```

---

## 8) Grant the identity access to Key Vault secrets

First determine if your Key Vault uses RBAC or access policies.

### Option A (recommended): Key Vault RBAC

```bash
export KV_ID=$(az keyvault show -g $KV_RG -n $KV --query id -o tsv)

az role assignment create \
  --assignee-object-id $UAMI_PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope $KV_ID
```

### Option B: Key Vault access policies (legacy)

```bash
az keyvault set-policy \
  -n $KV \
  --object-id $UAMI_PRINCIPAL_ID \
  --secret-permissions get list
```

Key Vault networking note (important):

- If Key Vault has **Public network access disabled** or a restrictive firewall, your Container Apps may fail to resolve Key Vault secret refs.
- In that case you must either:
  - allow public network access (simplest for a demo), or
  - use Private Endpoint + a VNet-integrated Container Apps Environment (more involved).

---

## 9) Get Key Vault secret IDs (URIs)

These commands do not print secret values; they fetch the secret *resource IDs*.

```bash
export OPENAI_KEY_SECRET_ID=$(az keyvault secret show --vault-name $KV --name azure-openai-api-key --query id -o tsv)
export CS_KEY_SECRET_ID=$(az keyvault secret show --vault-name $KV --name azure-content-safety-key --query id -o tsv)

echo $OPENAI_KEY_SECRET_ID
echo $CS_KEY_SECRET_ID
```

---

## 10) Build and push images to ACR

Because you’re on macOS (often ARM64), prefer ACR cloud build to guarantee `linux/amd64`.

### Option A (recommended): ACR cloud build

From repo root:

```bash
az acr build --registry $ACR \
  --image safebot-backend:latest \
  --platform linux/amd64 \
  -f backend/Dockerfile .

az acr build --registry $ACR \
  --image safebot-frontend:latest \
  --platform linux/amd64 \
  -f frontend/Dockerfile frontend
```

Verify images exist:

```bash
az acr repository list --name $ACR -o table
az acr repository show-tags --name $ACR --repository safebot-backend -o table
az acr repository show-tags --name $ACR --repository safebot-frontend -o table
```

### Option B (alternative): Docker buildx (local build) + push

Only use if you know your Docker is set up for `buildx` and you want local builds.

---

## 11) Deploy backend Container App (internal ingress)

Notes:
- Ingress internal means **no public access**.
- We set non-secret env vars directly.
- We set secrets via Key Vault references and map them into env vars.
- Replica count pinned: `--min-replicas 1 --max-replicas 1`.

Create backend app:

```bash
az containerapp create \
  -g $RG -n $BACKEND_APP \
  --environment $ACA_ENV \
  --image $ACR_LOGIN_SERVER/safebot-backend:latest \
  --ingress internal \
  --target-port 8000 \
  --min-replicas 1 --max-replicas 1 \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-identity $UAMI_ID \
  --user-assigned $UAMI_ID \
  --env-vars \
    AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
    AZURE_OPENAI_API_VERSION=$AZURE_OPENAI_API_VERSION \
    AZURE_OPENAI_DEPLOYMENT_NAME=$AZURE_OPENAI_DEPLOYMENT_NAME \
    AZURE_CONTENT_SAFETY_ENDPOINT=$AZURE_CONTENT_SAFETY_ENDPOINT
```

Attach Key Vault referenced secrets and map them to env vars:

```bash
az containerapp secret set \
  -g $RG -n $BACKEND_APP \
  --secrets \
    azure-openai-api-key=keyvaultref:$OPENAI_KEY_SECRET_ID,identityref:$UAMI_ID \
    azure-content-safety-key=keyvaultref:$CS_KEY_SECRET_ID,identityref:$UAMI_ID

az containerapp update \
  -g $RG -n $BACKEND_APP \
  --set-env-vars \
    AZURE_OPENAI_API_KEY=secretref:azure-openai-api-key \
    AZURE_CONTENT_SAFETY_KEY=secretref:azure-content-safety-key
```

Get backend internal FQDN:

```bash
export BACKEND_FQDN=$(az containerapp show -g $RG -n $BACKEND_APP --query "properties.configuration.ingress.fqdn" -o tsv)
echo $BACKEND_FQDN
```

---

## 12) Deploy frontend Container App (external ingress)

Frontend is an Nginx container that needs `BACKEND_ORIGIN`.

Notes:
- Because the backend has Container Apps ingress enabled, you should use the backend ingress FQDN without specifying `:8000` (ingress listens on 80/443 and forwards to target port 8000).
- By default, Container Apps ingress redirects HTTP to HTTPS. If your frontend proxies to the backend over HTTP, the browser may receive a 301 redirect to the backend's **internal** URL (which is not reachable from the public internet). To avoid this, set `BACKEND_ORIGIN` to **https://...**.

```bash
az containerapp create \
  -g $RG -n $FRONTEND_APP \
  --environment $ACA_ENV \
  --image $ACR_LOGIN_SERVER/safebot-frontend:latest \
  --ingress external \
  --target-port 80 \
  --min-replicas 1 --max-replicas 1 \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-identity $UAMI_ID \
  --user-assigned $UAMI_ID \
  --env-vars BACKEND_ORIGIN=https://$BACKEND_FQDN
```

Get frontend public FQDN:

```bash
export FRONTEND_FQDN=$(az containerapp show -g $RG -n $FRONTEND_APP --query "properties.configuration.ingress.fqdn" -o tsv)
echo $FRONTEND_FQDN
```

---

## 13) Validate the deployment

From your laptop:

```bash
# Frontend should be reachable
curl -i https://$FRONTEND_FQDN/

# Through frontend proxy (should reach backend)
curl -sS https://$FRONTEND_FQDN/api/health

# End-to-end chat (through frontend proxy)
curl -sS -X POST https://$FRONTEND_FQDN/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Hello from Azure Container Apps"}'
```

Expected:
- `/api/health` returns `{ "status": "ok" }`
- `/api/chat` returns `{ "response": "..." }`

Backend should NOT be directly reachable publicly:
- There should be no external backend URL.

---

## 14) Troubleshooting commands

### 14.1 Inspect app state

```bash
az containerapp show -g $RG -n $BACKEND_APP -o yaml | head
az containerapp show -g $RG -n $FRONTEND_APP -o yaml | head
```

### 14.2 Logs

Container Apps supports log streaming via CLI:

```bash
az containerapp logs show -g $RG -n $BACKEND_APP --tail 200
az containerapp logs show -g $RG -n $FRONTEND_APP --tail 200

# Live stream
az containerapp logs tail -g $RG -n $BACKEND_APP
az containerapp logs tail -g $RG -n $FRONTEND_APP
```

### 14.3 Common failures

- Image pull errors:
  - Check `AcrPull` role assignment
  - Confirm `--registry-identity` and `--user-assigned` are correct
- Key Vault reference errors:
  - Confirm Key Vault permissions to the UAMI
  - Confirm secret IDs and names
  - Check backend app logs for missing env vars
- Frontend can’t reach backend:
  - Confirm backend ingress is internal and has an FQDN
  - Confirm `BACKEND_ORIGIN=https://$BACKEND_FQDN` (no port, use HTTPS)
  - Check frontend logs (nginx) for upstream errors
  - **Nginx 502 Bad Gateway**: If frontend shows 502 when proxying to HTTPS backend:
    - Ensure frontend Dockerfile includes `ca-certificates` package: `RUN apk add --no-cache gettext ca-certificates`
    - Ensure nginx.conf.template has TLS/SNI directives in the `/api/` location block:
      ```
      proxy_ssl_server_name on;
      proxy_ssl_name $proxy_host;
      proxy_set_header Host $proxy_host;
      ```
    - Rebuild and redeploy frontend after making these changes
- Backend returns "Sorry, I couldn't process your request":
  - Check `AZURE_OPENAI_ENDPOINT` format - it should be the base URL only (e.g., `https://your-resource.openai.azure.com/`) WITHOUT `/openai/v1/` suffix
  - Verify deployment name exists: `az cognitiveservices account deployment list --name <resource-name> --resource-group <rg> -o table`
  - Check API key is correctly retrieved from Key Vault
  - If using corporate proxy, check container can reach Azure OpenAI endpoint
  - Fix endpoint format:
    ```bash
    az containerapp update -g $RG -n $BACKEND_APP \
      --replace-env-vars \
        AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/ \
        AZURE_OPENAI_API_VERSION=2024-12-01-preview \
        AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name \
        AZURE_CONTENT_SAFETY_ENDPOINT=https://your-resource.cognitiveservices.azure.com/ \
        AZURE_OPENAI_API_KEY=secretref:azure-openai-api-key \
        AZURE_CONTENT_SAFETY_KEY=secretref:azure-content-safety-key
    ```

---

## 15) Cleanup (optional)

```bash
az containerapp delete -g $RG -n $FRONTEND_APP --yes
az containerapp delete -g $RG -n $BACKEND_APP --yes
az containerapp env delete -g $RG -n $ACA_ENV --yes
az acr delete -g $RG -n $ACR --yes
az identity delete -g $RG -n $UAMI
```
