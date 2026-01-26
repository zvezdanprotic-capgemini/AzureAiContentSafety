# Plan: Run frontend + backend as Azure Container Apps (ACR-backed)

This plan is split into two phases:

- Phase 1: local containerization + local Docker testing (using the existing repo-root `.env`)
- Phase 2: Azure deployment (ACR + Azure Container Apps)

It assumes:

- You already have (or will be given) a Resource Group and Region.
- Azure CLI is installed and logged in.
- API keys are stored in Azure Key Vault.
- Autoscaling is fixed at 1 replica (demo stability).

## 0) Current state (repo as-is)

- Backend: FastAPI (`backend/app.py`) exposes `POST /api/chat` and `GET /api/health`.
- Frontend: Vite React app in `frontend/`.
  - Currently hardcodes backend URL: `http://localhost:8000/api/chat`.
- Deployment docs: `AZURE_README.md` targets Azure Web App for Containers (not Container Apps).
- Docker: no Dockerfiles yet.

## 1) Target architecture (what we want)

### 1.1 Public/private boundary

- Frontend Container App: **external ingress** (public)
- Backend Container App: **internal ingress** (private)

### 1.2 How browser calls backend (avoid CORS by design)

The browser cannot reach an internal-only backend. To keep the backend non-public while still supporting browser calls:

- Serve the frontend via Nginx, and proxy `/api/*` from the frontend container to the internal backend.

Result:

- Browser calls: `https://<frontend-fqdn>/api/chat` (same-origin)
- Nginx proxies to: `http://<backend-internal-fqdn>:8000/api/chat`
- CORS is effectively removed from the equation.

## Phase 1 — Local containerization & testing

## 2) Repo changes required

### 2.1 Frontend: use relative API URL

Tasks:

- Change the frontend code to call a relative API path:
  - from `axios.post('http://localhost:8000/api/chat', ...)`
  - to `axios.post('/api/chat', ...)`

Acceptance criteria:

- Frontend works when served behind a reverse proxy.

### 2.2 Frontend local dev: Vite proxy (optional but recommended)

For local development (without Docker), keep it convenient:

- Add Vite dev proxy in `frontend/vite.config.ts`:
  - proxy `/api` -> `http://localhost:8000`

Acceptance criteria:

- Local dev: `npm run dev` works with backend running on port 8000.

### 2.3 Backend: port strategy

Two acceptable options:

- Keep backend listening on 8000 and configure ACA `targetPort=8000`.
- Or read `PORT` and listen on that.

For least change, keep `8000`.

## 3) Dockerization tasks

### 3.1 Root `.dockerignore`

Add a root `.dockerignore` to avoid copying unnecessary files (and secrets):

- `.git/`
- `.venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `**/__pycache__/`
- `.env` (never bake local secrets)

### 3.2 Backend image

Create `backend/Dockerfile`:

- Base image: `python:3.13-slim` (or `3.12-slim`)
- Install `requirements.txt`
- Copy `backend/`
- Start command: `uvicorn backend.app:app --host 0.0.0.0 --port 8000`

Local run (recommended via docker compose; see below):

```bash
docker build -t safebot-backend:local -f backend/Dockerfile .
docker run --rm -p 8000:8000 \
  -e AZURE_OPENAI_API_KEY=... \
  -e AZURE_OPENAI_API_VERSION=... \
  -e AZURE_OPENAI_ENDPOINT=... \
  -e AZURE_OPENAI_DEPLOYMENT_NAME=... \
  -e AZURE_CONTENT_SAFETY_ENDPOINT=... \
  -e AZURE_CONTENT_SAFETY_KEY=... \
  safebot-backend:local
```

### 3.3 Frontend image (Nginx + reverse proxy)

Create `frontend/Dockerfile` (multi-stage):

1) Build (Node): `npm ci` + `npm run build`
2) Runtime (nginx): serve static files + proxy `/api/` to backend

Important: backend URL must not be hardcoded.

Add:

- `frontend/nginx.conf.template`
- `frontend/docker-entrypoint.sh` to render config via `envsubst` using `BACKEND_ORIGIN`

Local run (proxying to a locally running backend container):

```bash
docker build -t safebot-frontend:local -f frontend/Dockerfile frontend
docker run --rm -p 8080:80 \
  -e BACKEND_ORIGIN=http://host.docker.internal:8000 \
  safebot-frontend:local
```

Validate locally:

- Open `http://localhost:8080`
- `curl -sS http://localhost:8080/api/health`
- `curl -sS -X POST http://localhost:8080/api/chat -H 'Content-Type: application/json' -d '{"message":"hello"}'`

### 3.4 docker-compose for one-command local testing (recommended)

Create `docker-compose.yml` that uses the existing repo-root `.env` via `env_file` for the backend service.

- backend: `8000:8000`
- frontend: `8080:80` and `BACKEND_ORIGIN=http://backend:8000`

Acceptance criteria:

- `docker compose up --build` and then browse `http://localhost:8080`.

## Phase 2 — Azure deployment (ACR + Azure Container Apps)

For step-by-step commands you can follow interactively, use: `PHASE2_RUNBOOK_CONTAINER_APPS.md`.

## 4) Azure resources to create

You said you already have access to a Resource Group. This phase assumes:

- `RG=<your-resource-group>`
- `LOCATION=<your-region>` (you will receive it)

### 4.1 Create Azure Container Registry (ACR)

```bash
ACR=<youracrname> # must be globally unique, lowercase

az acr create \
  -g $RG -n $ACR \
  --sku Basic \
  --admin-enabled false
```

