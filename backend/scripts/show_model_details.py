#!/usr/bin/env python3
"""
Show detailed information about the registered model and its artifacts
"""

import mlflow
from mlflow.tracking import MlflowClient

# Set MLflow tracking URI to DagHub
DAGSHUB_REPO = "MarcoSrhl/NLP-Fact-checking"
mlflow.set_tracking_uri(f"https://dagshub.com/{DAGSHUB_REPO}.mlflow")

client = MlflowClient()

print("=" * 80)
print("🎯 DETAILED MODEL INFORMATION")
print("=" * 80)

# Get the registered model
model_name = "fact-checker-bert"
model_versions = client.search_model_versions(f"name='{model_name}'")

for mv in model_versions:
    print(f"\n📦 Model: {mv.name} v{mv.version}")
    print(f"   Stage: {mv.current_stage}")
    print(f"   Run ID: {mv.run_id}")
    print(f"   Source: {mv.source}")
    
    # Get run details
    run = client.get_run(mv.run_id)
    print(f"\n   📊 Run Details:")
    print(f"      Status: {run.info.status}")
    print(f"      Start Time: {run.info.start_time}")
    
    # Show metrics
    if run.data.metrics:
        print(f"\n   📈 Metrics:")
        for key, value in sorted(run.data.metrics.items()):
            print(f"      {key}: {value:.4f}")
    
    # Show parameters
    if run.data.params:
        print(f"\n   ⚙️  Parameters:")
        for key, value in sorted(run.data.params.items())[:10]:
            print(f"      {key}: {value}")
    
    # Show artifacts
    print(f"\n   📁 Artifacts:")
    artifacts = client.list_artifacts(mv.run_id)
    for artifact in artifacts:
        if artifact.is_dir:
            print(f"      📂 {artifact.path}/")
            # List files in directory
            sub_artifacts = client.list_artifacts(mv.run_id, artifact.path)
            for sub_art in sub_artifacts[:5]:
                size_str = f" ({sub_art.file_size} bytes)" if sub_art.file_size else ""
                print(f"         📄 {sub_art.path}{size_str}")
            if len(sub_artifacts) > 5:
                print(f"         ... and {len(sub_artifacts) - 5} more files")
        else:
            size_str = f" ({artifact.file_size} bytes)" if artifact.file_size else ""
            print(f"      📄 {artifact.path}{size_str}")
    
    print("\n" + "-" * 80)

# Also show the most recent successful runs
print("\n" + "=" * 80)
print("🔬 RECENT SUCCESSFUL RUNS")
print("=" * 80)

runs = client.search_runs(
    experiment_ids=["0"],
    filter_string="status = 'FINISHED'",
    order_by=["start_time DESC"],
    max_results=3
)

for run in runs:
    print(f"\n✓ Run ID: {run.info.run_id}")
    print(f"  Name: {run.data.tags.get('mlflow.runName', 'Unnamed')}")
    print(f"  Artifacts:")
    
    artifacts = client.list_artifacts(run.info.run_id)
    for artifact in artifacts[:10]:
        if artifact.is_dir:
            print(f"    📂 {artifact.path}/")
        else:
            print(f"    📄 {artifact.path}")

print("\n" + "=" * 80)
