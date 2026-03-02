# MacMini ML Inference Server

This server runs locally on a MacMini and handles GAN-based fact-checking inference for VeriGraph.

## Architecture

- **Backend** (Fly.io): Receives API requests, writes to Neon PostgreSQL
- **MacMini Server** (Local): Polls database, runs GAN inference, updates results
- **Database** (Neon PostgreSQL): Queue for verification tasks
- **MLflow/DagsHub**: Model registry for Staging and Production GAN models

## Setup

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install factcheck package (required for GAN inference)
pip install git+https://github.com/MarcoSrhl/factcheck.git

# Download spaCy language model
python -m spacy download en_core_web_sm
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
- `NEON_DB_URL`: PostgreSQL connection string
- `DAGSHUB_USER`: DagHub username (for MLflow authentication)
- `DAGSHUB_TOKEN`: DagHub access token

Optional:
- `MAX_RETRIES`: Maximum retries for failed tasks (default: 3)

### 3. Download Models

The server automatically checks for models on startup, but you can manually download them:

```bash
# Download Staging model
python download_gan_by_stage.py staging

# Download Production model
python download_gan_by_stage.py production

# Or download both at once
python download_gan_by_stage.py both
```

Models are downloaded to `models/fact-checker-gan_staging_v1/` and `models/fact-checker-gan_production_v2/`.

**Note:** Models are ~837 MB each and excluded from git. They are downloaded on-demand from DagsHub MLflow.

### 4. Run the Server

```bash
python main.py
```

## How It Works

1. **Startup**: Server checks if Staging and Production models are downloaded
   - If missing, automatically downloads them from MLflow Registry
   
2. **Polling Loop**: Every 1 second, server polls database for pending tasks
   
3. **Task Processing**:
   - Fetches tasks with `status='pending'` and `environment='staging'` or `'production'`
   - Selects appropriate GAN model based on task environment
   - Runs inference using `factcheck.infer_gan` with the local model
   - Extracts triplets from claims and scores them as REAL/FAKE
   - Updates task with results and `status='completed'`

4. **Backend Integration**:
   - Backend writes tasks to `verifications` table
   - Backend retrieves results via task ID
   - MacMini continuously processes queue

## Manual Model Testing

Test models directly without the service:

```bash
# Test with triplet (subject, relation, object)
python -m factcheck.infer_gan \
  --local models/fact-checker-gan_staging_v1/gan_model \
  "Paris" "is capital of" "France"

# Test with free-text phrase (auto-extracts triplet)
python -m factcheck.infer_gan \
  --local models/fact-checker-gan_production_v2/gan_model \
  --phrase "London is the capital of France"
```

Example output:
```
Using local model: models/fact-checker-gan_staging_v1/gan_model
Extracted triplet: (London, capital, France)

  (London, capital, France)
  Score: 0.2841 -> FAKE
```

## Model Management Scripts

### `list_mlflow_models.py`
List all fact-checker-gan models in MLflow Registry, organized by stage:

```bash
python list_mlflow_models.py
```

Shows model versions, stages (Production/Staging), and metrics (val_accuracy, etc.).

### `download_mlflow_artifacts.py`
Download model artifacts by run ID:

```bash
python download_mlflow_artifacts.py <run_id> --output <output_dir>

# Example
python download_mlflow_artifacts.py b965d1722ac64d199d9538779efeaf0d \
  --output models/my_model
```

### `download_gan_by_stage.py`
Download models by stage (recommended):

```bash
# Download specific stage
python download_gan_by_stage.py staging
python download_gan_by_stage.py production

# Download both
python download_gan_by_stage.py both
```

Automatically resolves `source_run_id` for packaged models in Model Registry.

### `test_inference.py`
Test wrapper for local inference:

```bash
# Test with triplet
python test_inference.py triplet "Paris" "is capital of" "France"

# Test with phrase
python test_inference.py phrase "The Eiffel Tower is in Paris"
```

## Database Schema

The `verifications` table:

```sql
CREATE TABLE verifications (
    id VARCHAR PRIMARY KEY,
    claim VARCHAR NOT NULL,
    environment VARCHAR NOT NULL,  -- 'staging' or 'production'
    status VARCHAR NOT NULL,       -- 'pending', 'processing', 'completed', 'failed'
    result JSON,
    error VARCHAR,
    retries INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

Create the table:
```bash
python create_db.py
```

## Model Architecture

- **Base Model**: BERT-GAN-Swap architecture
- **Discriminator**: Scores triplets as REAL (>0.5) or FAKE (<0.5)
- **Input**: Knowledge graph triplets (subject, relation, object)
- **Output**: Score between 0 and 1

### Current Model Versions

- **Staging**: Version 1, val_accuracy=0.8041
- **Production**: Version 2, val_accuracy=0.8272

Production model has higher accuracy and is used for final user-facing results.

## Troubleshooting

### Models not downloading
```bash
# Check DagsHub credentials
echo $DAGSHUB_USER
echo $DAGSHUB_TOKEN

# Test connection
python list_mlflow_models.py
```

### Inference errors
```bash
# Test model locally
python -m factcheck.infer_gan \
  --local models/fact-checker-gan_staging_v1/gan_model \
  --phrase "Paris is in France"

# Check model files exist
ls -lh models/fact-checker-gan_staging_v1/gan_model/
# Should contain: discriminator.pt, generator.pt, gan_meta.pt
```

### Database connection issues
```bash
# Test database connection
python -c "from sqlalchemy import create_engine; import os; from dotenv import load_dotenv; load_dotenv(); engine = create_engine(os.getenv('NEON_DB_URL')); print('Connected!' if engine.connect() else 'Failed')"
```

## Development

### File Structure

```
macmini/
├── main.py                        # Main service (runs continuously)
├── create_db.py                   # Database schema creation
├── download_gan_by_stage.py       # Download models by stage
├── download_mlflow_artifacts.py   # Download by run ID
├── download_gan_model.py          # Legacy download script
├── list_mlflow_models.py          # List models in registry
├── test_inference.py              # Manual inference testing
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── models/                        # Downloaded models (excluded from git)
    ├── fact-checker-gan_staging_v1/
    └── fact-checker-gan_production_v2/
```

### Adding New Features

1. Modify `main.py` for service logic
2. Test locally with `test_inference.py`
3. Use `list_mlflow_models.py` to explore available models
4. Download specific models with `download_mlflow_artifacts.py`
