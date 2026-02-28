# VeriGraph Backend

FastAPI backend for VeriGraph application.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create .env file:
```bash
cp .env.example .env
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

