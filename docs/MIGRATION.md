# Migration to 3-Tier Architecture

## Overview
This branch (`feature/3rd-server`) migrates VeriGraph to a 3-tier architecture where ML inference runs on a separate MacMini server instead of in the backend.

## Architecture Changes

### Before
```
Client → Backend (FastAPI + ML Models) → Response
```

### After
```
Client → Backend (FastAPI) → PostgreSQL (Neon) ← MacMini (ML Inference)
```

## Changes Made

### Backend Changes
1. **Removed ML dependencies** from `requirements.txt`:
   - mlflow, torch, transformers, factcheck, spacy
   
2. **Added database dependencies**:
   - sqlalchemy==2.0.23
   - psycopg2-binary==2.9.9

3. **Refactored `/verify` endpoint**:
   - Now creates a task in PostgreSQL with status `pending`
   - Returns `task_id` immediately instead of running inference
   - Use `GET /verify/{task_id}` to check status and get results

4. **Updated environment variables**:
   - Added `NEON_DB_URL` for PostgreSQL connection
   - Removed DagHub credentials (moved to MacMini)
   - `MODEL_STAGE` now determines environment routing

### MacMini Server
1. **New directory**: `macmini/`
   - `server.py`: Main worker that polls DB and runs inference
   - `model_loader.py`: ML model loading code (copied from backend)
   - `requirements.txt`: All ML dependencies
   - `.env.example`: Configuration template
   - `create_db.py`: Database schema creation script

2. **Polling mechanism**:
   - Polls every 5 seconds (configurable via `POLL_INTERVAL`)
   - Processes up to 10 pending tasks per cycle
   - Updates task status: `pending` → `processing` → `completed`/`failed`
   - Retry logic: up to 3 retries for failed tasks

### Database Schema
```sql
CREATE TABLE verifications (
    id VARCHAR PRIMARY KEY,
    claim VARCHAR NOT NULL,
    environment VARCHAR NOT NULL,  -- 'staging' or 'production'
    status VARCHAR NOT NULL,        -- 'pending', 'processing', 'completed', 'failed'
    result JSON,
    error VARCHAR,
    retries INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Deployment Steps

### 1. Setup MacMini Server

```bash
cd macmini

# Create .env file
cp .env.example .env
# Edit .env with actual credentials

# Install dependencies
pip install -r requirements.txt

# Create database table (only needed once)
python create_db.py

# Start the worker
python server.py
```

### 2. Update Backend Environment Variables

Add to Fly.io secrets:
```bash
# Staging
fly secrets set NEON_DB_URL="postgresql://..." -a verigraph-api-staging

# Production
fly secrets set NEON_DB_URL="postgresql://..." -a verigraph-api
```

### 3. Deploy Backend

The backend no longer needs ML dependencies, so deployments will be faster:
```bash
cd backend
fly deploy -a verigraph-api-staging
```

### 4. Update CI/CD

Backend Docker builds will be much lighter:
- No need for base image with ML dependencies
- Build time should drop significantly
- Memory requirements reduced from 1024MB to ~256MB

## API Usage Changes

### Old API
```bash
POST /verify
{
  "claim": "The Earth is flat"
}

# Immediate response with verdict
{
  "status": "success",
  "verdict": "REFUTED",
  "confidence": 0.95,
  ...
}
```

### New API
```bash
# Step 1: Create verification task
POST /verify
{
  "claim": "The Earth is flat"
}

Response:
{
  "status": "success",
  "task_id": "abc-123-def",
  "message": "Verification task created..."
}

# Step 2: Poll for results
GET /verify/abc-123-def

Response (while pending):
{
  "task_id": "abc-123-def",
  "claim": "The Earth is flat",
  "status": "pending",
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:00:00"
}

Response (when completed):
{
  "task_id": "abc-123-def",
  "claim": "The Earth is flat",
  "status": "completed",
  "verdict": "REFUTED",
  "confidence": 0.95,
  "probabilities": {...},
  "mode": "real",
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:00:05"
}
```

## Benefits

1. **Cost Reduction**: No ML inference on Fly.io (saves ~1-2GB RAM)
2. **Faster Deployments**: Backend has minimal dependencies
3. **Separation of Concerns**: API handling vs ML inference
4. **Scalability**: Can run multiple MacMini workers for different environments
5. **Flexibility**: Easy to upgrade ML models without backend redeployment

## Testing

### Test Backend Locally
```bash
cd backend
python -m uvicorn main:app --reload

# Create task
curl -X POST http://localhost:8000/verify -H "Content-Type: application/json" -d '{"claim": "Test claim"}'

# Check status
curl http://localhost:8000/verify/{task_id}
```

### Test MacMini Worker
```bash
cd macmini
python server.py

# Monitor logs for task processing
```

### Test End-to-End
1. Start MacMini worker: `python macmini/server.py`
2. Start backend: `uvicorn backend.main:app --reload`
3. Create verification via backend API
4. Watch MacMini logs for task pickup
5. Poll backend for results

## Environment Routing

- `MODEL_STAGE=Staging` → Tasks created with `environment='staging'`
- `MODEL_STAGE=Production` → Tasks created with `environment='production'`
- Run separate MacMini workers for each environment
- Each worker only processes tasks matching its environment

## Rollback Plan

If issues arise:
1. Merge latest `main` into this branch for comparison
2. The old code is preserved in `backend/model_loader.py` (commented out)
3. Revert backend `requirements.txt` to include ML dependencies
4. Restore old `/verify` endpoint logic
5. Redeploy backend with ML support

## Next Steps

1. Update frontend to handle async verification (poll task status)
2. Add WebSocket support for real-time result streaming
3. Add task queue monitoring dashboard
4. Set up multiple MacMini workers for load balancing
5. Add task expiration/cleanup (delete old completed tasks)
