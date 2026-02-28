#!/usr/bin/env python3
"""
Query MLflow server to list available models and runs
"""

import mlflow
from mlflow.tracking import MlflowClient

# Set MLflow tracking URI to DagHub
DAGSHUB_REPO = "MarcoSrhl/NLP-Fact-checking"
mlflow.set_tracking_uri(f"https://dagshub.com/{DAGSHUB_REPO}.mlflow")

client = MlflowClient()

print("=" * 80)
print("📦 REGISTERED MODELS")
print("=" * 80)
try:
    models = client.search_registered_models()
    if models:
        for model in models:
            print(f"\n✓ Model Name: {model.name}")
            print(f"  Description: {model.description or 'No description'}")
            print(f"  Latest Versions:")
            for version in model.latest_versions:
                print(f"    - Version {version.version}: Stage={version.current_stage}, Run ID={version.run_id[:8]}...")
    else:
        print("\nNo registered models found.")
except Exception as e:
    print(f"\n⚠️  Error accessing registered models: {e}")
    print("   (This is normal if no models are registered yet)")

print("\n" + "=" * 80)
print("🔬 EXPERIMENT RUNS")
print("=" * 80)

try:
    experiments = client.search_experiments()
    print(f"\nFound {len(experiments)} experiments:\n")
    
    for exp in experiments[:5]:  # Show first 5 experiments
        print(f"📊 Experiment: {exp.name} (ID: {exp.experiment_id})")
        
        # Get runs for this experiment
        runs = client.search_runs(
            experiment_ids=[exp.experiment_id],
            order_by=["start_time DESC"],
            max_results=5
        )
        
        if runs:
            print(f"   Recent runs ({len(runs)}):")
            for run in runs:
                print(f"   ✓ Run ID: {run.info.run_id[:8]}...")
                print(f"     Status: {run.info.status}")
                print(f"     Tags: {run.data.tags.get('mlflow.runName', 'Unnamed')}")
                
                # Show some metrics
                if run.data.metrics:
                    metrics_str = ", ".join([f"{k}={v:.4f}" for k, v in list(run.data.metrics.items())[:3]])
                    print(f"     Metrics: {metrics_str}")
                
                # Check for artifacts
                artifacts = client.list_artifacts(run.info.run_id)
                if artifacts:
                    artifact_names = [a.path for a in artifacts[:3]]
                    print(f"     Artifacts: {', '.join(artifact_names)}...")
                print()
        else:
            print("   No runs found.\n")
            
except Exception as e:
    print(f"Error: {e}")

print("=" * 80)
