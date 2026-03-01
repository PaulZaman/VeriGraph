#!/usr/bin/env python3
"""
Promote MLflow model from Staging to Production in DagHub registry.
This script transitions the current Staging model version to Production stage.
"""

import os
import sys
import mlflow
from mlflow.tracking import MlflowClient

def promote_model_to_production():
    """Promote the current Staging model to Production in DagHub"""
    
    # DagHub MLflow tracking URI
    dagshub_repo = os.getenv("DAGSHUB_REPO", "MarcoSrhl/NLP-Fact-checking")
    dagshub_user = os.getenv("DAGSHUB_USER", "MarcoSrhl")
    dagshub_token = os.getenv("DAGSHUB_TOKEN")
    model_name = os.getenv("MODEL_NAME", "fact-checker-bert")
    
    if not dagshub_token:
        print("❌ Error: DAGSHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    # Set MLflow tracking URI
    tracking_uri = f"https://dagshub.com/{dagshub_repo}.mlflow"
    os.environ["MLFLOW_TRACKING_URI"] = tracking_uri
    os.environ["MLFLOW_TRACKING_USERNAME"] = dagshub_user
    os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token
    
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    
    print(f"🔍 Checking model registry for: {model_name}")
    
    try:
        # Get the current Staging version
        staging_versions = client.get_latest_versions(model_name, stages=["Staging"])
        
        if not staging_versions:
            print(f"⚠️  No model found in Staging stage for {model_name}")
            print("   Skipping promotion - model may already be in Production")
            return
        
        staging_version = staging_versions[0]
        version_number = staging_version.version
        
        print(f"📦 Found Staging model: version {version_number}")
        print(f"   Run ID: {staging_version.run_id}")
        
        # Check if this version is already in Production
        prod_versions = client.get_latest_versions(model_name, stages=["Production"])
        if prod_versions and prod_versions[0].version == version_number:
            print(f"✅ Version {version_number} is already in Production stage")
            return
        
        # Transition to Production
        print(f"🚀 Promoting version {version_number} to Production stage...")
        client.transition_model_version_stage(
            name=model_name,
            version=version_number,
            stage="Production",
            archive_existing_versions=True  # Archive old production versions
        )
        
        print(f"✅ Successfully promoted model version {version_number} to Production!")
        print(f"   Model: {model_name}")
        print(f"   Stage: Staging → Production")
        print(f"   DagHub: https://dagshub.com/{dagshub_repo}")
        
    except Exception as e:
        print(f"❌ Error promoting model: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 DagHub Model Promotion: Staging → Production")
    print("=" * 60)
    promote_model_to_production()
    print("=" * 60)