### 4.2 Create Azure Container Apps Environment

```bash
ACA_ENV=<your-aca-env-name>

az containerapp env create \
  -g $RG -n $ACA_ENV -l $LOCATION
```

## 5) Identity and Key Vault integration

You want API keys in Azure Key Vault. Recommended approach (least code change):

- Use Managed Identity + Key Vault secret references in Container Apps.
- Container Apps injects the secret values into container env vars at runtime.
- The backend code can keep reading `os.environ[...]` like it does now.

### 5.1 Create a User Assigned Managed Identity (UAMI)

```bash
UAMI=<your-uami-name>
az identity create -g $RG -n $UAMI -l $LOCATION

UAMI_ID=$(az identity show -g $RG -n $UAMI --query id -o tsv)
UAMI_PRINCIPAL_ID=$(az identity show -g $RG -n $UAMI --query principalId -o tsv)
```

### 5.2 Grant ACR pull to the UAMI

```bash
ACR_ID=$(az acr show -g $RG -n $ACR --query id -o tsv)

az role assignment create \
  --assignee-object-id $UAMI_PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal \
  --role AcrPull \
  --scope $ACR_ID
```

### 5.3 Grant Key Vault secret read to the UAMI

This depends on your Key Vault permission model.

If your Key Vault uses RBAC:

```bash
KV=<your-keyvault-name>
KV_ID=$(az keyvault show -g $RG -n $KV --query id -o tsv)

az role assignment create \
  --assignee-object-id $UAMI_PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope $KV_ID
```

If your Key Vault uses access policies (legacy model), you’ll instead use `az keyvault set-policy`.

### 5.4 Decide secret names in Key Vault

Suggested Key Vault secret names (example):

- `azure-openai-api-key`
- `azure-content-safety-key`

And you’ll also set non-secret env vars directly on the backend app:

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_DEPLOYMENT_NAME`
- `AZURE_CONTENT_SAFETY_ENDPOINT`

## 6) Build and push images to ACR

Because you’re on macOS (likely ARM64), use ACR cloud build to guarantee linux/amd64 images:

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

## 7) Create Container Apps

Set these once:

```bash
BACKEND_APP=safebot-backend
FRONTEND_APP=safebot-frontend
ACR_LOGIN_SERVER=$(az acr show -g $RG -n $ACR --query loginServer -o tsv)
```

### 7.1 Create backend Container App (internal only)

- Ingress: internal
- Port: 8000
- Replicas: min=1, max=1

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
    AZURE_OPENAI_ENDPOINT=https://<your-openai-resource>.openai.azure.com \
    AZURE_OPENAI_API_VERSION=2024-12-01-preview \
    AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-mini \
    AZURE_CONTENT_SAFETY_ENDPOINT=https://<your-content-safety>.cognitiveservices.azure.com
```

Now attach Key Vault-backed secrets to the backend app.

You need the Key Vault secret URIs (IDs):

```bash
OPENAI_KEY_SECRET_ID=$(az keyvault secret show --vault-name $KV --name azure-openai-api-key --query id -o tsv)
CS_KEY_SECRET_ID=$(az keyvault secret show --vault-name $KV --name azure-content-safety-key --query id -o tsv)
```

Then set Container Apps secrets as Key Vault references and map to env vars:

```bash
az containerapp secret set \
  -g $RG -n $BACKEND_APP \
  --secrets \
    AZURE_OPENAI_API_KEY=keyvaultref:$OPENAI_KEY_SECRET_ID,identityref:$UAMI_ID \
    AZURE_CONTENT_SAFETY_KEY=keyvaultref:$CS_KEY_SECRET_ID,identityref:$UAMI_ID

az containerapp update \
  -g $RG -n $BACKEND_APP \
  --set-env-vars \
    AZURE_OPENAI_API_KEY=secretref:AZURE_OPENAI_API_KEY \
    AZURE_CONTENT_SAFETY_KEY=secretref:AZURE_CONTENT_SAFETY_KEY
```

### 7.2 Create frontend Container App (public)

- Ingress: external
- Port: 80
- Replicas: min=1, max=1

First, get backend internal FQDN:

```bash
BACKEND_FQDN=$(az containerapp show -g $RG -n $BACKEND_APP --query "properties.configuration.ingress.fqdn" -o tsv)
```

Then create frontend app, passing `BACKEND_ORIGIN`:

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
  --env-vars BACKEND_ORIGIN=http://$BACKEND_FQDN:8000
```

Get the frontend URL:

```bash
az containerapp show -g $RG -n $FRONTEND_APP --query "properties.configuration.ingress.fqdn" -o tsv
```

## 8) Validation checklist (Azure)

1) Frontend is reachable publicly.
2) Browser devtools show requests going to `https://<frontend>/api/*`.
3) Backend direct access from the internet should fail:

   - There should be no public backend URL exposed.

4) Frontend `/api/health` works.
5) Chat works end-to-end.

## 9) Notes on CORS

With the reverse proxy design, browser traffic is same-origin, so CORS is not required.

If you later decide to expose the backend publicly, you must:

- Restrict CORS to the frontend origin.
- Add authentication/authorization.

## 10) Alternative approach: backend retrieves secrets directly at runtime

If you prefer the backend to fetch from Key Vault itself (code change):

- Add dependencies: `azure-identity`, `azure-keyvault-secrets`.
- Use `DefaultAzureCredential()` and `SecretClient` to load secrets at startup.
- Requires giving the backend identity access to Key Vault.

For this repo/demo, Key Vault references via Container Apps is the simplest and keeps secrets out of images.
