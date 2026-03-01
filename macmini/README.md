# MacMini ML Inference Server

This server runs locally on a MacMini and handles ML model inference for VeriGraph.

## Architecture

- **Backend** (Fly.io): Receives API requests, writes to Neon PostgreSQL
- **MacMini Server** (Local): Polls database, runs ML inference, updates results
- **Database** (Neon PostgreSQL): Queue for verification tasks

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

2. Configure environment variables (`.env`):
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. Run the server:
   ```bash
   python server.py
   ```

## How it works

1. Server starts and loads BOTH Staging and Production models
2. Backend receives `/verify` request
3. Backend writes task to `verifications` table with `status='pending'` and `environment='staging'` or `'production'`
4. MacMini polls database for ALL pending tasks (both environments)
5. MacMini selects the appropriate model based on `task.environment`
6. MacMini runs inference and updates task with results and `status='completed'`
7. Backend retrieves results via GET `/verify/{task_id}`

## Environment Variables

- `NEON_DB_URL`: PostgreSQL connection string
- `DAGSHUB_USER`: DagHub username
- `DAGSHUB_TOKEN`: DagHub access token
- `DAGSHUB_REPO`: DagHub repository
- `MODEL_NAME`: Model name in MLflow (same name, different stages)
- `HUGGINGFACE_MODEL`: (Optional) HuggingFace model as fallback
- `POLL_INTERVAL`: Seconds between database polls (default: 5)
- `MAX_RETRIES`: Maximum retries for failed tasks (default: 3)

**Note:** The server automatically loads BOTH Staging and Production models at startup. No need to run multiple instances.
