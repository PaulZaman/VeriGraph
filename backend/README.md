# VeriGraph Backend

FastAPI backend for VeriGraph - **Lightweight API Layer** (No ML Dependencies)

## 🏗️ Architecture

This backend is part of a **3-tier architecture**:

```
Frontend (React) → Backend (FastAPI) → MacMini ML Server
                         ↓
                  PostgreSQL (Neon)
```

**Backend Role:**
- ✅ Receives fact-check requests
- ✅ Creates tasks in PostgreSQL
- ✅ Returns task status and results
- ❌ Does NOT run ML inference (handled by MacMini server)

**Why this architecture?**
- Fast Docker builds (~30 seconds vs 5 minutes)
- Reduced Fly.io costs (no ML on expensive cloud VMs)
- ML runs on local MacMini M1 hardware
- Scalable API layer independent of ML inference

## 📦 Dependencies

**Minimal & Fast:**
- FastAPI - Web framework
- SQLAlchemy - Database ORM
- psycopg2 - PostgreSQL driver
- Pydantic - Data validation

**No ML Libraries:** torch, transformers, mlflow, spacy moved to MacMini server

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies and setup:
```bash
# Quick setup (recommended)
chmod +x setup.sh
./setup.sh

# Or manually:
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

3. Create .env file:
```bash
cp .env.example .env
```

4. Ensure a model is in Staging (required for predictions):
```bash
# Run this script to promote version 1 to Staging
python scripts/promote_v1_to_staging.py

# Or ask your friend (repo owner) to promote it in DagHub UI
```

## Running the Server

### Local Development
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at http://localhost:8000

API Documentation: http://localhost:8000/docs

### Docker (Local)

Build and run with Docker Compose:
```bash
docker-compose up --build
```

Or build and run manually:
```bash
docker build -t verigraph-backend .
docker run -p 8000:8080 verigraph-backend
```

## Deployment to Fly.io

We have two environments configured:
- **Staging**: `verigraph-api-staging` (fly.staging.toml)
- **Production**: `verigraph-api` (fly.toml)

### Initial Setup

1. Install Fly CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Login to Fly.io:
```bash
fly auth login
```

3. Create the apps (one-time setup):
```bash
# Create staging app
fly apps create verigraph-api-staging

# Create production app
fly apps create verigraph-api
```

### Configure Environment Variables

1. Update your environment files:
   - `.env.staging` - Staging environment variables
   - `.env.prod` - Production environment variables

2. Push secrets to Fly.io using the automated script:
```bash
# Push secrets to staging
./deploy-secrets.sh staging

# Push secrets to production
./deploy-secrets.sh prod

# Push secrets to both environments
./deploy-secrets.sh all
```

Or manually set secrets:
```bash
fly secrets set FRONTEND_URL=https://your-frontend.com --app verigraph-api-staging
```

### Deploy

Use the deployment script:

```bash
# Deploy to staging
./deploy.sh staging

# Deploy to production (with confirmation prompt)
./deploy.sh prod
```

Or deploy manually:

```bash
# Deploy to staging
fly deploy --config fly.staging.toml --app verigraph-api-staging

# Deploy to production
fly deploy --config fly.toml --app verigraph-api
```

### Monitor and Manage

```bash
# Check app status
fly status --app verigraph-api-staging
fly status --app verigraph-api

# View logs
fly logs --app verigraph-api-staging
fly logs --app verigraph-api

# Open app in browser
fly open --app verigraph-api-staging
fly open --app verigraph-api

# SSH into the machine
fly ssh console --app verigraph-api-staging

# View secrets (names only, not values)
fly secrets list --app verigraph-api-staging
```

### Deployment Workflow

1. Make changes to your code
2. Test locally
3. Deploy to staging: `./deploy.sh staging`
4. Test on staging
5. If all good, deploy to production: `./deploy.sh prod`

## Environment Variables

- `PORT`: Server port (default: 8000 local, 8080 production)
- `HOST`: Host address (default: 0.0.0.0)
- `ENVIRONMENT`: development, staging, or production
- `FRONTEND_URL`: Frontend URL for CORS
- `DEBUG`: Debug mode (true/false)
- `DAGSHUB_REPO`: DagHub repository (e.g., MarcoSrhl/NLP-Fact-checking)
- `MODEL_NAME`: Name of the MLflow model
- `MODEL_VERSION`: Model version to use (latest, production, or version number)
- `DAGSHUB_USER`: (Optional) DagHub username for private repos
- `DAGSHUB_TOKEN`: (Optional) DagHub access token for private repos

## Model Integration

VeriGraph uses ML models hosted on DagHub for fact-checking predictions. 

**Documentation:**
- [docs/MODEL_INTEGRATION.md](docs/MODEL_INTEGRATION.md) - Technical details on model loading
- [docs/PRODUCTION_WORKFLOW.md](docs/PRODUCTION_WORKFLOW.md) - Model promotion and deployment process
- [docs/DAGSHUB_AUTH.md](docs/DAGSHUB_AUTH.md) - Setting up DagHub authentication

### Quick Start

1. Models are automatically loaded from DagHub on startup
2. Configure the model in your `.env` file:
```bash
DAGSHUB_REPO=MarcoSrhl/NLP-Fact-checking
MODEL_NAME=fact-checker-bert
MODEL_STAGE=Staging  # Use Production for production environment
```

3. The API will run in mock mode if the model fails to load (network issues, etc.)

### Model Stages

- **Staging**: Used for testing and local development
- **Production**: Automatically promoted when code is pushed to `main` branch

When you push to `main`, the Staging model is automatically promoted to Production and deployed to Fly.io. See [docs/PRODUCTION_WORKFLOW.md](docs/PRODUCTION_WORKFLOW.md) for details.

### DagHub Repository

- Repository: https://dagshub.com/MarcoSrhl/NLP-Fact-checking
- Experiments: https://dagshub.com/MarcoSrhl/NLP-Fact-checking/experiments

