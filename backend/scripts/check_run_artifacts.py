#!/usr/bin/env python3
"""
Check what artifacts exist in the run associated with model version 3
"""

import mlflow
from mlflow.tracking import MlflowClient

# Set MLflow tracking URI to DagHub
DAGSHUB_REPO = "MarcoSrhl/NLP-Fact-checking"
mlflow.set_tracking_uri(f"https://dagshub.com/{DAGSHUB_REPO}.mlflow")

client = MlflowClient()

# Get model version 3 to find its run
print("=" * 80)
print("🔍 Checking Model Version 3 and its Run")
print("=" * 80)

try:
    version_3 = client.get_model_version("fact-checker-bert", 3)
    run_id = version_3.run_id
    
    print(f"\n📦 Model Version 3:")
    print(f"   Run ID: {run_id}")
    print(f"   Stage: {version_3.current_stage}")
    print(f"   Source: {version_3.source}")
    
    print(f"\n📁 Checking ALL artifacts in run {run_id[:8]}...")
    artifacts = client.list_artifacts(run_id)
    
    if not artifacts:
        print("   ❌ No artifacts found at root level")
    else:
        print(f"   Found {len(artifacts)} artifact(s) at root:\n")
        
        def show_artifacts(artifact_list, indent="   "):
            for art in artifact_list:
                if art.is_dir:
                    print(f"{indent}📂 {art.path}/")
                    # List contents of directory
                    try:
                        sub_artifacts = client.list_artifacts(run_id, art.path)
                        show_artifacts(sub_artifacts, indent + "   ")
                    except:
                        pass
                else:
                    size_mb = art.file_size / (1024*1024) if art.file_size else 0
                    size_str = f" ({size_mb:.2f} MB)" if art.file_size else ""
                    print(f"{indent}📄 {art.path}{size_str}")
        
        show_artifacts(artifacts)
    
    # Check if there's a specific model artifact path
    print(f"\n🔍 Checking common model paths...")
    common_paths = ["model", "models", "artifacts", "checkpoint", "best_model"]
    
    for path in common_paths:
        try:
            path_artifacts = client.list_artifacts(run_id, path)
            if path_artifacts:
                print(f"\n   ✓ Found artifacts in '{path}/':")
                for art in path_artifacts[:5]:
                    print(f"      - {art.path}")
                if len(path_artifacts) > 5:
                    print(f"      ... and {len(path_artifacts) - 5} more")
        except:
            pass
    
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print("=" * 80)
