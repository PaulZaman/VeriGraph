#!/usr/bin/env python3
"""
Simple check for model artifacts in run 83c07187
"""

import mlflow
from mlflow.tracking import MlflowClient

DAGSHUB_REPO = "MarcoSrhl/NLP-Fact-checking"
mlflow.set_tracking_uri(f"https://dagshub.com/{DAGSHUB_REPO}.mlflow")

client = MlflowClient()
run_id = "83c07187e08644c590e3cd92358ac4a4"

print(f"Checking artifacts for run {run_id[:8]}...\n")

# Check root level
artifacts = client.list_artifacts(run_id)
print(f"Root level artifacts ({len(artifacts)}):")
for art in artifacts:
    print(f"  {'📂' if art.is_dir else '📄'} {art.path}")

# If there are directories, check inside them
if artifacts:
    print("\nChecking inside directories...")
    for art in artifacts:
        if art.is_dir:
            print(f"\n  Inside {art.path}/:")
            try:
                sub_arts = client.list_artifacts(run_id, art.path)
                for sub in sub_arts[:10]:  # Limit to first 10
                    size = f" ({sub.file_size} bytes)" if sub.file_size else ""
                    print(f"    {'📂' if sub.is_dir else '📄'} {sub.path}{size}")
                if len(sub_arts) > 10:
                    print(f"    ... and {len(sub_arts) - 10} more")
            except Exception as e:
                print(f"    Error: {e}")
