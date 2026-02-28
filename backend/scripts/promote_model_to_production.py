"""
Promote ML Model from Staging to Production in MLflow

This script:
1. Finds the current Staging model
2. Promotes it to Production (removes old Production first if exists)
3. Archives the old Production model
"""

import os
import sys
import mlflow
from mlflow.tracking import MlflowClient

# Configuration from environment
DAGSHUB_REPO = os.getenv("DAGSHUB_REPO", "MarcoSrhl/NLP-Fact-checking")
MODEL_NAME = os.getenv("MODEL_NAME", "fact-checker-bert")
DAGSHUB_USER = os.getenv("DAGSHUB_USER")
DAGSHUB_TOKEN = os.getenv("DAGSHUB_TOKEN")

# Set up MLflow tracking
mlflow.set_tracking_uri(f"https://dagshub.com/{DAGSHUB_REPO}.mlflow")

# Set authentication for DagHub
if DAGSHUB_USER and DAGSHUB_TOKEN:
    os.environ["MLFLOW_TRACKING_USERNAME"] = DAGSHUB_USER
    os.environ["MLFLOW_TRACKING_PASSWORD"] = DAGSHUB_TOKEN
    print(f"✓ Using DagHub authentication for user: {DAGSHUB_USER}")
else:
    print("ERROR: DAGSHUB_USER and DAGSHUB_TOKEN must be set")
    sys.exit(1)

# Initialize MLflow client
client = MlflowClient()

try:
    # Get model details
    print(f"🔍 Looking for model: {MODEL_NAME}")
    
    # Find Staging model
    staging_versions = client.get_latest_versions(MODEL_NAME, stages=["Staging"])
    if not staging_versions:
        print(f"❌ No model found in Staging for '{MODEL_NAME}'")
        sys.exit(1)
    
    staging_version = staging_versions[0]
    print(f"✓ Found Staging model: version {staging_version.version}")
    
    # Check for existing Production model
    production_versions = client.get_latest_versions(MODEL_NAME, stages=["Production"])
    if production_versions:
        old_prod_version = production_versions[0]
        print(f"📦 Current Production model: version {old_prod_version.version}")
        
        # Archive old production model
        print(f"📁 Archiving old Production model (version {old_prod_version.version})...")
        client.transition_model_version_stage(
            name=MODEL_NAME,
            version=old_prod_version.version,
            stage="Archived",
            archive_existing_versions=False
        )
        print("✓ Old Production model archived")
    else:
        print("ℹ️  No existing Production model found")
    
    # Promote Staging to Production
    print(f"🚀 Promoting version {staging_version.version} from Staging to Production...")
    client.transition_model_version_stage(
        name=MODEL_NAME,
        version=staging_version.version,
        stage="Production",
        archive_existing_versions=False
    )
    
    print("=" * 60)
    print(f"✅ Successfully promoted model to Production!")
    print(f"   Model: {MODEL_NAME}")
    print(f"   Version: {staging_version.version}")
    print(f"   Run ID: {staging_version.run_id}")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error promoting model: {str(e)}")
    sys.exit(1)
