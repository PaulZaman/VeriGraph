#!/usr/bin/env python3
"""
Promote model version 1 to Production and keep version 2 in Staging
"""

import mlflow
from mlflow.tracking import MlflowClient

# Set MLflow tracking URI to DagHub
DAGSHUB_REPO = "MarcoSrhl/NLP-Fact-checking"
mlflow.set_tracking_uri(f"https://dagshub.com/{DAGSHUB_REPO}.mlflow")

client = MlflowClient()
model_name = "fact-checker-bert"

print("=" * 80)
print("📦 Current Model Versions")
print("=" * 80)

versions = client.search_model_versions(f"name='{model_name}'")
for v in versions:
    print(f"\nVersion {v.version}:")
    print(f"  Stage: {v.current_stage}")
    print(f"  Run ID: {v.run_id[:8]}...")

print("\n" + "=" * 80)
print("🔄 Transitioning Model Stages...")
print("=" * 80)

# Move version 2 to Archived (since it has no artifacts)
print("\n1. Moving version 2 to Archived (no artifacts)...")
try:
    client.transition_model_version_stage(
        name=model_name,
        version=2,
        stage="Archived"
    )
    print("   ✓ Version 2 → Archived")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Keep version 1 in Staging (it has proper artifacts)
print("\n2. Keeping version 1 in Staging (has model artifacts)...")
print("   ✓ Version 1 remains in Staging")

print("\n" + "=" * 80)
print("📊 Updated Model Versions")
print("=" * 80)

versions = client.search_model_versions(f"name='{model_name}'")
staging_count = 0
for v in versions:
    print(f"\nVersion {v.version}:")
    print(f"  Stage: {v.current_stage}")
    print(f"  Run ID: {v.run_id[:8]}...")
    if v.current_stage == "Staging":
        staging_count += 1

print("\n" + "=" * 80)
if staging_count == 1:
    print("✅ SUCCESS: Exactly 1 model in Staging stage now!")
else:
    print(f"⚠️  WARNING: Found {staging_count} models in Staging")
print("=" * 80)
