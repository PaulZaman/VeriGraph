#!/usr/bin/env python3
"""
Promote model version 1 to Staging (it has the artifacts)
Run this script to make version 1 the staging model
"""

import mlflow
from mlflow.tracking import MlflowClient

# Set MLflow tracking URI to DagHub
DAGSHUB_REPO = "MarcoSrhl/NLP-Fact-checking"
mlflow.set_tracking_uri(f"https://dagshub.com/{DAGSHUB_REPO}.mlflow")

client = MlflowClient()
model_name = "fact-checker-bert"

print("=" * 80)
print("📦 Promoting Model Version 1 to Staging")
print("=" * 80)

try:
    # Get version 1
    version_1 = client.get_model_version(model_name, 1)
    print(f"\n✓ Found version 1")
    print(f"  Run ID: {version_1.run_id[:8]}...")
    print(f"  Current Stage: {version_1.current_stage}")
    
    # Check if it has artifacts
    print(f"\n📁 Checking for model artifacts...")
    artifacts = client.list_artifacts(version_1.run_id)
    model_artifacts = [a for a in artifacts if "model" in a.path]
    
    if model_artifacts:
        print(f"  ✓ Found {len(model_artifacts)} model artifact(s)")
        for art in model_artifacts[:3]:
            print(f"    - {art.path}")
    else:
        print("  ⚠️  No model artifacts found!")
        print("  This version may not work. Check other versions.")
    
    # Transition to Staging
    print(f"\n🔄 Transitioning version 1 to Staging...")
    client.transition_model_version_stage(
        name=model_name,
        version=1,
        stage="Staging"
    )
    print("  ✓ Successfully moved to Staging!")
    
    # Move other versions out of Staging
    print(f"\n🔄 Moving other versions out of Staging...")
    versions = client.search_model_versions(f"name='{model_name}'")
    for v in versions:
        if v.version != "1" and v.current_stage == "Staging":
            print(f"  Moving version {v.version} to Archived...")
            client.transition_model_version_stage(
                name=model_name,
                version=v.version,
                stage="Archived"
            )
            print(f"    ✓ Version {v.version} → Archived")
    
    print("\n" + "=" * 80)
    print("✅ SUCCESS!")
    print("Version 1 is now in Staging and ready to use")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nNote: You may need DagsHub authentication to promote models.")
    print("Ask your friend (repo owner) to run this script, or:")
    print("1. Go to: https://dagshub.com/MarcoSrhl/NLP-Fact-checking/experiments")
    print("2. Find model version 1")
    print("3. Click 'Stage' → 'Staging'")
    print("=" * 80)
